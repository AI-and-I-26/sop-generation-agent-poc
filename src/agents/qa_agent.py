# src/agents/qa_agent.py
"""
QA Agent - Module 5, Section 5.1

Quality assurance agent that reviews SOP documents.

GRAPH INTEGRATION PATTERN: same as planning_agent.py — see that file.

NOTE:
- Updated to use Anthropic Claude via AWS Bedrock inference profile.
- Removed unsupported constructor-time `max_tokens` from Agent/Model.
- Added robust JSON parsing/normalization and code-fence stripping.
"""

import os
import json
import logging
from typing import Any, Dict, List

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, QAResult, WorkflowStatus
from src.graph.state_store import STATE_STORE

logger = logging.getLogger(__name__)

# Default to Anthropic Claude Sonnet (Bedrock inference profile). Overridable via env.
_DEFAULT_ARN = (
    "arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")


def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_ARN)


def _bedrock_model(env_var: str) -> BedrockModel:
    # IMPORTANT: Do NOT pass unsupported args like max_tokens to constructor.
    # If you later need token caps, add them at the model-invoke layer in your wrapper.
    return BedrockModel(model_id=_get_model_id(env_var), region=_REGION)


# ---------------------------------------------------------------------------
# Inner LLM agent (string prompt in → string JSON out)
# ---------------------------------------------------------------------------

def _make_llm_agent() -> Agent:
    return Agent(
        name="QALLM",
        model=_bedrock_model("MODEL_QA"),
        system_prompt="""You are a quality assurance specialist for Standard Operating Procedures.

EVALUATION CRITERIA (each scored 0-10):
1. Completeness  — all mandatory sections present, adequate detail, no gaps
2. Clarity       — instructions clear and unambiguous, logical step ordering
3. Safety        — all hazards identified, warnings present, PPE specified,
                   emergency procedures included
4. Compliance    — regulations referenced, industry standards followed
5. Consistency   — formatting uniform, terminology consistent, numbering correct

SCORING RULES:
- Overall score = average of all five criteria
- Score >= 8.0  → approved: true
- Score <  8.0  → approved: false  (needs revision)

OUTPUT FORMAT — Return ONLY valid JSON:
{
  "score": 8.5,
  "feedback": "Detailed feedback here",
  "approved": true,
  "issues": ["Issue 1", "Issue 2"],
  "completeness_score": 9.0,
  "clarity_score": 8.5,
  "safety_score": 8.0,
  "compliance_score": 8.5,
  "consistency_score": 9.0
}

Be thorough, objective, and provide specific actionable feedback.""",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers if present."""
    t = text.strip()
    if t.startswith("```"):
        parts = t.split("```")
        if len(parts) >= 2:
            t = parts[1].strip()
            if t.lower().startswith("json"):
                t = t[4:].strip()
    return t


def _to_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val)
    except Exception:
        return default


def _ensure_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        # cast elements to str
        return [str(x) for x in val]
    return [str(val)]


def _normalize_qa_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize/validate the model's JSON so it matches QAResult(**kwargs)
    exactly and has consistent types/values.
    """
    # Pull individual criterion scores (permit strings)
    completeness = _to_float(data.get("completeness_score", None))
    clarity = _to_float(data.get("clarity_score", None))
    safety = _to_float(data.get("safety_score", None))
    compliance = _to_float(data.get("compliance_score", None))
    consistency = _to_float(data.get("consistency_score", None))

    # Compute overall score if missing/invalid and we have components
    raw_score = data.get("score", None)
    score = _to_float(raw_score, default=None)
    components = [x for x in [completeness, clarity, safety, compliance, consistency] if x is not None]

    if score is None or score < 0 or score > 10:
        if len(components) == 5:
            score = sum(components) / 5.0
        else:
            # fallback if model returned only 'score' as string but parsable
            score = _to_float(raw_score, default=0.0)

    # Clamp to 0..10
    score = max(0.0, min(10.0, score))

    feedback = str(data.get("feedback", "")).strip()
    issues = _ensure_list(data.get("issues", []))

    # Approved default based on policy if not provided
    approved = data.get("approved", None)
    if isinstance(approved, str):
        approved = approved.strip().lower() in {"true", "yes", "y", "approved", "1"}
    if approved is None:
        approved = bool(score >= 8.0)

    # Ensure each criterion is within 0..10 (or default to 0 if missing)
    def clamp(x: Any) -> float:
        v = _to_float(x, 0.0)
        return max(0.0, min(10.0, v))

    completeness = clamp(completeness)
    clarity = clamp(clarity)
    safety = clamp(safety)
    compliance = clamp(compliance)
    consistency = clamp(consistency)

    # Return ONLY the fields that QAResult expects
    return {
        "score": score,
        "feedback": feedback,
        "approved": bool(approved),
        "issues": issues,
        "completeness_score": completeness,
        "clarity_score": clarity,
        "safety_score": safety,
        "compliance_score": compliance,
        "consistency_score": consistency,
    }


# ---------------------------------------------------------------------------
# Graph-level tool — called by the qa_agent node
# ---------------------------------------------------------------------------

@tool
async def run_qa(prompt: str) -> str:
    """Execute the SOP quality assurance review step.

    Reads the SOPState identified by the workflow_id embedded in the prompt,
    reviews the formatted document, saves the QAResult to STATE_STORE, and
    returns a summary string for the conditional edge / end of graph.

    Args:
        prompt: The graph message string containing 'workflow_id::<id>'.
    """
    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        return f"ERROR: no state found for workflow_id={workflow_id}"

    try:
        # Accept either field (formatter writes both in newer code)
        formatted_doc = state.formatted_markdown or state.formatted_document
        if not formatted_doc:
            raise ValueError("No formatted document available for QA review")

        llm = _make_llm_agent()

        # Keep prompt reasonably bounded
        doc_sample = (
            formatted_doc[:3000] + "..."
            if len(formatted_doc) > 3000
            else formatted_doc
        )

        qa_prompt = (
            f"Review this SOP document:\n\n"
            f"Topic: {state.topic}\n"
            f"Industry: {state.industry}\n\n"
            f"Document Sample:\n{doc_sample}\n\n"
            f"Provide a comprehensive quality assessment with:\n"
            f"1. Overall score (0-10)\n"
            f"2. Individual criterion scores\n"
            f"3. Specific feedback on strengths and weaknesses\n"
            f"4. List of issues to address\n"
            f"5. Approval decision (true if score >= 8.0)\n\n"
            f"Return complete JSON with all required fields."
        )

        response = await llm.invoke_async(qa_prompt)
        response_text = _strip_code_fences(str(response))

        # Parse and normalize JSON
        qa_json = json.loads(response_text)
        normalized = _normalize_qa_json(qa_json)

        qa_result = QAResult(**normalized)

        # Persist result
        state.qa_result = qa_result
        state.status = WorkflowStatus.QA_COMPLETE   # Preserve original behavior
        state.current_node = "qa"
        state.increment_tokens(1500)

        verdict = "APPROVED" if qa_result.approved else "NEEDS REVISION"
        logger.info(
            "QA complete — score=%.1f %s | workflow_id=%s",
            qa_result.score, verdict, workflow_id
        )

        return (
            f"workflow_id::{workflow_id} | "
            f"QA complete: score={qa_result.score:.1f}/10 — {verdict}"
        )

    except Exception as e:
        logger.error("QA review failed: %s", e)
        # Safe fallback to avoid breaking the pipeline
        state.qa_result = QAResult(
            score=5.0,
            feedback=f"QA review error: {str(e)}",
            approved=False,
            issues=["QA review failed — see logs"],
            completeness_score=5.0,
            clarity_score=5.0,
            safety_score=5.0,
            compliance_score=5.0,
            consistency_score=5.0,
        )
        state.add_error(f"QA review failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | QA FAILED: {e}"


# ---------------------------------------------------------------------------
# The Agent node registered with GraphBuilder
# ---------------------------------------------------------------------------

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
    # Do NOT pass max_tokens here.
)