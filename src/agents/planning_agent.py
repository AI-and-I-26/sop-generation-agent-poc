"""
Planning Agent - Module 4, Section 4.2

ARCHITECTURE CHANGE (Option B - client-side tool execution):
  - Do NOT rely on Bedrock/Converse server-side tool use.
  - The planning *node* triggers the local Python tool directly (or, optionally,
    asks LLaMA to return a JSON function-call string that we parse & dispatch locally).
  - The local tool `run_planning` performs the actual planning work and writes to STATE_STORE.

DEBUG LOGGING:
  Set LOG_LEVEL=DEBUG in your environment or add this to your entry point:
      import logging
      logging.basicConfig(level=logging.DEBUG)
  You will then see exactly what is sent to Bedrock and what comes back.
"""

import os
import re
import json
import logging
import asyncio
from typing import Any, Dict, Optional, List

import boto3  # AWS SDK for Python — used to call Bedrock's Converse API

# `tool` decorator is optional now, but we keep it for compatibility with your tooling.
# It typically marks callables as graph tools for dispatch in your orchestration layer.
from strands import tool

# --- State types and centralized state store (your app domain) ---
from src.graph.state_schema import (
    SOPState,
    SOPOutline,
    OutlineSubsection,  # used by normalizer
    WorkflowStatus,
)
from src.graph.state_store import STATE_STORE

# --- Import centralized system prompt (configurable, defaults to KB v5.0 module) ---
import hashlib
from importlib import import_module

PROMPTS_MODULE = os.getenv("PROMPTS_MODULE", "src.prompts.system_prompts")  # point to your v5.0 file
prompts = import_module(PROMPTS_MODULE)
PLANNING_SYSTEM_PROMPT = prompts.PLANNING_SYSTEM_PROMPT

def _fp(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

# Module-level logger; respects logging.basicConfig / LOG_LEVEL env in the app entry point
logger = logging.getLogger(__name__)
logger.info("Planning prompt module=%s fp=%s", PROMPTS_MODULE, _fp(PLANNING_SYSTEM_PROMPT))

# Default LLM model ARN for Bedrock (Meta Llama 3.3 70B instruct profile)
# Can be overridden via environment variables — see _get_model_id.
_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)

# AWS region for Bedrock runtime client. Override with AWS_REGION if needed.
_REGION = os.getenv("AWS_REGION", "us-east-2")


# -----------------------------------------------------------------------------
# Bedrock low-level helpers
# -----------------------------------------------------------------------------
def _get_model_id(env_var: str) -> str:
    """
    Resolve the model ARN for a given env var key with a sensible fallback.

    Priority:
      1) Environment variable named by `env_var` (e.g., MODEL_PLANNING / MODEL_PLANNING_NODE)
      2) Module default `_DEFAULT_MODEL_ID`

    This allows you to switch model profiles per node by simply setting env vars.
    """
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _call_bedrock_sync(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """
    Synchronous Bedrock Converse API call.
    - Builds a converse() payload with a system prompt and a user message.
    - Returns the concatenated text from returned content parts.
    - Raises ValueError if the response has no usable text.
    """
    logger.debug("=== BEDROCK CALL (Planning) ===")
    logger.debug("Model: %s", model_id)
    logger.debug("Region: %s", _REGION)
    logger.debug("System prompt length: %d chars", len(system_prompt))
    logger.debug("User prompt (first 400 chars):\n%s", (user_prompt or "")[:400])

    client = boto3.client("bedrock-runtime", region_name=_REGION)

    request_body = {
        "modelId": model_id,
        "system": [{"text": system_prompt}],
        "messages": [{"role": "user", "content": [{"text": user_prompt}]}],
        "inferenceConfig": {
            "maxTokens": 2048,
            # temperature/topP/topK can be configured here if needed
        },
    }

    response = client.converse(**request_body)
    logger.debug("Raw Bedrock response: %s", json.dumps(response, default=str))

    output = response.get("output", {})
    message = output.get("message", {})
    content = message.get("content", [])

    if not content:
        raise ValueError(f"Bedrock returned empty content. Full response: {response}")

    text_parts = [part.get("text", "") for part in content if "text" in part]
    text = "\n".join(tp for tp in text_parts if tp).strip()
    logger.debug("Extracted text (%d chars)", len(text))

    if not text:
        raise ValueError(f"Bedrock returned blank text. Full response: {response}")

    return text


async def _call_bedrock_async(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """
    Async wrapper for the Bedrock call (offloads sync client to a worker thread).
    """
    return await asyncio.to_thread(_call_bedrock_sync, model_id, system_prompt, user_prompt)


def _strip_code_fences(text: str) -> str:
    """
    Remove basic Markdown code fences from an LLM response prior to JSON parsing.
    """
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


def _find_json_objects(text: str) -> List[dict]:
    """
    Attempt to extract *embedded* JSON objects from free-form text by brace balancing.
    """
    objs: List[dict] = []
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


def _parse_json_response(text: str) -> dict:
    """
    Returns the first JSON object that contains 'sections'.
    Strips code fences, then tries direct parse, then scans for brace-balanced objects.
    """
    text = _strip_code_fences(text)
    logger.debug("Parsing JSON (first 800 chars):\n%s", text[:800])

    # 1) Try direct parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and "sections" in obj:
            return obj
    except Exception:
        pass

    # 2) Fallback: scan and pick the object that has 'sections'
    for obj in _find_json_objects(text):
        if isinstance(obj, dict) and "sections" in obj:
            return obj

    raise ValueError("Could not find a valid planning JSON object containing 'sections'.")


# -----------------------------------------------------------------------------
# Missing helpers (fixes NameError) + function-call parsing for optional wrapper
# -----------------------------------------------------------------------------
def _extract_workflow_id_from_prompt(prompt: str) -> Optional[str]:
    """
    Extract the workflow id from a graph prompt with the convention:
        "workflow_id::<id> | <rest of message>"
    Returns the id string or None if not present.
    """
    m = re.search(r"workflow_id::([^\s\|]+)", prompt or "")
    return m.group(1) if m else None


def _extract_tool_call_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse the first object that looks like a function-call JSON in this shape:
      {
        "type": "function",
        "name": "run_planning",
        "parameters": {"prompt": "<string>"}
      }
    """
    if not text:
        return None

    cleaned = _strip_code_fences(text)

    # 1) Try direct JSON parse
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict) and obj.get("type") == "function" and "name" in obj:
            return obj
    except Exception:
        pass

    # 2) Fallback: scan embedded objects
    for obj in _find_json_objects(cleaned):
        if obj.get("type") == "function" and "name" in obj:
            return obj

    return None


# -----------------------------------------------------------------------------
# Outline guardrails (KB contract)
# -----------------------------------------------------------------------------
def _preflight_outline(outline: SOPOutline) -> None:
    """
    Ensures the outline matches the KB structure before saving to state.
    - 8 top-level sections with exact numbers (1.0..8.0)
    - 6.1 General and 6.2 Overview exist
    - 7.0 has only 7.1 category (7.1.x docs will be rendered later)
    """
    required = [
        ("1.0", "PURPOSE"),
        ("2.0", "SCOPE"),
        ("3.0", "RESPONSIBILITIES"),
        ("4.0", "DEFINITIONS / ABBREVIATIONS"),
        ("5.0", "MATERIALS"),
        ("6.0", "PROCEDURE"),
        ("7.0", "REFERENCES"),
        ("8.0", "REVISION HISTORY"),
    ]
    if len(outline.sections) != 8:
        raise ValueError(f"Expected 8 top-level sections; got {len(outline.sections)}")

    req_map = {n: t for n, t in required}
    for s in outline.sections:
        if s.number not in req_map:
            raise ValueError(f"Unexpected top-level section number: {s.number}")
        # Normalize title exactly to KB (avoid downstream title-case drift)
        s.title = req_map[s.number]

    # Check 6.1 / 6.2
    proc = next((s for s in outline.sections if s.number == "6.0"), None)
    nums = {ss.number for ss in (proc.subsections if proc else [])}
    for must in ("6.1", "6.2"):
        if must not in nums:
            raise ValueError(f"Missing required procedure subsection: {must}")

    # Check 7.0 has only 7.1 category
    refs = next((s for s in outline.sections if s.number == "7.0"), None)
    if refs and len(refs.subsections) > 1:
        raise ValueError("REFERENCES (7.0) should contain only 7.1 category (7.1.x docs rendered later).")


def _ban_placeholders(outline: SOPOutline) -> None:
    """
    Blocks literal '<...>' / '&lt;...&gt;' from leaking into state (common LLM artifact).
    """
    def _has_placeholder(txt: Optional[str]) -> bool:
        if not isinstance(txt, str):
            return False
        l = txt.lower()
        return ("<" in l and ">" in l) or ("&lt;" in l or "&gt;" in l)

    if _has_placeholder(outline.title) or _has_placeholder(outline.industry) or _has_placeholder(outline.audience or ""):
        raise ValueError("Outline contains placeholder brackets in header fields.")

    for s in outline.sections:
        if _has_placeholder(s.title):
            raise ValueError(f"Placeholder detected in section title: {s.number} {s.title}")


def _normalize_outline(outline: SOPOutline) -> SOPOutline:
    """
    Optional normalizer: ensures exact titles & required subsections exist.
    Use _preflight_outline to *enforce*; use this to *coerce* minor drift.
    """
    required = {
        "1.0": "PURPOSE",
        "2.0": "SCOPE",
        "3.0": "RESPONSIBILITIES",
        "4.0": "DEFINITIONS / ABBREVIATIONS",
        "5.0": "MATERIALS",
        "6.0": "PROCEDURE",
        "7.0": "REFERENCES",
        "8.0": "REVISION HISTORY",
    }
    for s in outline.sections:
        if s.number in required:
            s.title = required[s.number]

    # Ensure 6.1/6.2 exist
    proc = next((s for s in outline.sections if s.number == "6.0"), None)
    if proc:
        have = {ss.number: ss for ss in proc.subsections}
        for num, title in (("6.1", "General"), ("6.2", "Overview")):
            if num not in have:
                proc.subsections.insert(0, OutlineSubsection(number=num, title=title, subsections=[]))
            else:
                have[num].title = title

    # Squash extra categories under 7.0 (keep first as 7.1 "SOPs")
    refs = next((s for s in outline.sections if s.number == "7.0"), None)
    if refs and len(refs.subsections) > 1:
        refs.subsections = refs.subsections[:1]
        refs.subsections[0].title = "SOPs"

    return outline


# -----------------------------------------------------------------------------
# Graph-level tool implementation
# -----------------------------------------------------------------------------
@tool
async def run_planning(prompt: str) -> str:
    """
    Execute the SOP planning step (does the ACTUAL work and writes to STATE_STORE).

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.

    Flow:
      1) Extract workflow_id from the incoming graph message.
      2) Fetch current SOPState from STATE_STORE. Fail fast if missing (wiring issue).
      3) Build the system+user prompts and call Bedrock (async wrapped).
      4) Retry transient Bedrock errors (3 attempts with small backoff).
      5) Parse LLM JSON into SOPOutline; normalize -> preflight -> placeholder-ban; save to state.
      6) Flip state.status to PLANNED, set `current_node = "planning"`, account tokens.
      7) Return a compact success string including workflow_id and section count.
    """
    logger.info(">>> run_planning called | prompt: %s", (prompt or "")[:160])

    # Extract the workflow identifier from the graph message
    workflow_id = _extract_workflow_id_from_prompt(prompt or "") or ""
    logger.debug("Extracted workflow_id: '%s'", workflow_id)

    if not workflow_id:
        raise ValueError("Missing workflow_id in prompt; expected 'workflow_id::<id>' within the message content.")

    # Retrieve the current working state for this workflow/run
    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = f"ERROR: no state found for workflow_id='{workflow_id}' | store keys: {list(STATE_STORE.keys())}"
        logger.error(msg)
        return msg

    logger.info("State found | topic='%s' industry='%s'", state.topic, state.industry)

    try:
        # Allow per-node model override with env var MODEL_PLANNING; else use default
        model_id = _get_model_id("MODEL_PLANNING")
        logger.info("Using model for planning: %s", model_id)

        # Prompts
        system_prompt = PLANNING_SYSTEM_PROMPT

        # Avoid dangling "Additional Requirements:" when none are provided
        reqs = ", ".join(state.requirements or [])
        user_prompt = (
            "Create a detailed SOP outline for:\n"
            f"Topic: {state.topic}\n"
            f"Industry: {state.industry}\n"
            f"Target Audience: {state.target_audience}\n"
            + (f"Additional Requirements: {reqs}" if reqs else "")
        )

        # Simple retry loop to mitigate transient network/service hiccups.
        last_err: Optional[Exception] = None
        for attempt in range(1, 4):  # up to 3 attempts
            try:
                raw_text = await _call_bedrock_async(model_id, system_prompt, user_prompt)
                break  # success on first good call
            except Exception as e:
                last_err = e
                logger.warning("Bedrock call failed (attempt %d/3): %s", attempt, e)
                if attempt < 3:
                    await asyncio.sleep(0.75 * attempt)
        else:
            raise last_err or RuntimeError("Unknown Bedrock error during planning")

        # Parse model output into dictionary (find the object with 'sections')
        outline_data = _parse_json_response(raw_text)

        if not isinstance(outline_data, dict) or "sections" not in outline_data:
            raise ValueError("Planning JSON missing required key 'sections'.")

        # Cast/validate via your dataclass (will raise if the shape doesn't match)
        outline = SOPOutline(**outline_data)

        # Optional: if LLM didn't include audience in outline header, copy from state
        if getattr(outline, "audience", None) in (None, ""):
            outline.audience = state.target_audience

        # ✅ Normalize → Preflight → Placeholder-ban
        outline = _normalize_outline(outline)
        _preflight_outline(outline)
        _ban_placeholders(outline)

        # Persist updates to the shared state store
        state.outline = outline
        state.status = WorkflowStatus.PLANNED
        state.current_node = "planning"

        # Optional accounting (heuristic)
        if hasattr(state, "increment_tokens"):
            state.increment_tokens(1500)

        logger.info(
            "Planning complete — %d sections | workflow_id=%s",
            len(outline.sections or []), workflow_id
        )

        return (
            f"workflow_id::{workflow_id} | "
            f"Planning complete: {len(outline.sections or [])} sections for '{state.topic}'"
        )

    except Exception as e:
        # Fail-safe: mark state as FAILED and record the error detail for later QA/ops review
        logger.exception("Planning FAILED for workflow_id=%s", workflow_id)
        if hasattr(state, "add_error"):
            state.add_error(f"Planning failed: {str(e)}")
        # Clear any stale outline to prevent downstream confusion
        state.outline = None
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Planning FAILED: {e}"


# -----------------------------------------------------------------------------
# Node runner (client-side tool execution) — ASYNC WRAPPER
# -----------------------------------------------------------------------------
async def run_planning_node(
    prompt: str,
    *,
    use_llama_dispatch: bool = False,
) -> str:
    """
    Entry point for the PLANNING node under Option B. (ASYNC)

    Modes:
      - Default (use_llama_dispatch=False):
          Directly execute the local tool `run_planning(prompt=...)`.
      - Optional (use_llama_dispatch=True):
          Ask LLaMA to produce a *pure JSON function-call* string (no prose, no fences),
          parse it locally to a dict, validate the `name`, then dispatch to the local tool.
    """
    logger.info(">>> run_planning_node | use_llama_dispatch=%s", use_llama_dispatch)

    if not use_llama_dispatch:
        return await run_planning(prompt=prompt)

    # Optional: model-driven function call wrapper
    model_id = _get_model_id("MODEL_PLANNING_NODE")  # can reuse MODEL_PLANNING if preferred
    system_prompt = (
        "You are the planning node in an SOP generation pipeline.\n"
        "Return ONLY a single JSON object with this exact shape:\n"
        '{"type":"function","name":"run_planning","parameters":{"prompt":"<string>"}}\n'
        "Do NOT include any surrounding text, markdown, code fences, or commentary."
    )

    user_prompt = prompt
    raw = await _call_bedrock_async(model_id, system_prompt, user_prompt)
    tool_call = _extract_tool_call_from_text(raw)
    if not tool_call:
        raise RuntimeError(
            "Model did not return a parseable tool call JSON. "
            f"Got: {raw[:500]}..."
        )

    if tool_call.get("name") != "run_planning":
        raise RuntimeError(
            f"Model requested tool '{tool_call.get('name')}', expected 'run_planning'."
        )

    params = tool_call.get("parameters") or {}
    if "prompt" not in params:
        raise RuntimeError("Tool call missing required 'parameters.prompt'.")

    return await run_planning(**params)