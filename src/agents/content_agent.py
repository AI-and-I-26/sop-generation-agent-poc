"""
Content Agent - Module 6, Section 6.1 (Option B: client-side tool execution)

Generates detailed SOP content per outline section.

GRAPH INTEGRATION PATTERN:
  - The graph sends a plain string that includes 'workflow_id::<id>'.
  - STATE_STORE holds SOPState keyed by workflow_id (same as planning/research).
  - This module exposes:
      * async @tool run_content(prompt: str) -> str   (does the real work)
      * async run_content_node(prompt: str, use_llama_dispatch: bool=False) -> str
  - The graph should call run_content_node(prompt, use_llama_dispatch=False)
    via the LocalNodeAgent wrapper (see sop_workflow.py).

We do NOT rely on Bedrock server-side tool use. All tool decisions and execution
happen client-side. Optionally, you can enable a LLaMA JSON "function-call" hop
with use_llama_dispatch=True (still client-side dispatch).
"""

import os
import re
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional

import boto3
from strands import tool

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE

# --- Import centralized system prompt (adjust path if your file lives elsewhere) ---
try:
    from src.prompts.system_prompts import CONTENT_SYSTEM_PROMPT  # preferred path
except Exception:
    # Fallback for older layout where the file lived under agents/
    from src.agents.systems_prompt import CONTENT_SYSTEM_PROMPT  # type: ignore

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")
# Limit how many sections to generate in one pass to control cost/latency
_MAX_SECTIONS = int(os.getenv("MAX_CONTENT_SECTIONS", "5"))


# -----------------------------------------------------------------------------
# Robust JSON extraction & lenient parsing helpers (same treatment as research)
# -----------------------------------------------------------------------------
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
_TRAILING_COMMA_RE = re.compile(r",\s*(?=[}\]])")

def _extract_first_braced_object(s: str) -> str:
    """Return the first balanced {...} object found in the text, else ''. """
    if not s:
        return ""
    depth = 0
    start = -1
    for i, ch in enumerate(s):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start != -1:
                    return s[start:i+1]
    return ""

def _extract_json_block(text: str) -> str:
    """
    Try in order:
      1) ```json ... ```
      2) generic ``` ... ```
      3) the first balanced { ... } object from prose
    Return '' if nothing found.
    """
    if not text:
        return ""

    # 1) explicit fenced ```json
    m = _JSON_FENCE_RE.search(text)
    if m:
        return m.group(1).strip()

    # 2) any fenced block
    fence = re.search(r"```([\s\S]*?)```", text)
    if fence:
        inner = fence.group(1).strip()
        if inner.lower().startswith("json"):
            inner = inner[4:].strip()
        cand = _extract_first_braced_object(inner)
        if cand:
            return cand.strip()

    # 3) first balanced object from raw text
    cand = _extract_first_braced_object(text)
    return cand.strip()

def _escape_ctrl_in_strings(s: str) -> str:
    """
    Escape raw control chars inside double-quoted strings:
    \n -> \\n, \r -> \\r, \t -> \\t
    """
    out = []
    in_str = False
    esc = False
    for ch in s:
        if in_str:
            if esc:
                out.append(ch)
                esc = False
            else:
                if ch == "\\":
                    out.append(ch)
                    esc = True
                elif ch == "\"":
                    out.append(ch)
                    in_str = False
                elif ch == "\n":
                    out.append("\\n")
                elif ch == "\r":
                    out.append("\\r")
                elif ch == "\t":
                    out.append("\\t")
                else:
                    out.append(ch)
        else:
            out.append(ch)
            if ch == "\"":
                in_str = True
    return "".join(out)

def _remove_trailing_commas(s: str) -> str:
    """Remove trailing commas in object/array:  {"a":1,} -> {"a":1}, [1,2,] -> [1,2]"""
    return _TRAILING_COMMA_RE.sub("", s)

def _loads_lenient(text: str) -> dict:
    """
    Try strict json.loads first; on failure:
      - escape control chars in strings
      - remove trailing commas
    Then try again.
    """
    if not text:
        raise json.JSONDecodeError("empty", "", 0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fixed = _escape_ctrl_in_strings(text)
        fixed = _remove_trailing_commas(fixed)
        return json.loads(fixed)


# -----------------------------------------------------------------------------
# Bedrock (Converse) helpers — Option B uses Converse ONLY for text generation
# -----------------------------------------------------------------------------
def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _call_bedrock_sync(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 2048,
) -> str:
    """
    Synchronous Bedrock Converse API call.
    Returns the raw text response string or raises on error.
    Intended to be called via asyncio.to_thread from async code.
    """
    logger.debug("=== BEDROCK CALL (Content) ===")
    logger.debug("Model: %s | Region: %s | max_tokens=%s", model_id, _REGION, max_tokens)
    logger.debug("System prompt len: %d chars", len(system_prompt))
    logger.debug("User prompt (first 400 chars):\n%s", (user_prompt or "")[:400])

    client = boto3.client("bedrock-runtime", region_name=_REGION)
    request_body = {
        "modelId": model_id,
        "system": [{"text": system_prompt}],
        "messages": [{"role": "user", "content": [{"text": user_prompt}]}],
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0},
    }

    # NOTE: Do not set responseFormat here; some SDK/model combos reject it.
    response = client.converse(**request_body)
    logger.debug("Raw Bedrock response: %s", json.dumps(response, default=str))

    output = response.get("output", {})
    message = output.get("message", {})
    content = message.get("content", [])
    if not content:
        raise ValueError(f"Bedrock returned empty content. Full response: {response}")

    text_parts = [part.get("text", "") for part in content if "text" in part]
    text = "\n".join(tp for tp in text_parts if tp).strip()
    logger.debug("Extracted text (%d chars):\n%s", len(text), text[:800])
    if not text:
        raise ValueError(f"Bedrock returned blank text. Full response: {response}")

    return text


async def _call_bedrock_async(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 2048,
) -> str:
    """
    Async wrapper to run the blocking boto3 call in a thread, keeping the event loop responsive.
    """
    return await asyncio.to_thread(
        _call_bedrock_sync, model_id, system_prompt, user_prompt, max_tokens=max_tokens
    )


def _strip_code_fences(text: str) -> str:
    """Remove ```...``` or ```json ... ``` fences if present."""
    if not text:
        return text
    t = text.strip()
    if t.startswith("```"):
        parts = t.split("```")
        candidates = [p.strip() for p in parts if "{" in p and "}" in p]
        if candidates:
            cleaned = candidates[0]
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
            return cleaned
    return t


def _find_json_objects(text: str) -> List[Dict[str, Any]]:
    """
    Find JSON objects in text by brace balancing and parse those that are valid dicts.
    """
    objs: List[Dict[str, Any]] = []
    s = text or ""
    n = len(s)
    i = 0
    while i < n:
        if s[i] == "{":
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                j += 1
            if depth == 0:
                candidate = s[i:j]
                try:
                    obj = json.loads(candidate)
                    if isinstance(obj, dict):
                        objs.append(obj)
                except Exception:
                    pass
                i = j
                continue
        i += 1
    return objs


def _extract_tool_call_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Optional Mode: Return the first object that looks like:
      {"type":"function","name":"run_content","parameters": {...}}
    """
    if not text:
        return None
    cleaned = _strip_code_fences(text)
    # First try entire content
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict) and obj.get("type") == "function" and "name" in obj:
            return obj
    except Exception:
        pass
    # Then scan for embedded objects
    for obj in _find_json_objects(cleaned):
        if obj.get("type") == "function" and "name" in obj:
            return obj
    return None


def _extract_workflow_id_from_prompt(prompt: str) -> Optional[str]:
    m = re.search(r"workflow_id::([^\s\|]+)", prompt or "")
    return m.group(1) if m else None


def _parse_json_response(text: str) -> dict:
    """
    Legacy parser: strip code fences and parse JSON. (Kept for fallback)
    """
    t = _strip_code_fences(text)
    logger.debug("Parsing JSON (%d chars):\n%s", len(t), t[:800])
    return json.loads(t)


def _truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else (s[: max_len - 3] + "...")


# -----------------------------------------------------------------------------
# Graph-level tool — does the ACTUAL content generation and writes to STATE_STORE
# -----------------------------------------------------------------------------
@tool
async def run_content(prompt: str) -> str:
    """
    Execute the SOP content generation step.

    Reads the SOPState identified by the workflow_id embedded in the prompt,
    generates detailed content for each outline section (up to MAX_CONTENT_SECTIONS),
    saves results to STATE_STORE, and returns a summary string for the next graph node.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_content called | prompt: %s", (prompt or "")[:160])

    workflow_id = _extract_workflow_id_from_prompt(prompt or "") or ""
    logger.debug("Extracted workflow_id: '%s'", workflow_id)

    # Fail fast if workflow_id is missing (helps catch graph prompt wiring issues)
    if not workflow_id:
        raise ValueError(
            "Missing workflow_id in prompt; expected 'workflow_id::<id>' within the message content."
        )

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = f"ERROR: no state found for workflow_id='{workflow_id}' | store keys: {list(STATE_STORE.keys())}"
        logger.error(msg)
        return msg

    if not getattr(state, "outline", None) or not getattr(state.outline, "sections", None):
        err = "No outline available for content generation"
        logger.error(err)
        if hasattr(state, "add_error"):
            state.add_error(err)
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Content FAILED: {err}"

    try:
        # Extract research context if available (be robust if it's a pydantic model/dataclass)
        research_data: Dict[str, Any] = {}
        if getattr(state, "research", None) is not None:
            if hasattr(state.research, "dict"):
                research_data = state.research.dict()
            elif hasattr(state.research, "__dict__"):
                research_data = dict(state.research.__dict__)
            else:
                # As a fallback, attempt json roundtrip if it’s a pydantic-like object
                try:
                    research_data = json.loads(json.dumps(state.research))
                except Exception:
                    research_data = {}

        best_practices: List[str] = research_data.get("best_practices") or []
        compliance: List[str] = research_data.get("compliance_requirements") or []

        # Use centralized system prompt
        system_prompt = CONTENT_SYSTEM_PROMPT

        model_id = _get_model_id("MODEL_CONTENT")
        max_sections = max(1, _MAX_SECTIONS)
        generated = 0
        content_sections: Dict[str, str] = {}

        # Iterate the outline and generate up to max_sections
        for idx, section in enumerate(state.outline.sections or []):
            if generated >= max_sections:
                break

            section_title = getattr(section, "title", f"Section {idx+1}") or f"Section {idx+1}"
            # Compose prompt with research context if any
            user_prompt = (
                f"Write detailed SOP content for this section.\n"
                f"Section: {section_title}\n"
                f"Topic: {state.topic}\n"
                f"Industry: {state.industry}\n"
                f"Target Audience: {state.target_audience}\n\n"
                f"Relevant Information:\n"
                f"- Best Practices: {', '.join(best_practices) if best_practices else 'None'}\n"
                f"- Compliance: {', '.join(compliance) if compliance else 'None'}\n\n"
                f"Requirements:\n"
                f"1) Clear, numbered procedural steps\n"
                f"2) Include safety warnings when applicable (⚠️ WARNING: ...)\n"
                f"3) Add quality checkpoints (✓ CHECKPOINT: ...)\n"
                f"4) Provide time estimates per step and overall minutes field\n"
                f"5) Use specific measurements and quantities\n"
                f"Return ONLY valid JSON with the exact schema requested in the system prompt."
            )

            # Bedrock call with a small retry loop for resiliency
            last_err: Optional[Exception] = None
            raw_text: Optional[str] = None
            for attempt in range(1, 3 + 1):
                try:
                    raw_text = await _call_bedrock_async(
                        model_id, system_prompt, user_prompt, max_tokens=2048
                    )
                    break
                except Exception as e:
                    last_err = e
                    logger.warning(
                        "Content Bedrock call failed (section='%s', attempt %d/3): %s",
                        section_title, attempt, e
                    )
                    if attempt < 3:
                        await asyncio.sleep(0.75 * attempt)
            else:
                # All attempts failed for this section; skip and continue
                logger.warning("Skipping section '%s' due to Bedrock errors: %s", section_title, last_err)
                if hasattr(state, "add_error"):
                    state.add_error(f"Content section '{section_title}' failed: {last_err}")
                continue

            try:
                # --- Robust JSON extraction + lenient parsing (same as research) ---
                json_str = _extract_json_block(raw_text or "")
                if not json_str:
                    json_str = _strip_code_fences(raw_text or "")
                content_data = _loads_lenient(json_str)

                # Minimal schema sanity checks
                if "section_title" not in content_data or "content" not in content_data:
                    raise ValueError("Model response missing required keys 'section_title' or 'content'.")

                # Persist the content text; keep key by model section_title to preserve headings
                section_key = content_data.get("section_title") or section_title
                content_sections[section_key] = content_data["content"]

                # Token accounting (rough, feature-gated)
                if hasattr(state, "increment_tokens"):
                    state.increment_tokens(2500)
                generated += 1

                logger.info("Generated content for section: %s | workflow_id=%s", section_key, workflow_id)

            except Exception as e:
                logger.warning("Skipping section '%s' due to parse/generation error: %s", section_title, e)
                if hasattr(state, "add_error"):
                    state.add_error(f"Content section '{section_title}' failed: {e}")
                continue

        if not content_sections:
            raise ValueError("No valid content sections were generated.")

        # Merge with any prior partial content
        prev = getattr(state, "content_sections", None) or {}
        prev.update(content_sections)

        state.content_sections = prev
        state.status = WorkflowStatus.WRITTEN
        state.current_node = "content"

        logger.info("Content generation complete — %d sections | workflow_id=%s", len(content_sections), workflow_id)

        return (
            f"workflow_id::{workflow_id} | "
            f"Content complete: {len(content_sections)} sections written for '{state.topic}'"
        )

    except Exception as e:
        logger.exception("Content generation FAILED for workflow_id=%s", workflow_id)
        if hasattr(state, "add_error"):
            state.add_error(f"Content generation failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Content FAILED: {e}"


# -----------------------------------------------------------------------------
# Node entry point for Graph (client-side execution) — ASYNC WRAPPER
# -----------------------------------------------------------------------------
async def run_content_node(
    prompt: str,
    *,
    use_llama_dispatch: bool = False
) -> str:
    """
    Entry point for the CONTENT node under Option B. (ASYNC)

    Default (use_llama_dispatch=False):
      - Directly execute the local async tool `run_content` (recommended).
        This avoids an extra LLM hop and is deterministic.

    Optional (use_llama_dispatch=True):
      - Ask LLaMA to return a single function-call JSON:
          {"type":"function","name":"run_content","parameters":{"prompt":"<string>"}}
        Parse it locally and dispatch to the local tool. Still client-side.

    Returns:
      The tool result string to pass to the next node.
    """
    logger.info(">>> run_content_node | use_llama_dispatch=%s", use_llama_dispatch)

    if not use_llama_dispatch:
        # Execute the local async tool (await)
        return await run_content(prompt=prompt)

    # --- Optional LLaMA-dispatch path (parity with other nodes) ---
    model_id = _get_model_id("MODEL_CONTENT_NODE")
    system_prompt = (
        "You are the content node in an SOP generation pipeline.\n"
        "Return ONLY a single JSON object with this exact shape:\n"
        '{"type":"function","name":"run_content","parameters":{"prompt":"<string>"}}\n'
        "Do NOT include any surrounding text, markdown, code fences, or commentary."
    )
    user_prompt = prompt

    raw = await _call_bedrock_async(model_id, system_prompt, user_prompt, max_tokens=256)
    tool_call = _extract_tool_call_from_text(raw)
    if not tool_call:
        raise RuntimeError(
            "Model did not return a parseable tool call JSON. "
            f"Got: {raw[:500]}..."
        )
    if tool_call.get("name") != "run_content":
        raise RuntimeError(
            f"Model requested tool '{tool_call.get('name')}', expected 'run_content'."
        )
    params = tool_call.get("parameters") or {}
    if "prompt" not in params:
        raise RuntimeError("Tool call missing required 'parameters.prompt'.")

    return await run_content(**params)


# -----------------------------------------------------------------------------
# NOTE:
# We intentionally do NOT export a `content_agent = Agent(...)` here.
# Under Option B, your graph should wrap `run_content_node` with LocalNodeAgent:
#
#   content_node = LocalNodeAgent("content", lambda p: run_content_node(p, use_llama_dispatch=False))
#   gb.add_node(content_node, "content")
# -----------------------------------------------------------------------------