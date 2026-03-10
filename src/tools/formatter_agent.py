# src/agents/formatter_agent.py
"""
formatter_agent.py — Formatter Agent for the SOP pipeline.

Node 4 of 5. Converts content sections into KB‑style Markdown with
STRICT header/footer enforcement.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE
from src.prompts.system_prompts import FORMATTER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------------------------

_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")

# Tuning knobs (env overrides)
_MAX_JSON_BYTES = int(os.getenv("FORMATTER_MAX_JSON_BYTES", "120000"))
_MAX_CONCURRENCY = int(os.getenv("FORMATTER_MAX_CONCURRENCY", "2"))
_READ_TIMEOUT_SECONDS = int(os.getenv("FORMATTER_READ_TIMEOUT", "180"))
_MAX_ATTEMPTS = int(os.getenv("FORMATTER_MAX_ATTEMPTS", "5"))
_BACKOFF_BASE = float(os.getenv("FORMATTER_BACKOFF_BASE", "1.6"))  # exponential
_CONNECT_TIMEOUT_SECONDS = int(os.getenv("FORMATTER_CONNECT_TIMEOUT", "10"))

def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)

# FIX: Default header/footer used when kb_header/footer_template are empty.
# The KB-chunk heuristic in the old research_agent always returned empty strings
# because Bedrock KB returns mid-document semantic slices — never the page-1
# metadata rows.  These defaults guarantee every output has a professional
# document header and footer.
_DEFAULT_HEADER_TEMPLATE = """---
| Field | Value |
|---|---|
| **Title** | {{title}} |
| **Document ID** | {{document_id}} |
| **Version** | {{version}} |
| **Effective Date** | {{effective_date}} |
| **Industry** | {{industry}} |
| **Target Audience** | {{target_audience}} |

---
"""

_DEFAULT_FOOTER_TEMPLATE = (
    "\n---\n"
    "*This document is controlled. Unauthorised reproduction is prohibited.*\n"
    "*Always verify you are reading the current approved version before use.*"
)


def _bedrock_model(env_var: str) -> BedrockModel:
    """
    FIX: Removed unsupported 'region' and 'client_config' kwargs that were
    generating a UserWarning on every agent instantiation.
    BedrockModel reads AWS_REGION from the environment automatically.
    """
    return BedrockModel(model_id=_get_model_id(env_var))


# ---------------------------------------------------------------------------
# DOCUMENT HEADER ASSEMBLY
# ---------------------------------------------------------------------------

def _build_document_header(state: SOPState) -> Dict[str, Any]:
    """Constructs the metadata used for header placeholders."""
    title = state.outline.title if state.outline else state.topic
    return {
        "title": title,
        "document_id": f"SOP-{datetime.now().strftime('%Y%m%d-%H%M')}",
        "version": "1.0",
        "effective_date": datetime.now().strftime("%d-%b-%Y"),
        "industry": state.industry,
        "target_audience": state.target_audience,
    }


# ---------------------------------------------------------------------------
# HEADER/FOOTER FINALIZER
# ---------------------------------------------------------------------------

def _apply_header_footer(
    header_template: str,
    footer_template: str,
    metadata: Dict[str, str],
    body: str
) -> str:
    """
    Prepend header and append footer to the Markdown body.

    FIX: Falls back to _DEFAULT_HEADER_TEMPLATE / _DEFAULT_FOOTER_TEMPLATE
    when the KB-extracted templates are empty strings, guaranteeing every
    output document has a proper document header and footer.
    """
    effective_header = (header_template or "").strip() or _DEFAULT_HEADER_TEMPLATE
    effective_footer = (footer_template or "").strip() or _DEFAULT_FOOTER_TEMPLATE

    if not (header_template or "").strip():
        logger.info("kb_header_template empty — applying built-in default header")
    if not (footer_template or "").strip():
        logger.info("kb_footer_template empty — applying built-in default footer")

    # Substitute {{placeholder}} variables
    hdr = effective_header
    for key, value in metadata.items():
        hdr = hdr.replace("{{" + key + "}}", str(value))

    return hdr.strip() + "\n\n" + body.strip() + "\n\n" + effective_footer.strip()


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _json_len(obj: Any) -> int:
    try:
        return len(json.dumps(obj, ensure_ascii=False))
    except Exception:
        return 0

def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        parts = t.split("```")
        if len(parts) >= 2:
            t = parts[1].strip()
            if t.lower().startswith("json"):
                t = t[4:].strip()
    return t

def _ordered_section_keys(state: SOPState) -> List[str]:
    """
    Try to order sections according to the outline numbers if available.
    Fallback to the dict order in content_sections.
    """
    if state.outline and state.outline.sections:
        ordered: List[str] = []
        seen = set()
        for sec in state.outline.sections:
            k = sec.number
            if k in state.content_sections and k not in seen:
                ordered.append(k)
                seen.add(k)
        # append any remaining
        for k in state.content_sections.keys():
            if k not in seen:
                ordered.append(k)
        return ordered
    return list(state.content_sections.keys())

async def _invoke_with_retries(llm: Agent, prompt: str) -> str:
    """
    Invoke the LLM with retries and simple backoff.
    Note: asyncio.wait_for adds a hard cap; underlying botocore read_timeout
    is increased in _bedrock_model (best effort).
    """
    last_err: Optional[Exception] = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            start = time.time()
            # Give a bit more than read timeout to allow coroutine wrapping
            resp = await asyncio.wait_for(llm.invoke_async(prompt), timeout=_READ_TIMEOUT_SECONDS + 15)
            elapsed = time.time() - start
            logger.info("LLM call succeeded | attempt=%d | elapsed=%.1fs | bytes_prompt=%d",
                        attempt, elapsed, len(prompt))
            return str(resp).strip()
        except Exception as e:
            last_err = e
            # Jittered exponential backoff
            backoff = (_BACKOFF_BASE ** (attempt - 1)) + (0.05 * attempt)
            logger.warning("LLM call failed | attempt=%d/%d | will retry in %.2fs | error=%s",
                           attempt, _MAX_ATTEMPTS, backoff, e)
            if attempt == _MAX_ATTEMPTS:
                break
            await asyncio.sleep(backoff)
    raise RuntimeError(f"LLM call failed after {_MAX_ATTEMPTS} attempts: {last_err}")

def _llm_from_env(name: str) -> Agent:
    return Agent(
        name=name,
        model=_bedrock_model("MODEL_FORMATTER"),
        system_prompt=FORMATTER_SYSTEM_PROMPT,
    )


# ---------------------------------------------------------------------------
# LLM FORMATTER — WHOLE DOCUMENT
# ---------------------------------------------------------------------------

async def _run_llm_formatter_whole(state: SOPState) -> str:
    """
    Single-shot: send all sections and context at once.
    """
    header_metadata = _build_document_header(state)
    payload = {
        "document_header": header_metadata,
        "sections": state.content_sections,
        "kb_format_context": state.kb_format_context or {},
        "kb_header_template": state.kb_header_template or "",
        "kb_footer_template": state.kb_footer_template or "",
    }

    user_prompt = (
        "Convert the following SOP JSON payload into KB-format Markdown "
        "following your system prompt rules exactly.\n\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n\n"
        'Return ONLY a JSON object: {"formatted_markdown": "..."}'
    )

    llm = _llm_from_env("FormatterLLM(whole)")
    text = await _invoke_with_retries(llm, user_prompt)
    text = _strip_code_fences(text)

    try:
        parsed = json.loads(text)
        if "formatted_markdown" in parsed:
            base_md = parsed["formatted_markdown"]
        else:
            logger.warning("Model returned JSON but missing formatted_markdown; using raw text.")
            base_md = text
    except Exception:
        logger.warning("Formatter returned non-JSON response (whole); using raw output.")
        base_md = text

    # Apply header/footer once
    final_doc = _apply_header_footer(
        state.kb_header_template or "",
        state.kb_footer_template or "",
        header_metadata,
        base_md,
    )
    return final_doc


# ---------------------------------------------------------------------------
# LLM FORMATTER — PER SECTION (CHUNKED)
# ---------------------------------------------------------------------------

async def _format_one_section(
    section_key: str,
    section_payload: Any,
    kb_format_context: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Formats a single section. Returns (section_key, formatted_markdown).
    """
    # Keep prompt minimal: only the section, plus style hints
    payload = {
        "section_key": section_key,
        "section": section_payload,
        "kb_format_context": kb_format_context or {},
    }
    user_prompt = (
        "Format ONLY the given section into KB-style Markdown. "
        "Do not include document-level headers/footers or cover/title pages. "
        "Return ONLY a JSON object: {\"formatted_markdown\": \"...\"}\n\n"
        f"{json.dumps(payload, indent=2, ensure_ascii=False)}"
    )

    llm = _llm_from_env(f"FormatterLLM(sec:{section_key})")
    text = await _invoke_with_retries(llm, user_prompt)
    text = _strip_code_fences(text)

    try:
        parsed = json.loads(text)
        if "formatted_markdown" in parsed:
            formatted = parsed["formatted_markdown"]
        else:
            logger.warning("Section %s: JSON missing formatted_markdown; using raw text.", section_key)
            formatted = text
    except Exception:
        logger.warning("Section %s: non-JSON response; using raw output.", section_key)
        formatted = text

    return section_key, str(formatted or "").strip()

async def _run_llm_formatter_chunked(state: SOPState) -> str:
    """
    Formats each section separately and stitches them together.
    """
    header_metadata = _build_document_header(state)
    keys = _ordered_section_keys(state)

    sem = asyncio.Semaphore(_MAX_CONCURRENCY)

    async def _bounded_format(key: str, payload: Any) -> Tuple[str, str]:
        async with sem:
            return await _format_one_section(key, payload, state.kb_format_context or {})

    tasks = [asyncio.create_task(_bounded_format(k, state.content_sections[k])) for k in keys]
    results: List[Tuple[str, str]] = await asyncio.gather(*tasks, return_exceptions=False)

    # Rebuild in order (keys list order)
    formatted_map = {k: v for k, v in results}
    stitched = "\n\n".join([formatted_map.get(k, "") for k in keys if formatted_map.get(k, "")])

    # Final header/footer pass
    final_doc = _apply_header_footer(
        state.kb_header_template or "",
        state.kb_footer_template or "",
        header_metadata,
        stitched,
    )
    return final_doc


# ---------------------------------------------------------------------------
# STRATEGY SELECTOR
# ---------------------------------------------------------------------------

async def _run_llm_formatter(state: SOPState) -> str:
    """
    Choose whole-document vs per-section based on payload size.
    """
    # Fast size estimate to decide strategy
    header_metadata = _build_document_header(state)
    size_probe = {
        "document_header": header_metadata,
        "sections": state.content_sections,
        "kb_format_context": state.kb_format_context or {},
        "kb_header_template": state.kb_header_template or "",
        "kb_footer_template": state.kb_footer_template or "",
    }
    approx_bytes = _json_len(size_probe)

    logger.info("Formatter payload size ~%d bytes | sections=%d", approx_bytes, len(state.content_sections or {}))

    # If small enough, try whole-document; otherwise, chunk
    if approx_bytes > _MAX_JSON_BYTES:
        logger.info("Payload exceeds %d bytes — using per-section chunked formatting.", _MAX_JSON_BYTES)
        return await _run_llm_formatter_chunked(state)
    else:
        logger.info("Payload within limit — using single-shot whole-document formatting.")
        return await _run_llm_formatter_whole(state)


# ---------------------------------------------------------------------------
# GRAPH TOOL: run_formatting()
# ---------------------------------------------------------------------------

@tool
async def run_formatting(prompt: str) -> str:
    logger.info(">>> run_formatting | prompt: %.120s", prompt)

    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()

    state: SOPState = STATE_STORE.get(workflow_id)

    if state is None:
        return f"ERROR: no state found for workflow_id={workflow_id}"

    try:
        if not state.content_sections:
            raise ValueError("No content sections available for formatting.")

        t0 = time.time()
        formatted_doc = await _run_llm_formatter(state)
        elapsed = time.time() - t0

        state.formatted_markdown = formatted_doc
        state.formatted_document = formatted_doc
        state.status = WorkflowStatus.FORMATTED
        state.current_node = "formatter"
        # This is a rough token proxy; consider adding real token usage if available
        state.increment_tokens(800)

        logger.info(
            "Formatting complete — %d chars | elapsed=%.1fs | workflow_id=%s",
            len(formatted_doc), elapsed, workflow_id,
        )

        return (
            f"workflow_id::{workflow_id} | Formatting complete "
            f"({len(state.content_sections)} sections, {len(formatted_doc)} chars, {elapsed:.1f}s)"
        )

    except Exception as e:
        logger.error("Formatting FAILED: %s", e, exc_info=True)
        state.add_error(f"Formatting failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Formatting FAILED: {e}"


# ---------------------------------------------------------------------------
# NODE AGENT
# ---------------------------------------------------------------------------

formatter_agent = Agent(
    name="FormatterNode",
    model=_bedrock_model("MODEL_FORMATTER"),
    system_prompt=(
        "You are the formatting node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_formatting tool "
        "with the full message as the prompt argument. "
        "Do not add commentary."
    ),
    tools=[run_formatting],
)