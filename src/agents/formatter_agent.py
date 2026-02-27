"""
Formatter Agent - Module X (Option B: client-side tool execution)

Formats final SOP document (pure Python — no LLM calls).

GRAPH INTEGRATION PATTERN:
  - The graph passes a plain string containing 'workflow_id::<id>'.
  - STATE_STORE holds SOPState keyed by workflow_id.
  - This module exposes:
      * async @tool run_formatting(prompt: str) -> str     (does the real work)
      * async run_formatter_node(prompt: str, use_llama_dispatch: bool=False) -> str
  - In the graph, wrap run_formatter_node with LocalNodeAgent (see sop_workflow.py).
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple

from strands import tool

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE

# --- Import centralized system prompt (adjust path if your file lives elsewhere) ---
try:
    from src.prompts.system_prompts import FORMATTER_SYSTEM_PROMPT  # preferred path
except Exception:
    # Fallback for older layout where the file lived under agents/
    from src.agents.systems_prompt import FORMATTER_SYSTEM_PROMPT  # type: ignore

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _extract_workflow_id_from_prompt(prompt: str) -> Optional[str]:
    """
    Extract 'workflow_id::<id>' from a text prompt or message content.
    """
    m = re.search(r"workflow_id::([^\s\|]+)", prompt or "")
    return m.group(1) if m else None


def _order_sections_by_outline(
    content_sections: Dict[str, str],
    state: SOPState
) -> List[Tuple[str, str]]:
    """
    Return a list of (section_title, content) ordered by the outline if available.
    Any content keys not found in the outline are appended at the end in insertion order.
    """
    if not getattr(state, "outline", None) or not getattr(state.outline, "sections", None):
        # Fall back to insertion order (Py3.7+ dict preserves insertion order)
        return list(content_sections.items())

    # Titles from outline in order
    expected_titles = [getattr(s, "title", "").strip() for s in (state.outline.sections or [])]
    expected_titles = [t for t in expected_titles if t]  # drop empties

    # Map content by title
    ordered: List[Tuple[str, str]] = []
    seen = set()

    for title in expected_titles:
        if title in content_sections:
            ordered.append((title, content_sections[title]))
            seen.add(title)

    # Append any extras that weren't in the outline (in insertion order)
    for k, v in content_sections.items():
        if k not in seen:
            ordered.append((k, v))

    return ordered


def _build_document(
    title: str,
    industry: str,
    target_audience: str,
    ordered_sections: List[Tuple[str, str]],
) -> str:
    """
    Assemble the final Markdown document.
    `ordered_sections` is a list of (section_title, content) in the desired order.
    """
    doc_parts: List[str] = []

    # Header & control
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

    # Table of contents
    doc_parts.append("## Table of Contents")
    doc_parts.append("")
    for i, (section_title, _) in enumerate(ordered_sections, 1):
        doc_parts.append(f"{i}. {section_title}")
    doc_parts.append("")
    doc_parts.append("---")
    doc_parts.append("")

    # Sections
    for section_title, content in ordered_sections:
        # Ensure content already contains numbered steps etc. from content generation
        doc_parts.append(f"## {section_title}")
        doc_parts.append("")
        doc_parts.append(content or "")
        doc_parts.append("")
        doc_parts.append("---")
        doc_parts.append("")

    # Signatures
    doc_parts.append("**Approval Signatures**")
    doc_parts.append("")
    doc_parts.append("Prepared by: _________________ Date: _______")
    doc_parts.append("")
    doc_parts.append("Reviewed by: _________________ Date: _______")
    doc_parts.append("")
    doc_parts.append("Approved by: _________________ Date: _______")

    return "\n".join(doc_parts)


# -----------------------------------------------------------------------------
# Graph-level tool — does the ACTUAL formatting and writes to STATE_STORE
# -----------------------------------------------------------------------------
@tool
async def run_formatting(prompt: str) -> str:
    """
    Execute the SOP formatting step.

    Reads the SOPState identified by the workflow_id embedded in the prompt,
    assembles the formatted markdown document from content_sections, saves it
    to STATE_STORE, and returns a summary string for the next graph node.

    Args:
        prompt: The graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_formatting called | prompt: %s", (prompt or "")[:160])

    workflow_id = _extract_workflow_id_from_prompt(prompt or "") or ""
    logger.debug("Extracted workflow_id: '%s'", workflow_id)

    # Fail fast if workflow_id is missing (helps catch graph prompt wiring issues early)
    if not workflow_id:
        raise ValueError(
            "Missing workflow_id in prompt; expected 'workflow_id::<id>' within the message content."
        )

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = f"ERROR: no state found for workflow_id='{workflow_id}' | store keys: {list(STATE_STORE.keys())}"
        logger.error(msg)
        return msg

    try:
        if not getattr(state, "content_sections", None):
            raise ValueError("No content sections available for formatting")

        title = state.outline.title if getattr(state, "outline", None) else state.topic

        # Ensure a stable, user-expected ordering (outline order if present)
        ordered_sections = _order_sections_by_outline(state.content_sections, state)

        formatted_doc = _build_document(
            title=title,
            industry=state.industry,
            target_audience=state.target_audience,
            ordered_sections=ordered_sections,
        )

        # Persist results
        state.formatted_document = formatted_doc
        state.status = WorkflowStatus.FORMATTED
        state.current_node = "formatter"
        # Token accounting (rough; formatting is pure python)
        if hasattr(state, "increment_tokens"):
            state.increment_tokens(800)

        logger.info(
            "Formatting complete — %d chars | sections=%d | workflow_id=%s",
            len(formatted_doc),
            len(ordered_sections),
            workflow_id,
        )

        return (
            f"workflow_id::{workflow_id} | "
            f"Formatting complete: document assembled with "
            f"{len(ordered_sections)} sections ({len(formatted_doc)} chars)"
        )

    except Exception as e:
        logger.exception("Formatting FAILED for workflow_id=%s", workflow_id)
        if hasattr(state, "add_error"):
            state.add_error(f"Formatting failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Formatting FAILED: {e}"


# -----------------------------------------------------------------------------
# Node entry point for Graph (client-side execution) — ASYNC WRAPPER
# -----------------------------------------------------------------------------
async def run_formatter_node(
    prompt: str,
    *,
    use_llama_dispatch: bool = False
) -> str:
    """
    Entry point for the FORMATTER node under Option B. (ASYNC)

    Formatting is pure Python; we ignore LLaMA dispatch and directly execute
    the local async tool `run_formatting` (deterministic and cheap).

    Returns:
      The tool result string to pass to the next node.
    """
    logger.info(">>> run_formatter_node | use_llama_dispatch=%s (ignored for formatting)", use_llama_dispatch)
    return await run_formatting(prompt=prompt)


# -----------------------------------------------------------------------------
# NOTE:
# We intentionally do NOT export a `formatter_agent = Agent(...)` here.
# Under Option B, your graph should wrap `run_formatter_node` with LocalNodeAgent:
#
#   from src.agents.formatter_agent import run_formatter_node
#   formatter_node = LocalNodeAgent("formatter", lambda p: run_formatter_node(p, use_llama_dispatch=False))
#   gb.add_node(formatter_node, "formatter")
# -----------------------------------------------------------------------------