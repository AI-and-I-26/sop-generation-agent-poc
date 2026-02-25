"""
Planning Agent - Module 4, Section 4.2

ARCHITECTURE CHANGE (this version):
  Removed the inner _make_llm_agent() pattern. Instead, run_planning calls
  BedrockModel directly via boto3 (converse API). This eliminates the
  double-agent hop that was silently swallowing errors and makes every step
  visible in logs.

DEBUG LOGGING:
  Set LOG_LEVEL=DEBUG in your environment or add this to your entry point:
      import logging
      logging.basicConfig(level=logging.DEBUG)
  You will then see exactly what is sent to Bedrock and what comes back.
"""

import os
import json
import logging
import boto3

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, SOPOutline, WorkflowStatus
from src.agents.state_store import STATE_STORE

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")


def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _call_bedrock(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """
    Call Bedrock converse API directly.
    Returns the raw text response string.
    Raises on any error so callers see the real exception.
    """
    logger.debug("=== BEDROCK CALL ===")
    logger.debug("Model: %s", model_id)
    logger.debug("Region: %s", _REGION)
    logger.debug("System prompt length: %d chars", len(system_prompt))
    logger.debug("User prompt:\n%s", user_prompt)

    client = boto3.client("bedrock-runtime", region_name=_REGION)

    request_body = {
        "modelId": model_id,
        "system": [{"text": system_prompt}],
        "messages": [{"role": "user", "content": [{"text": user_prompt}]}],
        "inferenceConfig": {"maxTokens": 2048},
    }

    logger.debug("Sending converse request...")
    response = client.converse(**request_body)

    logger.debug("Raw Bedrock response: %s", json.dumps(response, default=str))

    # Extract text from response
    output = response.get("output", {})
    message = output.get("message", {})
    content = message.get("content", [])

    if not content:
        raise ValueError(f"Bedrock returned empty content. Full response: {response}")

    text = content[0].get("text", "")
    logger.debug("Extracted text (%d chars):\n%s", len(text), text)

    if not text.strip():
        raise ValueError(f"Bedrock returned blank text. Full response: {response}")

    return text


def _parse_json_response(text: str) -> dict:
    """Strip code fences and parse JSON. Raises json.JSONDecodeError on failure."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    logger.debug("Parsing JSON:\n%s", text)
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

        system_prompt = (
            "You are an expert SOP planning agent. "
            "Return ONLY valid JSON — no prose, no markdown fences.\n\n"
            "JSON structure:\n"
            '{\n'
            '  "title": "Complete SOP Title",\n'
            '  "industry": "Industry Name",\n'
            '  "sections": [\n'
            '    {"number": "1", "title": "Purpose and Scope", "subsections": ["1.1 Purpose"]}\n'
            '  ],\n'
            '  "estimated_pages": 8\n'
            '}\n\n'
            "Include all 11 mandatory sections: "
            "Purpose and Scope, Definitions and Abbreviations, Responsibilities and Authorities, "
            "Required Materials and Equipment, Safety Requirements and PPE, "
            "Detailed Step-by-Step Procedures, Quality Control and Verification, "
            "Emergency Procedures, Troubleshooting Guide, "
            "References and Related Documents, Revision History."
        )

        user_prompt = (
            f"Create a detailed SOP outline for:\n"
            f"Topic: {state.topic}\n"
            f"Industry: {state.industry}\n"
            f"Target Audience: {state.target_audience}\n"
            f"Additional Requirements: {', '.join(state.requirements or [])}"
        )

        raw_text = _call_bedrock(model_id, system_prompt, user_prompt)
        outline_data = _parse_json_response(raw_text)
        outline = SOPOutline(**outline_data)

        state.outline = outline
        state.status = WorkflowStatus.PLANNED
        state.current_node = "planning"
        state.increment_tokens(1500)

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
    model=BedrockModel(model_id=_get_model_id("MODEL_PLANNING"), region=_REGION),
    system_prompt=(
        "You are the planning node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_planning tool "
        "with the full message as the prompt argument. "
        "Do not add commentary — just call the tool and return its result."
    ),
    tools=[run_planning],
)
