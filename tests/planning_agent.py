"""
Planning Agent - Module 4, Section 4.2

ARCHITECTURE CHANGE (this version):
  - Keep the single-hop design: run_planning -> direct Bedrock (Converse API).
  - Add Structured outputs (JSON Schema) so the model MUST return valid JSON.
  - Add stopReason handling + token escalation to avoid truncated JSON.

DEBUG LOGGING:
  Set LOG_LEVEL=DEBUG in your environment or add this to your entry point:
      import logging
      logging.basicConfig(level=logging.DEBUG)
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

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")

# ---- JSON Schema used for Structured outputs (Converse outputConfig.textFormat) ----
# Enforces a stable, parsable output for the planning agent.
_SOP_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 3},
        "industry": {"type": "string", "minLength": 2},
        "sections": {
            "type": "array",
            "minItems": 11,
            "maxItems": 11,
            "items": {
                "type": "object",
                "properties": {
                    "number": {"type": "string", "pattern": r"^\d+(\.\d+)?$"},
                    "title": {"type": "string", "minLength": 2},
                    "subsections": {
                        "type": "array",
                        "items": {"type": "string"},
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


def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _extract_text_blocks(response: Dict[str, Any]) -> str:
    """
    Extract all text blocks from the Converse response's output.message.content.
    """
    output = response.get("output", {})
    message = output.get("message", {})
    content: List[Dict[str, Any]] = message.get("content", [])
    texts: List[str] = []
    for block in content:
        if "text" in block and isinstance(block["text"], str):
            texts.append(block["text"])
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
    Call Bedrock Converse with Structured outputs (JSON Schema) and return parsed JSON.
    Retries if stopReason == 'max_tokens' by increasing maxTokens.

    Uses:
      - outputConfig.textFormat.type = "json_schema"
      - outputConfig.textFormat.structure.jsonSchema.schema = <schema_as_string>

    References:
      - Bedrock Structured outputs for Converse API.  (docs)  [1]
      - Converse stopReason values & handling.          (docs)  [2]
    """
    max_tokens = initial_max_tokens
    last_reason = None
    last_text = None

    for attempt in range(1, max_attempts + 1):
        logger.debug("Converse attempt %d | maxTokens=%s", attempt, max_tokens)

        response = client.converse(
            modelId=model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": 0.0
            },
            outputConfig={
                "textFormat": {
                    "type": "json_schema",
                    "structure": {
                        "jsonSchema": {
                            # Bedrock expects the schema as a STRING in this field.
                            "schema": json.dumps(schema),
                            "name": "sop_planning",
                            "description": "Validated JSON plan for SOP outline"
                        }
                    }
                }
            },
        )

        logger.debug("Raw Bedrock response: %s", json.dumps(response, default=str))

        stop_reason = response.get("stopReason")
        last_reason = stop_reason

        text = _extract_text_blocks(response)
        last_text = text
        if not text:
            # Sometimes content could be empty if model ended turn with no text (rare with structured outputs)
            raise ValueError(f"Empty content from Bedrock. stopReason={stop_reason} | response={response}")

        # With Structured outputs, text is guaranteed valid JSON against schema,
        # provided the model had enough tokens to finish.  [1]
        if stop_reason == "end_turn":
            logger.debug("stopReason=end_turn; parsing JSON.")
            return json.loads(text)

        if stop_reason == "max_tokens":
            logger.warning("Model hit max_tokens; escalating maxTokens and retrying. [attempt=%d]", attempt)
            # Increase budget and retry
            max_tokens = min(max_tokens * 2, 8192)  # Adjust ceiling if needed for your model
            continue

        # Other reasons: stop_sequence, tool_use, etc. Handle conservatively.
        logger.warning("Unhandled stopReason=%s; attempting to parse anyway.", stop_reason)
        return json.loads(text)

    # If we exhausted attempts, surface a clear error.
    raise RuntimeError(
        f"Converse did not complete within token budget. Last stopReason={last_reason}. "
        f"Last text length={len(last_text or '')}."
    )


def _call_bedrock(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """
    Backward-compatible wrapper (kept for minimal change).
    Now uses Structured outputs and returns the JSON string.
    """
    logger.debug("=== BEDROCK CALL (structured JSON) ===")
    logger.debug("Model: %s | Region: %s", model_id, _REGION)
    logger.debug("System prompt length: %d chars", len(system_prompt))
    logger.debug("User prompt:\n%s", user_prompt)

    client = boto3.client("bedrock-runtime", region_name=_REGION)
    data = _converse_json(
        client=client,
        model_id=model_id,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=_SOP_SCHEMA,
        initial_max_tokens=4096,  # tuned for long JSON; adjust as needed
        max_attempts=3,
    )
    json_text = json.dumps(data, ensure_ascii=False)
    logger.debug("Validated JSON received (%d chars).", len(json_text))
    return json_text


def _parse_json_response(text: str) -> dict:
    """
    Parse JSON from text. With Structured outputs, text is already pure JSON.
    Left here for compatibility (e.g., if text included code fences in older runs).
    """
    text = text.strip()
    if text.startswith("```"):
        # Remove fences if any legacy prompts returned them.
        chunks = text.split("```")
        if len(chunks) >= 2:
            text = chunks[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
    logger.debug("Parsing JSON payload.")
    return json.loads(text)


# ---------------------------------------------------------------------------
# Graph-level tool
# ---------------------------------------------------------------------------

@tool
async def run_planning(prompt: str) -> str:
    """Execute the SOP planning step.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_planning called | prompt: %s", prompt[:120])

    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()
    logger.debug("Extracted workflow_id: '%s'", workflow_id)

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = f"ERROR: no state found for workflow_id='{workflow_id}' | store keys: {list(STATE_STORE.keys())}"
        logger.error(msg)
        return msg

    logger.info("State found | topic='%s' industry='%s'", state.topic, state.industry)

    try:
        model_id = _get_model_id("MODEL_PLANNING")
        logger.info("Using model: %s", model_id)

        # The schema enforces JSON; system prompt can stay concise.
        system_prompt = (
            "You are an expert SOP planning agent. "
            "Produce a complete SOP outline strictly matching the provided JSON Schema."
        )

        user_prompt = (
            f"Create a detailed SOP outline:\n"
            f"Topic: {state.topic}\n"
            f"Industry: {state.industry}\n"
            f"Target Audience: {state.target_audience}\n"
            f"Additional Requirements: {', '.join(state.requirements or [])}\n\n"
            "Mandatory 11 sections (exactly 11), in this order:\n"
            "1) Purpose and Scope\n"
            "2) Definitions and Abbreviations\n"
            "3) Responsibilities and Authorities\n"
            "4) Required Materials and Equipment\n"
            "5) Safety Requirements and PPE\n"
            "6) Detailed Step-by-Step Procedures\n"
            "7) Quality Control and Verification\n"
            "8) Emergency Procedures\n"
            "9) Troubleshooting Guide\n"
            "10) References and Related Documents\n"
            "11) Revision History\n"
            "Your output must match the JSON Schema; no extra keys."
        )

        raw_text = _call_bedrock(model_id, system_prompt, user_prompt)
        outline_data = _parse_json_response(raw_text)
        outline = SOPOutline(**outline_data)

        # Update state
        state.outline = outline
        state.status = WorkflowStatus.PLANNED
        state.current_node = "planning"
        state.increment_tokens(1500)  # keep your accounting

        logger.info("Planning complete — %d sections | workflow_id=%s",
                    len(outline.sections), workflow_id)

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
# Node Agent
# ---------------------------------------------------------------------------

planning_agent = Agent(
    name="PlanningNode",
    # model=BedrockModel(model_id=_get_model_id("MODEL_PLANNING"), region=_REGION),
    model=BedrockModel(model_id=_get_model_id("MODEL_PLANNING")),
    system_prompt=(
        "You are the planning node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_planning tool "
        "with the full message as the prompt argument. "
        "Do not add commentary — just call the tool and return its result."
    ),
    tools=[run_planning],
)