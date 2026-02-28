"""
Formatter Agent (Option B: client-side tool execution)

ONE BUG FIXED vs formatter_agent__2_.py:

FIX — FORMATTER NEVER CALLED THE LLM. FORMATTER_SYSTEM_PROMPT WAS IMPORTED
      BUT NEVER USED.

  Old code: _build_document() was pure Python string concatenation:
      doc_parts.append(f"## {section_title}")
      doc_parts.append(content or "")
    It took whatever flat strings were in content_sections and wrapped ## headings
    around them. No Bedrock call. No table rendering. No KB-style numbering.
    FORMATTER_SYSTEM_PROMPT was imported at the top but passed to nothing.

  Fix: _build_document() is replaced with _call_formatter_llm() which:
    1. Serialises the full content_sections dict (now containing rich per-section
       JSON from the fixed content_agent) as JSON.
    2. Calls Bedrock with FORMATTER_SYSTEM_PROMPT as the system prompt.
    3. Returns the rendered Markdown string from the model.

  The Python fallback (_build_document_fallback) is kept for the case where
  the LLM call fails, so the pipeline never crashes with an empty document.

  Hard post-processing strips (Step 1 from FORMATTER_SYSTEM_PROMPT) are also
  applied in Python after the LLM renders, as a safety net.
"""

import os
import re
import json
import logging
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import boto3
from strands import tool

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE
from src.prompts.system_prompts import FORMATTER_SYSTEM_PROMPT   # now actually used

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")

# Strings that must never appear in the final document — stripped in post-processing
_BANNED_LABELS = [
    "Method:",
    "Acceptance Criteria:",
    "Time Estimate:",
    "Safety Considerations:",
    "Quality Checkpoints:",
    "Overall Time Estimate:",
    "■ CRITICAL:",
    "■■ WARNING:",
    "✓ CHECKPOINT:",
]

# Section heading synonyms — lines matching these exactly are title echoes and removed
_HEADING_SYNONYMS = {
    "purpose", "scope", "purpose and scope", "responsibilities",
    "responsibilities and authorities", "definitions", "abbreviations",
    "definitions / abbreviations", "definitions and abbreviations",
    "materials", "procedure", "references", "revision history",
}


# ---------------------------------------------------------------------------
# Bedrock helpers
# ---------------------------------------------------------------------------
def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _call_bedrock_sync(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 8192,
) -> str:
    logger.debug("=== BEDROCK CALL (Formatter) ===")
    logger.debug("Model: %s | Region: %s | max_tokens=%s", model_id, _REGION, max_tokens)

    client = boto3.client("bedrock-runtime", region_name=_REGION)
    response = client.converse(
        modelId=model_id,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0},
    )
    logger.debug("Raw response: %s", json.dumps(response, default=str))

    content = response.get("output", {}).get("message", {}).get("content", [])
    if not content:
        raise ValueError(f"Bedrock returned empty content: {response}")
    text = "\n".join(p.get("text", "") for p in content if "text" in p).strip()
    if not text:
        raise ValueError(f"Bedrock returned blank text: {response}")
    logger.debug("Formatter response (%d chars):\n%s", len(text), text[:600])
    return text


async def _call_bedrock_async(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 8192,
) -> str:
    return await asyncio.to_thread(
        _call_bedrock_sync, model_id, system_prompt, user_prompt, max_tokens=max_tokens
    )


# ---------------------------------------------------------------------------
# Post-processing safety net (Python strip — catches anything the LLM missed)
# ---------------------------------------------------------------------------
def _post_process(markdown: str) -> str:
    """
    Remove any banned labels and title-echo lines that the LLM may have left.
    Applied after the LLM renders the document.
    """
    lines = markdown.split("\n")
    clean: List[str] = []
    for line in lines:
        # Remove lines that contain banned labels
        lower = line.lower().strip()
        if any(label.lower() in lower for label in _BANNED_LABELS):
            logger.debug("POST-PROCESS stripped banned label: %s", line[:80])
            continue
        # Remove lines that are pure title echoes (bare heading synonym, no other text)
        stripped = lower.lstrip("#").strip()
        if stripped in _HEADING_SYNONYMS:
            logger.debug("POST-PROCESS stripped title echo: %s", line[:80])
            continue
        clean.append(line)
    return "\n".join(clean)


# ---------------------------------------------------------------------------
# Python fallback renderer (used if LLM call fails)
# ---------------------------------------------------------------------------
def _build_document_fallback(
    title: str,
    industry: str,
    target_audience: str,
    content_sections: Dict[str, Any],
) -> str:
    """
    Minimal Python fallback that at least produces a readable document
    if the formatter LLM call fails. Does not attempt KB-style formatting.
    """
    logger.warning("Using Python fallback formatter — LLM formatter call failed")
    parts: List[str] = [
        f"# {title}",
        "",
        f"**Industry:** {industry}",
        f"**Target Audience:** {target_audience}",
        f"**Effective Date:** {datetime.now().strftime('%d-%b-%Y').upper()}",
        "",
        "---",
        "",
    ]
    for section_key, section_data in content_sections.items():
        parts.append(f"## {section_key}")
        parts.append("")
        if isinstance(section_data, dict):
            content = section_data.get("content", "")
        else:
            content = str(section_data)
        if content:
            parts.append(content)
        parts.append("")
        parts.append("---")
        parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main formatter — calls Bedrock with FORMATTER_SYSTEM_PROMPT
# ---------------------------------------------------------------------------
async def _call_formatter_llm(
    title: str,
    industry: str,
    target_audience: str,
    content_sections: Dict[str, Any],
    model_id: str,
) -> str:
    """
    Pass the full content_sections JSON to the LLM with FORMATTER_SYSTEM_PROMPT.
    The LLM renders it as KB-format Markdown (tables, numbered subsections etc.).
    """
    # Serialise the full structured content so the LLM has all tables/subsections
    content_json = json.dumps(content_sections, indent=2, ensure_ascii=False)

    user_prompt = (
        f"Convert the following SOP content JSON into a complete KB-format Markdown document.\n\n"
        f"Document title: {title}\n"
        f"Industry: {industry}\n"
        f"Target Audience: {target_audience}\n\n"
        f"CONTENT SECTIONS (full structured JSON from content agent):\n"
        f"{content_json}\n\n"
        f"Follow your system instructions exactly:\n"
        f"- Apply Step 1 (hard strip) first — remove all banned labels\n"
        f"- Render all 8 sections in order (1.0 PURPOSE through 8.0 REVISION HISTORY)\n"
        f"- Render tables for sections 3.0, 4.0, 8.0\n"
        f"- Render scope subsections (2.x) and procedure subsections (6.x) as "
        f"indented numbered items — NOT as ### headings\n"
        f"- Return the complete Markdown document only. No commentary. No code fences."
    )

    last_err: Optional[Exception] = None
    for attempt in range(1, 4):
        try:
            raw = await _call_bedrock_async(model_id, FORMATTER_SYSTEM_PROMPT, user_prompt)
            return raw
        except Exception as e:
            last_err = e
            logger.warning("Formatter Bedrock attempt %d/3 failed: %s", attempt, e)
            if attempt < 3:
                await asyncio.sleep(0.75 * attempt)

    raise last_err or RuntimeError("All formatter Bedrock retries exhausted")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_workflow_id_from_prompt(prompt: str) -> Optional[str]:
    m = re.search(r"workflow_id::([^\s\|]+)", prompt or "")
    return m.group(1) if m else None


def _order_sections_by_outline(
    content_sections: Dict[str, Any],
    state: SOPState,
) -> Dict[str, Any]:
    """Return content_sections ordered to match the outline section sequence."""
    if not getattr(state, "outline", None) or not getattr(state.outline, "sections", None):
        return content_sections

    expected = [
        getattr(s, "title", "").strip()
        for s in (state.outline.sections or [])
        if getattr(s, "title", "").strip()
    ]
    ordered: Dict[str, Any] = {}
    for title in expected:
        if title in content_sections:
            ordered[title] = content_sections[title]
    # Append any extras not in the outline
    for k, v in content_sections.items():
        if k not in ordered:
            ordered[k] = v
    return ordered


# ---------------------------------------------------------------------------
# Graph-level tool
# ---------------------------------------------------------------------------
@tool
async def run_formatting(prompt: str) -> str:
    """Execute the SOP formatting step.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_formatting called | prompt: %s", (prompt or "")[:160])

    workflow_id = _extract_workflow_id_from_prompt(prompt or "") or ""
    if not workflow_id:
        raise ValueError("Missing workflow_id in prompt.")

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = (
            f"ERROR: no state for workflow_id='{workflow_id}' | "
            f"keys={list(STATE_STORE.keys())}"
        )
        logger.error(msg)
        return msg

    try:
        if not getattr(state, "content_sections", None):
            raise ValueError("No content sections available for formatting")

        title = state.outline.title if getattr(state, "outline", None) else state.topic
        model_id = _get_model_id("MODEL_FORMATTER")

        # Order sections to match outline
        ordered_sections = _order_sections_by_outline(state.content_sections, state)

        logger.info(
            "Calling formatter LLM with %d sections | wf=%s",
            len(ordered_sections), workflow_id
        )

        try:
            # THE FIX: actually call Bedrock with FORMATTER_SYSTEM_PROMPT
            formatted_doc = await _call_formatter_llm(
                title=title,
                industry=state.industry,
                target_audience=state.target_audience,
                content_sections=ordered_sections,
                model_id=model_id,
            )
        except Exception as llm_err:
            # Fallback to Python renderer so the pipeline doesn't die
            logger.error("Formatter LLM failed, using Python fallback: %s", llm_err)
            formatted_doc = _build_document_fallback(
                title=title,
                industry=state.industry,
                target_audience=state.target_audience,
                content_sections=ordered_sections,
            )

        # Apply Python post-processing strip regardless of which path was taken
        formatted_doc = _post_process(formatted_doc)

        state.formatted_document = formatted_doc
        state.status = WorkflowStatus.FORMATTED
        state.current_node = "formatter"
        if hasattr(state, "increment_tokens"):
            state.increment_tokens(800)

        logger.info(
            "Formatting complete — %d chars | wf=%s", len(formatted_doc), workflow_id
        )
        return (
            f"workflow_id::{workflow_id} | "
            f"Formatting complete: {len(ordered_sections)} sections "
            f"({len(formatted_doc)} chars)"
        )

    except Exception as e:
        logger.exception("Formatting FAILED wf=%s", workflow_id)
        if hasattr(state, "add_error"):
            state.add_error(f"Formatting failed: {e}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Formatting FAILED: {e}"


# ---------------------------------------------------------------------------
# Node entry point (unchanged interface — drop-in replacement)
# ---------------------------------------------------------------------------
async def run_formatter_node(
    prompt: str,
    *,
    use_llama_dispatch: bool = False,
) -> str:
    logger.info(">>> run_formatter_node | wf prompt: %s", (prompt or "")[:80])
    return await run_formatting(prompt=prompt)
