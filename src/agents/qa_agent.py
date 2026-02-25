"""
QA Agent - Module 5, Section 5.1

ARCHITECTURE CHANGE: direct boto3 converse call instead of inner Agent.
See planning_agent.py for full explanation and debug instructions.
"""

import os
import json
import logging
import boto3

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, QAResult, WorkflowStatus
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
    logger.debug("=== BEDROCK CALL [qa] ===")
    logger.debug("Model: %s | Region: %s", model_id, _REGION)
    logger.debug("User prompt length: %d chars", len(user_prompt))

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
async def run_qa(prompt: str) -> str:
    """Execute the SOP quality assurance review step.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_qa called | prompt: %s", prompt[:120])

    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()
    logger.debug("Extracted workflow_id: '%s'", workflow_id)

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = f"ERROR: no state found for workflow_id='{workflow_id}' | store keys: {list(STATE_STORE.keys())}"
        logger.error(msg)
        return msg

    logger.info("State found | formatted_document: %s",
                f"{len(state.formatted_document)} chars" if state.formatted_document else "EMPTY - missing!")

    if not state.formatted_document:
        msg = f"ERROR: no formatted_document in state for workflow_id='{workflow_id}'"
        logger.error(msg)
        state.add_error(msg)
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | QA FAILED: {msg}"

    try:
        model_id = _get_model_id("MODEL_QA")

        doc_sample = (
            state.formatted_document[:3000] + "..."
            if len(state.formatted_document) > 3000
            else state.formatted_document
        )

        system_prompt = (
            "You are a quality assurance specialist for Standard Operating Procedures. "
            "Return ONLY valid JSON — no prose, no markdown fences.\n\n"
            "Score each criterion 0-10. Overall score = average of all five.\n"
            "approved = true if overall score >= 8.0, else false.\n\n"
            "JSON structure:\n"
            '{\n'
            '  "score": 8.5,\n'
            '  "feedback": "Detailed feedback",\n'
            '  "approved": true,\n'
            '  "issues": ["Issue 1"],\n'
            '  "completeness_score": 9.0,\n'
            '  "clarity_score": 8.5,\n'
            '  "safety_score": 8.0,\n'
            '  "compliance_score": 8.5,\n'
            '  "consistency_score": 9.0\n'
            '}'
        )

        user_prompt = (
            f"Review this SOP document:\n\n"
            f"Topic: {state.topic}\n"
            f"Industry: {state.industry}\n\n"
            f"Document:\n{doc_sample}\n\n"
            f"Score on: completeness, clarity, safety, compliance, consistency. "
            f"Return complete JSON."
        )

        raw_text = _call_bedrock(model_id, system_prompt, user_prompt)
        qa_data = _parse_json_response(raw_text)
        qa_result = QAResult(**qa_data)

        state.qa_result = qa_result
        state.status = WorkflowStatus.QA_COMPLETE
        state.current_node = "qa"
        state.increment_tokens(1500)

        verdict = "APPROVED" if qa_result.approved else "NEEDS REVISION"
        logger.info("QA complete — score=%.1f %s | workflow_id=%s",
                    qa_result.score, verdict, workflow_id)

        return (
            f"workflow_id::{workflow_id} | "
            f"QA complete: score={qa_result.score:.1f}/10 — {verdict}"
        )

    except Exception as e:
        logger.exception("QA FAILED for workflow_id=%s", workflow_id)
        state.qa_result = QAResult(
            score=5.0,
            feedback=f"QA error: {str(e)}",
            approved=False,
            issues=["QA failed — see logs"],
            completeness_score=5.0,
            clarity_score=5.0,
            safety_score=5.0,
            compliance_score=5.0,
            consistency_score=5.0,
        )
        state.add_error(f"QA failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | QA FAILED: {e}"


qa_agent = Agent(
    name="QANode",
    model=BedrockModel(model_id=_get_model_id("MODEL_QA"), region=_REGION),
    system_prompt=(
        "You are the quality assurance node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_qa tool "
        "with the full message as the prompt argument. "
        "Do not add commentary — just call the tool and return its result."
    ),
    tools=[run_qa],
)
