"""
Research Agent - Module 5, Section 5.1

ARCHITECTURE CHANGE: direct boto3 converse call instead of inner Agent.
See planning_agent.py for full explanation and debug instructions.
"""

import os
import json
import logging
import boto3

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, ResearchFindings, WorkflowStatus
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
    logger.debug("=== BEDROCK CALL [research] ===")
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


def _get_compliance(industry: str) -> list:
    """Inline compliance lookup (no external call needed)."""
    compliance_map = {
        "Manufacturing": ["OSHA 1910", "ISO 9001"],
        "Healthcare": ["HIPAA", "FDA 21 CFR"],
        "Laboratory": ["CLIA", "CAP Standards"],
    }
    return compliance_map.get(industry, ["General Safety Standards"])


@tool
async def run_research(prompt: str) -> str:
    """Execute the SOP research step.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_research called | prompt: %s", prompt[:120])

    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()
    logger.debug("Extracted workflow_id: '%s'", workflow_id)

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = f"ERROR: no state found for workflow_id='{workflow_id}' | store keys: {list(STATE_STORE.keys())}"
        logger.error(msg)
        return msg

    logger.info("State found | topic='%s' | outline sections: %d",
                state.topic, len(state.outline.sections) if state.outline else 0)

    try:
        model_id = _get_model_id("MODEL_RESEARCH")
        compliance = _get_compliance(state.industry)
        logger.info("Compliance requirements: %s", compliance)

        outline_summary = ""
        if state.outline:
            titles = [s.title for s in state.outline.sections[:5]]
            outline_summary = f"Outline sections: {', '.join(titles)}"

        system_prompt = (
            "You are a research specialist for SOP development. "
            "Return ONLY valid JSON — no prose, no markdown fences.\n\n"
            "JSON structure:\n"
            '{\n'
            '  "similar_sops": [{"title": "...", "relevance": 0.9, "key_points": ["..."]}],\n'
            '  "compliance_requirements": ["..."],\n'
            '  "best_practices": ["..."],\n'
            '  "sources": ["..."]\n'
            '}'
        )

        user_prompt = (
            f"Research SOPs for the following:\n"
            f"Topic: {state.topic}\n"
            f"Industry: {state.industry}\n"
            f"Known compliance requirements: {', '.join(compliance)}\n"
            f"{outline_summary}\n\n"
            f"Identify similar SOPs, best practices, and all relevant "
            f"regulatory requirements. Return findings as JSON."
        )

        raw_text = _call_bedrock(model_id, system_prompt, user_prompt)
        findings_data = _parse_json_response(raw_text)

        # Ensure compliance requirements include what we already know
        existing = findings_data.get("compliance_requirements", [])
        for c in compliance:
            if c not in existing:
                existing.append(c)
        findings_data["compliance_requirements"] = existing

        findings = ResearchFindings(**findings_data)

        state.research = findings
        state.status = WorkflowStatus.RESEARCHED
        state.current_node = "research"
        state.increment_tokens(2000)

        logger.info("Research complete — %d similar SOPs, %d compliance reqs | workflow_id=%s",
                    len(findings.similar_sops), len(findings.compliance_requirements), workflow_id)

        return (
            f"workflow_id::{workflow_id} | "
            f"Research complete: {len(findings.similar_sops)} similar SOPs, "
            f"{len(findings.compliance_requirements)} compliance requirements"
        )

    except Exception as e:
        logger.exception("Research FAILED for workflow_id=%s", workflow_id)
        state.add_error(f"Research failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Research FAILED: {e}"


research_agent = Agent(
    name="ResearchNode",
    model=BedrockModel(model_id=_get_model_id("MODEL_RESEARCH"), region=_REGION),
    system_prompt=(
        "You are the research node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_research tool "
        "with the full message as the prompt argument. "
        "Do not add commentary — just call the tool and return its result."
    ),
    tools=[run_research],
)
