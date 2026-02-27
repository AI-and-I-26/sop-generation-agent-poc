"""
Formatter Agent - Module 5, Section 5.1

Formats final SOP document using Strand Agent.

GRAPH INTEGRATION PATTERN: same as planning_agent.py — see that file.

BUG FIXED (this session):
  The outer node Agent had no `model` parameter — see planning_agent.py.
  Note: the formatting step is pure Python (no LLM call needed), but the
  node Agent still requires a model to be able to invoke its tool.
"""

import os
import logging
from datetime import datetime

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE

logger = logging.getLogger(__name__)

_DEFAULT_ARN = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)

def _bedrock_model(env_var: str) -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv(env_var, _DEFAULT_ARN),
       # region=os.getenv("AWS_REGION", "us-east-2"),
    )


# ---------------------------------------------------------------------------
# Pure-Python formatting logic (no LLM needed for this step)
# ---------------------------------------------------------------------------

def _build_document(
    title: str,
    industry: str,
    target_audience: str,
    content_sections: dict,
) -> str:
    doc_parts = []

    doc_parts.append(f"# {title}")
    doc_parts.append("")
    doc_parts.append("**Document Control**")
    doc_parts.append(f"- Document ID: SOP-{datetime.now().strftime('%Y%m%d-%H%M')}")
    doc_parts.append("- Version: 1.0")
    doc_parts.append(f"- Effective Date: {datetime.now().strftime('%Y-%m-%d')}")
    doc_parts.append(f"- Industry: {industry}")
    doc_parts.append(f"- Target Audience: {target_audience}")
    doc_parts.append("")
    doc_parts.append("---")
    doc_parts.append("")

    doc_parts.append("## Table of Contents")
    doc_parts.append("")
    for i, section_title in enumerate(content_sections.keys(), 1):
        doc_parts.append(f"{i}. {section_title}")
    doc_parts.append("")
    doc_parts.append("---")
    doc_parts.append("")

    for section_title, content in content_sections.items():
        doc_parts.append(f"## {section_title}")
        doc_parts.append("")
        doc_parts.append(content)
        doc_parts.append("")
        doc_parts.append("---")
        doc_parts.append("")

    doc_parts.append("**Approval Signatures**")
    doc_parts.append("")
    doc_parts.append("Prepared by: _________________ Date: _______")
    doc_parts.append("")
    doc_parts.append("Reviewed by: _________________ Date: _______")
    doc_parts.append("")
    doc_parts.append("Approved by: _________________ Date: _______")

    return "\n".join(doc_parts)


# ---------------------------------------------------------------------------
# Graph-level tool — called by the formatter_agent node
# ---------------------------------------------------------------------------

@tool
async def run_formatting(prompt: str) -> str:
    """Execute the SOP formatting step.

    Reads the SOPState identified by the workflow_id embedded in the prompt,
    assembles the formatted markdown document from content_sections, saves it
    to STATE_STORE, and returns a summary string for the next graph node.

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
        if not state.content_sections:
            raise ValueError("No content sections available for formatting")

        title = state.outline.title if state.outline else state.topic

        formatted_doc = _build_document(
            title=title,
            industry=state.industry,
            target_audience=state.target_audience,
            content_sections=state.content_sections,
        )

        state.formatted_document = formatted_doc
        state.status = WorkflowStatus.FORMATTED
        state.current_node = "formatter"
        state.increment_tokens(800)

        logger.info("Formatting complete — %d chars | workflow_id=%s",
                    len(formatted_doc), workflow_id)

        return (
            f"workflow_id::{workflow_id} | "
            f"Formatting complete: document assembled with "
            f"{len(state.content_sections)} sections ({len(formatted_doc)} chars)"
        )

    except Exception as e:
        logger.error("Formatting failed: %s", e)
        state.add_error(f"Formatting failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Formatting FAILED: {e}"


# ---------------------------------------------------------------------------
# The Agent node registered with GraphBuilder
# FIX: node Agent must have a model so it can actually invoke the tool.
# ---------------------------------------------------------------------------

formatter_agent = Agent(
    name="FormatterNode",
    model=_bedrock_model("MODEL_FORMATTER"),
    system_prompt=(
        "You are the formatting node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_formatting tool "
        "with the full message as the prompt argument. "
        "Do not add any commentary — just call the tool and return its result."
    ),
    tools=[run_formatting],
)