"""
Content Agent - Module 5, Section 5.1

ARCHITECTURE CHANGE: direct boto3 converse call instead of inner Agent.
See planning_agent.py for full explanation and debug instructions.
"""

import os
import json
import logging
import boto3

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, WorkflowStatus
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
    logger.debug("=== BEDROCK CALL [content] ===")
    logger.debug("Model: %s | Region: %s", model_id, _REGION)
    logger.debug("User prompt:\n%s", user_prompt)

    client = boto3.client("bedrock-runtime", region_name=_REGION)
    response = client.converse(
        modelId=model_id,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": 2048},
    )

    logger.debug("Raw response: %s", json.dumps(response, default=str))

    content = response.get("output", {}).get("message", {}).get("content", [])
    if not content:
        raise ValueError(f"Bedrock returned empty content. Response: {response}")

    text = content[0].get("text", "").strip()
    if not text:
        raise ValueError(f"Bedrock returned blank text. Response: {response}")

    logger.debug("Response text (%d chars):\n%s", len(text), text)
    return text


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


@tool
async def run_content(prompt: str) -> str:
    """Execute the SOP content generation step.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_content called | prompt: %s", prompt[:120])

    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()
    logger.debug("Extracted workflow_id: '%s'", workflow_id)

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = f"ERROR: no state found for workflow_id='{workflow_id}' | store keys: {list(STATE_STORE.keys())}"
        logger.error(msg)
        return msg

    if not state.outline:
        msg = f"ERROR: no outline in state for workflow_id='{workflow_id}'"
        logger.error(msg)
        state.add_error(msg)
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Content FAILED: {msg}"

    logger.info("State found | topic='%s' | sections: %d | research: %s",
                state.topic,
                len(state.outline.sections),
                "yes" if state.research else "NO - missing!")

    try:
        model_id = _get_model_id("MODEL_CONTENT")
        research_data = state.research.dict() if state.research else {}
        best_practices = research_data.get("best_practices", [])
        compliance = research_data.get("compliance_requirements", [])

        system_prompt = (
            "You are a technical writer specializing in Standard Operating Procedures. "
            "Return ONLY valid JSON — no prose, no markdown fences.\n\n"
            "JSON structure:\n"
            '{\n'
            '  "section_title": "Section Name",\n'
            '  "content": "## Section Name\\n\\n1. **Step**\\n   - Detail\\n   - ⚠️ WARNING: ...\\n   - ✓ CHECKPOINT: ...",\n'
            '  "safety_warnings": ["warning text"],\n'
            '  "quality_checkpoints": ["checkpoint text"],\n'
            '  "time_estimate_minutes": 5\n'
            '}\n\n'
            "Use active voice. Number all steps. Include time estimates."
        )

        content_sections = {}
        sections_to_generate = state.outline.sections[:5]
        logger.info("Generating content for %d sections", len(sections_to_generate))

        for i, section in enumerate(sections_to_generate):
            logger.info("  Generating section %d/%d: '%s'",
                        i + 1, len(sections_to_generate), section.title)

            user_prompt = (
                f"Write detailed SOP content for this section:\n\n"
                f"Section: {section.title}\n"
                f"Topic context: {state.topic} ({state.industry})\n"
                f"Target Audience: {state.target_audience}\n"
                f"Best Practices: {', '.join(best_practices) if best_practices else 'None'}\n"
                f"Compliance: {', '.join(compliance) if compliance else 'None'}\n\n"
                f"Write clear numbered steps with safety warnings, checkpoints, "
                f"and time estimates. Return complete JSON."
            )

            raw_text = _call_bedrock(model_id, system_prompt, user_prompt)
            content_data = _parse_json_response(raw_text)
            content_sections[section.title] = content_data["content"]
            state.increment_tokens(2500)

            logger.info("  Section '%s' complete (%d chars)",
                        section.title, len(content_data["content"]))

        state.content_sections = content_sections
        state.status = WorkflowStatus.WRITTEN
        state.current_node = "content"

        logger.info("Content generation complete — %d sections | workflow_id=%s",
                    len(content_sections), workflow_id)

        return (
            f"workflow_id::{workflow_id} | "
            f"Content complete: {len(content_sections)} sections written for '{state.topic}'"
        )

    except Exception as e:
        logger.exception("Content FAILED for workflow_id=%s", workflow_id)
        state.add_error(f"Content generation failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Content FAILED: {e}"


content_agent = Agent(
    name="ContentNode",
    model=BedrockModel(model_id=_get_model_id("MODEL_CONTENT"), region=_REGION),
    system_prompt=(
        "You are the content generation node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_content tool "
        "with the full message as the prompt argument. "
        "Do not add commentary — just call the tool and return its result."
    ),
    tools=[run_content],
)
