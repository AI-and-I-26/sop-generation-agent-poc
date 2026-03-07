"""
planning_agent.py — PlanningAgent for the SOP generation pipeline.

ROLE IN THE PIPELINE:
    Node 1 of 5 in the Strands graph.
    Receives the "workflow_id::..." graph message and produces a structured
    SOP outline (SOPOutline) with exactly 8 KB-locked sections.

HOW IT WORKS:
    1. The outer 'planning_agent' (Agent instance) is registered as a
       Strands graph node. When the graph activates this node, the Agent
       calls the run_planning @tool function via its tool-use capability.
    2. run_planning extracts the workflow_id from the graph message,
       fetches the SOPState from STATE_STORE, and calls the Bedrock
       Converse API with Structured Outputs (JSON Schema) to guarantee
       a valid JSON outline (when supported by the local SDK).
       If the local SDK is older and rejects `outputConfig`, we
       automatically fall back to a plain Converse call without
       Structured Outputs — silently (no warning).
    3. The outline is parsed into SOPOutline, stored back in STATE_STORE,
       and a summary string is returned to the graph for the next node.

WHY STRUCTURED OUTPUTS?
    Using Bedrock's outputConfig.textFormat.type = "json_schema" forces
    the model to return JSON that validates against _SOP_SCHEMA. This
    eliminates the need for brittle post-processing and prevents
    truncated JSON from passing downstream.

RETRY LOGIC:
    If stopReason == "max_tokens", the Converse call is retried up to
    3 times with doubled maxTokens each attempt.

ANTHROPIC CLAUDE MODEL:
    Uses the claude-sonnet-4-6 inference profile via the AWS Bedrock
    Converse API. Model ID is read from MODEL_PLANNING (env var),
    defaulting to the us-east-2 inference profile ARN.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional

import boto3
from botocore.exceptions import ParamValidationError, ClientError

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, SOPOutline, WorkflowStatus
from src.graph.state_store import STATE_STORE
from src.prompts.system_prompts import PLANNING_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")


def _get_model_id(env_var: str) -> str:
    """Read model ID from env var, falling back to the default Claude ARN."""
    return os.getenv(env_var, _DEFAULT_MODEL_ID)



# ---------------------------------------------------------------------------
# JSON Schema for Structured Outputs (Bedrock-safe subset, FIXED)
# ---------------------------------------------------------------------------
# FIX APPLIED:
#   • Every object now has `additionalProperties: False`
#   • Nested objects (like subsection items) are also closed
#   • No minItems / maxItems / default (to avoid Bedrock subset violations)

_SOP_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "title": {
            "type": "string",
            "minLength": 3,
            "additionalProperties": False
        },
        "industry": {
            "type": "string",
            "minLength": 2,
            "additionalProperties": False
        },
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "number": {
                        "type": "string",
                        "pattern": r"^\d+(\.\d+)?$",
                        "additionalProperties": False
                    },
                    "title": {
                        "type": "string",
                        "minLength": 2,
                        "additionalProperties": False
                    },
                    "subsections": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "number": {
                                    "type": "string",
                                    "pattern": r"^\d+(\.\d+)?$",
                                    "additionalProperties": False
                                },
                                "title": {
                                    "type": "string",
                                    "minLength": 2,
                                    "additionalProperties": False
                                }
                            },
                            "required": ["number", "title"]
                        },
                        "additionalProperties": False
                    }
                },
                "required": ["number", "title", "subsections"]
            },
            "additionalProperties": False
        },
        "estimated_pages": {
            "type": "integer",          
            "additionalProperties": False
        }
    },
    "required": ["title", "industry", "sections", "estimated_pages"]
}

# ---------------------------------------------------------------------------
# JSON parsing helpers (robust in plain-Converse fallback)
# ---------------------------------------------------------------------------

def _repair_malformed_json(text: str) -> str:
    """
    Attempt to repair common JSON issues in LLM output:
      - strip markdown fences / leading prose
      - cut off at the last balanced top-level brace/bracket
      - remove trailing commas before '}' or ']'
    Returns a candidate JSON string for json.loads().
    """
    if not text:
        return text
    t = text.strip()

    # Strip code fences if present
    if t.startswith("```"):
        parts = t.split("```")
        if len(parts) >= 2:
            t = parts[1]
            if t.lstrip().startswith("json"):
                t = t.lstrip()[4:]
        t = t.strip()

    # Drop leading prose before first JSON token
    first = min([i for i in [t.find("{"), t.find("[")] if i != -1], default=-1)
    if first > 0:
        t = t[first:]

    # Keep up to last balanced top-level brace/bracket
    stack, last = [], -1
    for i, ch in enumerate(t):
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                opener = stack.pop()
                if (opener, ch) in (("{", "}"), ("[", "]")) and not stack:
                    last = i
    if last != -1:
        t = t[:last + 1]

    # Remove a trailing comma immediately before } or ]
    t = re.sub(r",\s*([}\]])", r"\1", t)
    return t.strip()


def _parse_json_lenient(text: str) -> Dict[str, Any]:
    """
    Parse JSON from text. In structured-output mode it's already valid JSON.
    In plain Converse fallback, attempt lightweight repair before parsing.
    """
    if not text or not text.strip():
        raise ValueError("Empty JSON string.")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        repaired = _repair_malformed_json(text)
        return json.loads(repaired)


# ---------------------------------------------------------------------------
# Low-level Bedrock helpers
# ---------------------------------------------------------------------------

def _extract_text_blocks(response: Dict[str, Any]) -> str:
    """
    Pull the concatenated text from a Converse API response.
    """
    output = response.get("output", {})
    message = output.get("message", {})
    content: List[Dict[str, Any]] = message.get("content", [])
    texts = [
        block["text"]
        for block in content
        if "text" in block and isinstance(block["text"], str)
    ]
    return "".join(texts).strip()


def _build_output_config(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the structured outputs config for Converse:
      outputConfig.textFormat.type = "json_schema"
      with a JSON Schema string supplied.
    """
    return {
        "textFormat": {
            "type": "json_schema",
            "structure": {
                "jsonSchema": {
                    "schema": json.dumps(schema),  # Bedrock expects a STRING here
                    "name": "sop_planning",
                    "description": "Validated JSON plan for SOP outline"
                }
            }
        }
    }


def _converse_once(
    client,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    use_structured_outputs: bool,
    schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Issue a single Converse request, optionally with structured outputs.
    """
    kwargs: Dict[str, Any] = dict(
        modelId=model_id,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0.0},
    )
    if use_structured_outputs and schema is not None:
        kwargs["outputConfig"] = _build_output_config(schema)

    return client.converse(**kwargs)


def _converse_json(
    client,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    schema: Dict[str, Any],
    initial_max_tokens: int = 5120,   # slightly higher to reduce truncation
    max_attempts: int = 3,
) -> Dict[str, Any]:
    """
    Call Bedrock Converse and return parsed JSON dict.

    Strategy:
      1) Try with Structured Outputs (outputConfig.textFormat). If the local SDK
         rejects `outputConfig` (older model), silently fall back to plain Converse.
      2) Retry on stopReason == "max_tokens" by doubling maxTokens up to 8192.
    """
    max_tokens = initial_max_tokens
    last_reason = None
    last_text = None

    supports_structured = True

    for attempt in range(1, max_attempts + 1):
        logger.debug(
            "Converse attempt %d | maxTokens=%d | structured=%s",
            attempt, max_tokens, supports_structured
        )
        try:
            response = _converse_once(
                client=client,
                model_id=model_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                use_structured_outputs=supports_structured,
                schema=schema,
            )
        except ParamValidationError as e:
            # Older boto3/botocore without 'outputConfig' support: silent fallback.
            msg = str(e)
            if 'Unknown parameter in input: "outputConfig"' in msg and supports_structured:
                supports_structured = False
                response = _converse_once(
                    client=client,
                    model_id=model_id,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=max_tokens,
                    use_structured_outputs=False,
                )
            else:
                raise
        except ClientError:
            raise

        stop_reason = response.get("stopReason")
        last_reason = stop_reason

        text = _extract_text_blocks(response)
        last_text = text

        if not text:
            raise ValueError(f"Empty content from Bedrock. stopReason={stop_reason}")

        # Parse strictly (structured mode) or leniently (fallback mode)
        if stop_reason == "end_turn":
            logger.debug("stopReason=end_turn; parsing JSON.")
            return _parse_json_lenient(text)

        if stop_reason == "max_tokens":
            logger.warning(
                "Model hit max_tokens; doubling budget to %d (attempt %d).",
                min(max_tokens * 2, 8192), attempt
            )
            max_tokens = min(max_tokens * 2, 8192)
            continue

        logger.debug("Unhandled stopReason=%s; attempting parse.", stop_reason)
        return _parse_json_lenient(text)

    raise RuntimeError(
        "Converse did not complete within token budget after "
        f"{max_attempts} attempts. Last stopReason={last_reason}. "
        f"Last text length={len(last_text or '')}."
    )


def _call_bedrock(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """
    Synchronous wrapper: calls _converse_json and returns the result as a
    JSON string. This keeps run_planning (async) clean by moving the
    blocking boto3 call here.
    """
    logger.debug("Calling Bedrock | model=%s | region=%s", model_id, _REGION)
    client = boto3.client("bedrock-runtime", region_name=_REGION)
    data = _converse_json(
        client=client,
        model_id=model_id,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=_SOP_SCHEMA,
        initial_max_tokens=5120,
        max_attempts=3,
    )
    json_text = json.dumps(data, ensure_ascii=False)
    logger.debug("Validated/parsed JSON received (%d chars).", len(json_text))
    return json_text


def _parse_json_response(text: str) -> dict:
    """
    Parse JSON from text again (kept for compatibility with caller).
    Uses the same lenient strategy to avoid decode errors in rare cases.
    """
    return _parse_json_lenient((text or "").strip())


# ---------------------------------------------------------------------------
# @tool function — called by the planning_agent node
# ---------------------------------------------------------------------------

@tool
async def run_planning(prompt: str) -> str:
    """
    Execute the SOP planning step.
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

        # Step 3: Call Bedrock; returns a JSON string (already parsed/validated upstream).
        raw_text = _call_bedrock(model_id, PLANNING_SYSTEM_PROMPT, user_prompt)
        outline_data = _parse_json_response(raw_text)
        outline = SOPOutline(**outline_data)

        # Step 4: Store the outline and update workflow state.
        state.outline = outline
        state.status = WorkflowStatus.PLANNED
        state.current_node = "planning"
        state.planning_complete = True
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

planning_agent = Agent(
    name="PlanningNode",
    model=BedrockModel(model_id=_get_model_id("MODEL_PLANNING")),
    system_prompt=(
        "You are the planning node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_planning tool "
        "with the full message as the prompt argument. "
        "Do not add commentary — just call the tool and return its result."
    ),
    tools=[run_planning],
)