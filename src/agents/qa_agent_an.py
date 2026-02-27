"""
QA Agent - Module 5, Section 5.1

Quality assurance agent that reviews SOP documents.

GRAPH INTEGRATION PATTERN: same as planning_agent.py — see that file.

BUG FIXED (this session):
  The outer node Agent had no `model` parameter — see planning_agent.py.
"""

import os
import json
import logging

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, QAResult, WorkflowStatus
from src.graph.state_store import STATE_STORE

logger = logging.getLogger(__name__)

_DEFAULT_ARN = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)

def _bedrock_model(env_var: str) -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv(env_var, _DEFAULT_ARN),
        #region=os.getenv("AWS_REGION", "us-east-2"),
    )


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
        max_tokens=2048,
    )


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
        if not state.formatted_document:
            raise ValueError("No formatted document available for QA review")

        llm = _make_llm_agent()

        doc_sample = (
            state.formatted_document[:3000] + "..."
            if len(state.formatted_document) > 3000
            else state.formatted_document
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
        response_text = str(response).strip()

        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        qa_data = json.loads(response_text)
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
        logger.error("QA review failed: %s", e)
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
# FIX: node Agent must have a model so it can actually invoke the tool.
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
)