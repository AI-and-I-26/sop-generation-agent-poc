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

import boto3
from botocore.config import Config as _BotoCfg
from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE
from src.prompts.system_prompts import FORMATTER_SYSTEM_PROMPT
from src.prompts.document_templates import KB_APPROVAL_TABLE, KB_TEMPLATE_DEFAULTS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------------------------

_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")

# Tuning knobs (env overrides)
# Recommended env: FORMATTER_MAX_JSON_BYTES=80000
_MAX_JSON_BYTES = int(os.getenv("FORMATTER_MAX_JSON_BYTES", "80000"))
_MAX_CONCURRENCY = int(os.getenv("FORMATTER_MAX_CONCURRENCY", "2"))
_READ_TIMEOUT_SECONDS = int(os.getenv("FORMATTER_READ_TIMEOUT", "180"))
_MAX_ATTEMPTS = int(os.getenv("FORMATTER_MAX_ATTEMPTS", "5"))
_BACKOFF_BASE = float(os.getenv("FORMATTER_BACKOFF_BASE", "1.6"))  # exponential
_CONNECT_TIMEOUT_SECONDS = int(os.getenv("FORMATTER_CONNECT_TIMEOUT", "10"))

def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)

def _bedrock_model(env_var: str) -> BedrockModel:
    """
    BedrockModel used ONLY for the Strands Agent wrapper (planning/qa nodes).
    NOTE: BedrockModel ignores client_config so we cannot control read_timeout
    through it. Heavy formatter calls use _invoke_bedrock_direct() instead.
    """
    model_id = _get_model_id(env_var)
    return BedrockModel(model_id=model_id)


def _make_boto3_client():
    """
    Create a boto3 bedrock-runtime client with FORMATTER_READ_TIMEOUT (default 400s).
    This bypasses BedrockModel entirely so we get reliable long-running calls.
    """
    read_to = int(os.getenv("FORMATTER_READ_TIMEOUT", "400"))
    conn_to = int(os.getenv("FORMATTER_CONNECT_TIMEOUT", "10"))
    return boto3.client(
        "bedrock-runtime",
        region_name=_REGION,
        config=_BotoCfg(
            read_timeout=read_to,
            connect_timeout=conn_to,
            retries={"max_attempts": 1, "mode": "standard"},
        ),
    )


def _invoke_bedrock_direct(system_prompt: str, user_prompt: str) -> str:
    """
    Call Bedrock invoke_model directly with a long read timeout.
    Returns the assistant text response.
    Retries up to _MAX_ATTEMPTS times with exponential backoff.
    """
    model_id = _get_model_id("MODEL_FORMATTER")
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 8192,
        "temperature": 0.0,
        "system": system_prompt,
        "messages": [{"role": "user", "content": [{"type": "text", "text": user_prompt}]}],
    }
    last_err: Optional[Exception] = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            t0 = time.time()
            client = _make_boto3_client()
            resp = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body).encode("utf-8"),
            )
            raw = resp.get("body")
            body_json = json.loads(raw.read()) if raw is not None else {}
            # Extract text from Anthropic Messages response
            content_blocks = body_json.get("content", [])
            text = ""
            for blk in content_blocks:
                if isinstance(blk, dict) and blk.get("type") == "text":
                    text += blk.get("text", "")
            elapsed = time.time() - t0
            logger.info(
                "Formatter direct invoke OK | attempt=%d | elapsed=%.1fs | chars=%d",
                attempt, elapsed, len(text),
            )
            return text.strip()
        except Exception as e:
            last_err = e
            backoff = (_BACKOFF_BASE ** (attempt - 1)) + (0.05 * attempt)
            logger.warning(
                "Formatter direct invoke failed | attempt=%d/%d | retry in %.2fs | error=%s",
                attempt, _MAX_ATTEMPTS, backoff, e,
            )
            if attempt < _MAX_ATTEMPTS:
                time.sleep(backoff)
    raise RuntimeError(f"Formatter invoke failed after {_MAX_ATTEMPTS} attempts: {last_err}")


# ---------------------------------------------------------------------------
# DOCUMENT HEADER ASSEMBLY
# ---------------------------------------------------------------------------

def _build_document_header(state: SOPState) -> Dict[str, Any]:
    """Build header metadata, merging KB_TEMPLATE_DEFAULTS so every
    {{placeholder}} in templates is covered and no raw syntax leaks out.
    """
    title = state.outline.title if state.outline else state.topic
    metadata: Dict[str, Any] = dict(KB_TEMPLATE_DEFAULTS)
    metadata.update({
        "title":           title,
        "document_id":     f"SOP-{datetime.now().strftime('%Y%m%d-%H%M')}",
        "version":         "1.0",
        "effective_date":  datetime.now().strftime("%d-%b-%Y"),
        "industry":        state.industry,
        "target_audience": state.target_audience,
    })
    return metadata


# ---------------------------------------------------------------------------
# HEADER/FOOTER FINALIZER
# ---------------------------------------------------------------------------

def _apply_header_footer(
    header_template: str,
    footer_template: str,
    metadata: Dict[str, str],
    body: str
) -> str:
    """Assemble final document: header + approval table + body + footer.

    All {{placeholders}} in header, approval table, and footer are
    substituted from metadata before assembly.  KB_APPROVAL_TABLE is
    injected on page 1 to satisfy GxP signature requirements.
    """
    def _sub(template: str) -> str:
        for key, value in metadata.items():
            template = template.replace("{{" + key + "}}", str(value))
        return template

    header   = _sub(header_template or "")
    approval = _sub(KB_APPROVAL_TABLE)
    footer   = _sub(footer_template or "")

    parts = []
    if header.strip():
        parts.append(header.strip())
    if approval.strip():
        parts.append(approval.strip())
    parts.append(body.strip())
    if footer.strip():
        parts.append(footer.strip())
    return "\n\n".join(parts)


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

# _invoke_with_retries and _llm_from_env removed — using _invoke_bedrock_direct() instead


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

    text = await asyncio.to_thread(_invoke_bedrock_direct, FORMATTER_SYSTEM_PROMPT, user_prompt)
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

    text = await asyncio.to_thread(_invoke_bedrock_direct, FORMATTER_SYSTEM_PROMPT, user_prompt)
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