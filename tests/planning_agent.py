"""
planning_agent.py — PlanningAgent for the SOP generation pipeline.

ROLE IN THE PIPELINE:
    Node 1 of 5 in the Strands graph.
    Receives the "workflow_id::..." graph message and produces a structured
    SOP outline (SOPOutline) with exactly 8 KB-locked sections.

HOW IT WORKS:
    1. The outer 'planning_agent' (Agent instance) is registered as a
       Strands graph node.  When the graph activates this node, the Agent
       calls the run_planning @tool function via its tool-use capability.
    2. run_planning extracts the workflow_id from the graph message,
       fetches the SOPState from STATE_STORE, and calls the Bedrock
       Converse API with Structured Outputs (JSON Schema) to guarantee
       a valid JSON outline.
    3. The outline is parsed into SOPOutline, stored back in STATE_STORE,
       and a summary string is returned to the graph for the next node.

WHY STRUCTURED OUTPUTS?
    Using Bedrock's outputConfig.textFormat.type = "json_schema" forces
    the model to return JSON that validates against _SOP_SCHEMA.  This
    eliminates the need for brittle regex/strip post-processing and
    prevents truncated JSON from silently passing downstream.

RETRY LOGIC:
    If stopReason == "max_tokens", the Converse call is retried up to
    3 times with doubled maxTokens each attempt.

ANTHROPIC CLAUDE MODEL:
    Uses the claude-sonnet-4-6 inference profile via the AWS Bedrock
    Converse API.  Model ID is read from the MODEL_PLANNING env var,
    defaulting to the us-east-2 inference profile ARN.
"""

import os
import json
import logging
from typing import Dict, Any, List

import boto3

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, SOPOutline, WorkflowStatus
from src.graph.state_store import STATE_STORE
from src.prompts.system_prompts import PLANNING_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# Default Bedrock inference profile ARN for Claude Sonnet 4.6 in us-east-2.
# Override with MODEL_PLANNING env var to switch models or regions.
_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")


def _get_model_id(env_var: str) -> str:
    """Read model ID from env var, falling back to the default Claude ARN."""
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


# ---------------------------------------------------------------------------
# JSON Schema for Structured Outputs
# ---------------------------------------------------------------------------
# This schema is passed to Bedrock's outputConfig.textFormat.  The Bedrock
# service validates the model's response against it before returning, so we
# are guaranteed to receive valid JSON (or a stopReason error).
#
# NOTE: The schema allows 1–20 sections (minItems=1, maxItems=20).
# The actual section count and titles come from the KB — the planning agent
# reads kb_format_context from its prompt and uses the KB's own structure.
_SOP_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "title":     {"type": "string", "minLength": 3},
        "industry":  {"type": "string", "minLength": 2},
        "sections": {
            "type": "array",
            # Allow 1–20 sections — the actual count is determined by the KB
            "minItems": 1,
            "maxItems": 20,
            "items": {
                "type": "object",
                "properties": {
                    # Section numbers follow the KB's numbering style
                    "number":  {"type": "string", "pattern": r"^\d+(\.\d+)?$"},
                    "title":   {"type": "string", "minLength": 2},
                    # subsections is an array of objects at this schema level
                    "subsections": {
                        "type": "array",
                        "items": {"type": "object"},
                        "default": []
                    }
                },
                "required": ["number", "title", "subsections"],
                "additionalProperties": False
            }
        },
        "estimated_pages": {"type": "integer", "minimum": 1, "maximum": 200}
    },
    "required": ["title", "industry", "sections", "estimated_pages"],
    "additionalProperties": False
}


# ---------------------------------------------------------------------------
# Low-level Bedrock helpers
# ---------------------------------------------------------------------------

def _extract_text_blocks(response: Dict[str, Any]) -> str:
    """
    Pull the concatenated text from a Converse API response.

    The Converse API returns output.message.content as a list of blocks.
    Each block may be {"text": "..."} or {"toolUse": ...}.  We only want
    the text blocks.

    Args:
        response: Raw dict returned by bedrock_client.converse().

    Returns:
        All text blocks joined into one string, stripped of whitespace.
    """
    output  = response.get("output", {})
    message = output.get("message", {})
    content: List[Dict[str, Any]] = message.get("content", [])
    texts = [
        block["text"]
        for block in content
        if "text" in block and isinstance(block["text"], str)
    ]
    return "".join(texts).strip()


def _converse_json(
    client,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    schema: Dict[str, Any],
    initial_max_tokens: int = 4096,
    max_attempts: int = 3,
) -> Dict[str, Any]:
    """
    Call Bedrock Converse with Structured Outputs and return parsed JSON.

    Bedrock's outputConfig.textFormat.type = "json_schema" forces the model
    to emit JSON that conforms to the supplied schema.  If the model runs out
    of tokens before finishing (stopReason == "max_tokens"), we double the
    budget and retry (up to max_attempts times).

    Args:
        client:             boto3 bedrock-runtime client.
        model_id:           Bedrock inference profile ARN or model ID.
        system_prompt:      The LLM's behavioural instructions.
        user_prompt:        The specific planning request.
        schema:             JSON Schema dict for the expected output.
        initial_max_tokens: Starting token budget (default 4096).
        max_attempts:       How many times to retry on max_tokens (default 3).

    Returns:
        Parsed dict matching the schema.

    Raises:
        RuntimeError: If all attempts exhaust the token budget.
        ValueError:   If the model returns empty content.
    """
    max_tokens = initial_max_tokens
    last_reason = None
    last_text = None

    for attempt in range(1, max_attempts + 1):
        logger.debug("Converse attempt %d | maxTokens=%d", attempt, max_tokens)

        response = client.converse(
            modelId=model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={
                "maxTokens":   max_tokens,
                "temperature": 0.0,   # deterministic output for structured data
            },
            # Structured Outputs: Bedrock validates response against the schema.
            # 'schema' must be passed as a JSON string (not a dict) in this field.
            outputConfig={
                "textFormat": {
                    "type": "json_schema",
                    "structure": {
                        "jsonSchema": {
                            "schema": json.dumps(schema),
                            "name":   "sop_planning",
                            "description": "Validated JSON plan for SOP outline"
                        }
                    }
                }
            },
        )

        stop_reason = response.get("stopReason")
        last_reason = stop_reason

        text = _extract_text_blocks(response)
        last_text = text

        if not text:
            raise ValueError(
                f"Empty content from Bedrock. stopReason={stop_reason}"
            )

        if stop_reason == "end_turn":
            # Happy path: model finished cleanly within the token budget.
            logger.debug("stopReason=end_turn; parsing JSON.")
            return json.loads(text)

        if stop_reason == "max_tokens":
            # The response was truncated.  Double the budget and retry.
            logger.warning(
                "Model hit max_tokens; doubling budget to %d (attempt %d).",
                max_tokens * 2, attempt
            )
            max_tokens = min(max_tokens * 2, 8192)
            continue

        # Any other stop reason (e.g. stop_sequence, content_filtered):
        # try to parse what we got rather than raising immediately.
        logger.warning("Unhandled stopReason=%s; attempting parse.", stop_reason)
        return json.loads(text)

    raise RuntimeError(
        f"Converse did not complete within token budget after {max_attempts} attempts. "
        f"Last stopReason={last_reason}. Last text length={len(last_text or '')}."
    )


def _call_bedrock(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """
    Synchronous wrapper: calls _converse_json and returns the result as a
    JSON string.  This keeps run_planning (async) clean by moving the
    blocking boto3 call here, where it can be run in a thread if needed.

    Args:
        model_id:      Bedrock model/profile ARN.
        system_prompt: Planning agent system prompt.
        user_prompt:   The specific SOP planning request.

    Returns:
        JSON string representation of the validated outline dict.
    """
    logger.debug("Calling Bedrock | model=%s | region=%s", model_id, _REGION)
    client = boto3.client("bedrock-runtime", region_name=_REGION)
    data = _converse_json(
        client=client,
        model_id=model_id,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=_SOP_SCHEMA,
        initial_max_tokens=4096,
        max_attempts=3,
    )
    json_text = json.dumps(data, ensure_ascii=False)
    logger.debug("Validated JSON received (%d chars).", len(json_text))
    return json_text


def _parse_json_response(text: str) -> dict:
    """
    Parse JSON from text.  With Structured Outputs the text is already pure
    JSON.  This function is kept for safety — it also strips code fences in
    case an older model still wraps the output.

    Args:
        text: Raw string from the Bedrock response.

    Returns:
        Parsed dict.
    """
    text = text.strip()
    # Strip legacy markdown code fences if present.
    if text.startswith("```"):
        chunks = text.split("```")
        if len(chunks) >= 2:
            text = chunks[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
    return json.loads(text)


# ---------------------------------------------------------------------------
# @tool function — called by the planning_agent node
# ---------------------------------------------------------------------------

@tool
async def run_planning(prompt: str) -> str:
    """
    Execute the SOP planning step.

    This function is the @tool that the outer planning_agent (Agent instance)
    calls when the Strands graph activates the "planning" node.

    FLOW:
        1. Extract workflow_id from the graph message string.
        2. Fetch SOPState from STATE_STORE.
        3. Call Bedrock Converse (Structured Outputs) with PLANNING_SYSTEM_PROMPT.
        4. Parse the response into SOPOutline and store it on the state.
        5. Return a summary string for the next graph node.

    Args:
        prompt: The graph message string containing 'workflow_id::<id>'.

    Returns:
        A string starting with 'workflow_id::<id> | ...' for the next node.
    """
    logger.info(">>> run_planning called | prompt: %.120s", prompt)

    # Step 1: Extract workflow_id from the embedded token in the graph message.
    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()
    logger.debug("Extracted workflow_id: '%s'", workflow_id)

    # Step 2: Fetch state from the shared store.
    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = (
            f"ERROR: no state found for workflow_id='{workflow_id}' "
            f"| store keys: {list(STATE_STORE.keys())}"
        )
        logger.error(msg)
        return msg

    logger.info("State found | topic='%s' industry='%s'", state.topic, state.industry)

    try:
        model_id = _get_model_id("MODEL_PLANNING")
        logger.info("Using model: %s", model_id)

        # Build the user prompt — includes kb_format_context if available from a
        # previous run or pre-seeded state.  On a fresh run it will be None and
        # the planning agent falls back to standard SOP structure.
        kb_ctx_str = (
            json.dumps(state.kb_format_context, indent=2)
            if state.kb_format_context
            else "(not available yet — use standard SOP structure)"
        )

        user_prompt = (
            f"Create a detailed SOP outline:\n"
            f"Topic: {state.topic}\n"
            f"Industry: {state.industry}\n"
            f"Target Audience: {state.target_audience}\n"
            f"Additional Requirements: {', '.join(state.requirements or [])}\n\n"
            f"KB FORMAT CONTEXT (use these section titles and structure if available):\n"
            f"{kb_ctx_str}\n\n"
            "If KB FORMAT CONTEXT is available, use its section_titles and section_count "
            "to determine the sections. Otherwise use a standard 8-section SOP structure:\n"
            "  1.0 PURPOSE | 2.0 SCOPE | 3.0 RESPONSIBILITIES | 4.0 DEFINITIONS\n"
            "  5.0 MATERIALS | 6.0 PROCEDURE | 7.0 REFERENCES | 8.0 REVISION HISTORY\n\n"
            "Generate topic-appropriate subsection titles for the Procedure section "
            "(and any other sections that have subsections in KB FORMAT CONTEXT).\n"
            "Return valid JSON. No extra keys. Exactly match the JSON Schema."
        )

        # Step 3: Call Bedrock with the planning system prompt and user prompt.
        raw_text    = _call_bedrock(model_id, PLANNING_SYSTEM_PROMPT, user_prompt)
        outline_data = _parse_json_response(raw_text)
        outline      = SOPOutline(**outline_data)

        # Step 4: Store the outline and update workflow state.
        state.outline            = outline
        state.status             = WorkflowStatus.PLANNED
        state.current_node       = "planning"
        state.planning_complete  = True
        state.increment_tokens(1500)

        logger.info(
            "Planning complete — %d sections | workflow_id=%s",
            len(outline.sections), workflow_id
        )

        # Step 5: Return the workflow_id token so the next node can find state.
        return (
            f"workflow_id::{workflow_id} | "
            f"Planning complete: {len(outline.sections)} sections for '{state.topic}'"
        )

    except Exception as e:
        logger.exception("Planning FAILED for workflow_id=%s", workflow_id)
        state.add_error(f"Planning failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Planning FAILED: {e}"


# ---------------------------------------------------------------------------
# Graph node Agent
# ---------------------------------------------------------------------------
# The Agent registered with GraphBuilder.add_node().
# It has a system prompt instructing it to call run_planning immediately,
# and the run_planning @tool in its tools list.
#
# IMPORTANT: The node Agent must have a `model` parameter so it can invoke
# its tools.  Without it, the graph silently skips tool calls.

planning_agent = Agent(
    name="PlanningNode",
    # BedrockModel wraps the boto3 Bedrock client used by Strands Agent internally.
    model=BedrockModel(model_id=_get_model_id("MODEL_PLANNING")),
    system_prompt=(
        "You are the planning node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_planning tool "
        "with the full message as the prompt argument. "
        "Do not add commentary — just call the tool and return its result."
    ),
    tools=[run_planning],
)
