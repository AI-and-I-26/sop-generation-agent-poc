"""
qa_agent.py — Quality Assurance Agent for the SOP pipeline.

ROLE IN PIPELINE:
    Node 5 of 5 (and potentially repeated via the revision loop).
    Reviews the formatted Markdown document against the formatting conventions
    discovered from YOUR Knowledge Base — not any hardcoded standard.

DYNAMIC EVALUATION:
    The QA agent receives kb_format_context in the review payload.
    It checks the document against THAT context:
      - Are the section titles the same as the KB's?
      - Do table sections have the right columns?
      - Does the writing style match?
      - Are any banned elements present?

    If kb_format_context is absent, it falls back to general SOP quality checks.
"""

import json
import logging
import os
from typing import Any, Dict

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import QAResult, SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE
from src.prompts.system_prompts import QA_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ── CONFIGURATION ──────────────────────────────────────────────────────────────

_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")


def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _bedrock_model(env_var: str) -> BedrockModel:
    return BedrockModel(model_id=_get_model_id(env_var))


# ── INNER LLM AGENT ────────────────────────────────────────────────────────────

def _make_qa_llm() -> Agent:
    """
    Create a single-use inner LLM agent for QA scoring.

    This agent receives the SOP document text and returns a JSON object
    with five criterion scores plus the overall score and approval decision.
    The QA_SYSTEM_PROMPT defines all evaluation rules.
    """
    return Agent(
        name="QALLM",
        model=_bedrock_model("MODEL_QA"),
        system_prompt=QA_SYSTEM_PROMPT,
        max_tokens=2048,   # plenty for the JSON score object
    )


# ── STRANDS TOOL ───────────────────────────────────────────────────────────────

@tool
async def run_qa(prompt: str) -> str:
    """
    Execute the SOP quality assurance review.

    Reviews the formatted_markdown stored in SOPState against the KB format
    standard.  Populates state.qa_result and state.qa_policy_feedback (for
    the revision loop).

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.

    Returns:
        "workflow_id::<id> | QA complete: ..." or error string.
    """
    logger.info(">>> run_qa | prompt: %.120s", prompt)

    # ── Extract workflow_id ──────────────────────────────────────────────
    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        return f"ERROR: no state found for workflow_id={workflow_id}"

    try:
        # Use the primary KB-format output; fall back to legacy field
        document = state.formatted_markdown or state.formatted_document
        if not document:
            raise ValueError(
                "No formatted document available for QA review. "
                "Ensure formatter_agent ran successfully."
            )

        # ── Build QA prompt ──────────────────────────────────────────────
        # Include kb_format_context so QA evaluates against the actual KB's
        # conventions — not any hardcoded standard.
        kb_format_ctx_str = (
            json.dumps(state.kb_format_context, indent=2)
            if state.kb_format_context
            else "(not available — evaluate against general SOP quality standards)"
        )

        doc_sample = document[:4000] + ("..." if len(document) > 4000 else "")

        qa_prompt = (
            f"Review this SOP document:\n\n"
            f"Topic:    {state.topic}\n"
            f"Industry: {state.industry}\n\n"
            f"KB FORMAT CONTEXT (conventions from your Knowledge Base):\n"
            f"{kb_format_ctx_str}\n\n"
            f"Document:\n{doc_sample}\n\n"
            "Evaluate the document against the KB FORMAT CONTEXT above.\n"
            "Return ONLY the JSON score object defined in your system prompt."
        )

        # ── Call inner LLM ───────────────────────────────────────────────
        llm = _make_qa_llm()
        response = await llm.invoke_async(qa_prompt)
        response_text = str(response).strip()

        # Strip code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.lower().startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        qa_data: Dict[str, Any] = json.loads(response_text)

        # Ensure overall score is set (compute average if missing)
        if "score" not in qa_data or qa_data.get("score") is None:
            subscores = [
                qa_data.get("completeness_score", 0.0),
                qa_data.get("clarity_score",      0.0),
                qa_data.get("safety_score",        0.0),
                qa_data.get("compliance_score",    0.0),
                qa_data.get("consistency_score",   0.0),
            ]
            qa_data["score"] = round(sum(subscores) / len(subscores), 2)

        # Ensure approved flag matches score threshold
        if "approved" not in qa_data:
            qa_data["approved"] = qa_data["score"] >= 8.0

        # ── Build QAResult ───────────────────────────────────────────────
        qa_result = QAResult(**qa_data)

        # ── Write back to shared state ───────────────────────────────────
        state.qa_result = qa_result
        state.status = WorkflowStatus.QA_COMPLETE
        state.current_node = "qa"
        state.increment_tokens(1500)

        # If not approved, surface issues as policy feedback for the content agent
        if not qa_result.approved and qa_result.issues:
            state.qa_policy_feedback = qa_result.issues

        verdict = "APPROVED" if qa_result.approved else "NEEDS REVISION"
        logger.info(
            "QA complete — score=%.1f %s | retry=%d | workflow_id=%s",
            qa_result.score, verdict, state.retry_count, workflow_id
        )

        return (
            f"workflow_id::{workflow_id} | "
            f"QA complete: score={qa_result.score:.1f}/10 — {verdict}"
        )

    except Exception as e:
        logger.error("QA review FAILED: %s", e, exc_info=True)

        # Set a failing QAResult so the revision loop can respond correctly
        state.qa_result = QAResult(
            score=0.0,
            feedback=f"QA review error: {str(e)}",
            approved=False,
            issues=["QA review failed — see logs"],
            completeness_score=0.0,
            clarity_score=0.0,
            safety_score=0.0,
            compliance_score=0.0,
            consistency_score=0.0,
        )
        state.add_error(f"QA review failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | QA FAILED: {e}"


# ── NODE AGENT ─────────────────────────────────────────────────────────────────

qa_agent = Agent(
    name="QANode",
    model=_bedrock_model("MODEL_QA"),
    system_prompt=(
        "You are the quality assurance node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_qa tool "
        "with the full message as the prompt argument. "
        "Do not add any commentary — just call the tool and return its result."
    ),
    tools=[run_qa],
)