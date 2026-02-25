"""
Formatter Agent - Module 5, Section 5.1

ARCHITECTURE CHANGE: pure Python formatting (no LLM needed).
See planning_agent.py for full debug instructions.
"""

import os
import logging
from datetime import datetime

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


def _build_document(title: str, industry: str, target_audience: str, content_sections: dict) -> str:
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


@tool
async def run_formatting(prompt: str) -> str:
    """Execute the SOP formatting step.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_formatting called | prompt: %s", prompt[:120])

    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()
    logger.debug("Extracted workflow_id: '%s'", workflow_id)

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = f"ERROR: no state found for workflow_id='{workflow_id}' | store keys: {list(STATE_STORE.keys())}"
        logger.error(msg)
        return msg

    logger.info("State found | content_sections: %s",
                list(state.content_sections.keys()) if state.content_sections else "EMPTY - missing!")

    if not state.content_sections:
        msg = f"ERROR: no content_sections in state for workflow_id='{workflow_id}'"
        logger.error(msg)
        state.add_error(msg)
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Formatting FAILED: {msg}"

    try:
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
            f"Formatting complete: {len(state.content_sections)} sections, "
            f"{len(formatted_doc)} chars"
        )

    except Exception as e:
        logger.exception("Formatting FAILED for workflow_id=%s", workflow_id)
        state.add_error(f"Formatting failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Formatting FAILED: {e}"


formatter_agent = Agent(
    name="FormatterNode",
    model=BedrockModel(model_id=_get_model_id("MODEL_FORMATTER"), region=_REGION),
    system_prompt=(
        "You are the formatting node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_formatting tool "
        "with the full message as the prompt argument. "
        "Do not add commentary — just call the tool and return its result."
    ),
    tools=[run_formatting],
)
