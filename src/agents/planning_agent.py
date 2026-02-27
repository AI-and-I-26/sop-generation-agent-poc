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

import boto3

# `tool` decorator is optional now, but we keep it for compatibility with your tooling.
from strands import tool

from src.graph.state_schema import SOPState, SOPOutline, WorkflowStatus
from src.graph.state_store import STATE_STORE

# --- Import centralized system prompt (adjust path if your file lives elsewhere) ---
try:
    from src.prompts.system_prompts import PLANNING_SYSTEM_PROMPT  # preferred path
except Exception:
    # Fallback for older layout where the file lived under agents/
    from src.agents.systems_prompt import PLANNING_SYSTEM_PROMPT  # type: ignore

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")


# -----------------------------------------------------------------------------
# Bedrock low-level helpers
# -----------------------------------------------------------------------------
def _get_model_id(env_var: str) -> str:
    """Resolve model ARN from env var or fall back to default."""
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _call_bedrock_sync(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """
    Synchronous Bedrock Converse API call.
    Returns the raw text response string or raises on error.
    Intended to be offloaded to a thread via asyncio.to_thread in async code.
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
        "inferenceConfig": {"maxTokens": 2048},
    }

    response = client.converse(**request_body)
    logger.debug("Raw Bedrock response: %s", json.dumps(response, default=str))

    # Extract text from response
    output = response.get("output", {})
    message = output.get("message", {})
    content = message.get("content", [])

    if not content:
        raise ValueError(f"Bedrock returned empty content. Full response: {response}")

    # LLaMA returns content parts with "text"
    text_parts = [part.get("text", "") for part in content if "text" in part]
    text = "\n".join(tp for tp in text_parts if tp).strip()
    logger.debug("Extracted text (%d chars)", len(text))

    if not text:
        raise ValueError(f"Bedrock returned blank text. Full response: {response}")

    return text


async def _call_bedrock_async(model_id: str, system_prompt: str, user_prompt: str) -> str:
    """
    Async wrapper for Bedrock call. Offloads the blocking boto3 client call to a thread
    so we don't block the event loop.
    """
    return await asyncio.to_thread(_call_bedrock_sync, model_id, system_prompt, user_prompt)


def _strip_code_fences(text: str) -> str:
    """Remove ```...``` or ```json ... ``` fences."""
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
    Scan `text` and attempt to extract JSON objects by brace balancing.
    Return a list of successfully parsed Python dict objects.
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


def _extract_tool_call_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Return the first object that looks like a tool call:
      {"type":"function","name":"run_planning","parameters": {...}}
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

    # 2) Scan for any JSON objects within the text
    for obj in _find_json_objects(cleaned):
        if obj.get("type") == "function" and "name" in obj:
            return obj

    return None


def _extract_workflow_id_from_prompt(prompt: str) -> Optional[str]:
    """
    Extract the workflow id from a prompt like:
      "workflow_id::sop-369... | Generate a Standard ..."
    """
    m = re.search(r"workflow_id::([^\s\|]+)", prompt or "")
    return m.group(1) if m else None


def _parse_json_response(text: str) -> dict:
    """Strip code fences and parse JSON. Raises json.JSONDecodeError on failure."""
    text = _strip_code_fences(text)
    logger.debug("Parsing JSON (first 800 chars):\n%s", text[:800])
    return json.loads(text)


# -----------------------------------------------------------------------------
# Graph-level tool implementation
# -----------------------------------------------------------------------------
@tool
async def run_planning(prompt: str) -> str:
    """Execute the SOP planning step (does the ACTUAL work and writes to STATE_STORE).

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_planning called | prompt: %s", (prompt or "")[:160])

    workflow_id = _extract_workflow_id_from_prompt(prompt or "") or ""
    logger.debug("Extracted workflow_id: '%s'", workflow_id)

    # Fail fast if workflow_id is missing (helps catch graph prompt wiring issues)
    if not workflow_id:
        raise ValueError(
            "Missing workflow_id in prompt; expected 'workflow_id::<id>' within the message content."
        )

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = (
            f"ERROR: no state found for workflow_id='{workflow_id}' | "
            f"store keys: {list(STATE_STORE.keys())}"
        )
        logger.error(msg)
        return msg

    logger.info("State found | topic='%s' industry='%s'", state.topic, state.industry)

    try:
        model_id = _get_model_id("MODEL_PLANNING")  # use env override if present
        logger.info("Using model for planning: %s", model_id)

        system_prompt = PLANNING_SYSTEM_PROMPT
        user_prompt = (
            f"Create a detailed SOP outline for:\n"
            f"Topic: {state.topic}\n"
            f"Industry: {state.industry}\n"
            f"Target Audience: {state.target_audience}\n"
            f"Additional Requirements: {', '.join(state.requirements or [])}"
        )

        # Optional: simple retry loop for transient Bedrock errors
        last_err: Optional[Exception] = None
        for attempt in range(1, 4):  # up to 3 attempts
            try:
                raw_text = await _call_bedrock_async(model_id, system_prompt, user_prompt)
                break
            except Exception as e:
                last_err = e
                logger.warning("Bedrock call failed (attempt %d/3): %s", attempt, e)
                if attempt < 3:
                    await asyncio.sleep(0.75 * attempt)
        else:
            # exhausted retries
            raise last_err or RuntimeError("Unknown Bedrock error during planning")

        outline_data = _parse_json_response(raw_text)

        # Minimal schema guardrails (let your model/dataclass enforce the rest)
        if not isinstance(outline_data, dict) or "sections" not in outline_data:
            raise ValueError("Planning JSON missing required key 'sections'.")

        outline = SOPOutline(**outline_data)

        # Persist to state
        state.outline = outline
        state.status = WorkflowStatus.PLANNED
        state.current_node = "planning"
        # Token increment is a rough accounting; adjust if you track exact tokens
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
        logger.exception("Planning FAILED for workflow_id=%s", workflow_id)
        if hasattr(state, "add_error"):
            state.add_error(f"Planning failed: {str(e)}")
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

    - Default (use_llama_dispatch=False): directly run the local tool `run_planning`.
      This avoids an extra LLM hop and is the simplest/most reliable form of
      client-side tool execution.

    - Optional (use_llama_dispatch=True): ask LLaMA to return a JSON function-call
      string, parse it locally, validate the tool name, and then dispatch to the
      local tool. This keeps parity with other nodes that might follow the same
      pattern but still avoids server-side tool use.

    Returns: The tool result string (used by the next graph node).
    """
    logger.info(">>> run_planning_node | use_llama_dispatch=%s", use_llama_dispatch)

    if not use_llama_dispatch:
        # Pure client-side tool exec (recommended): just call the local tool (await).
        return await run_planning(prompt=prompt)

    # --- Optional: LLaMA-driven function-call string, parsed client-side ---
    model_id = _get_model_id("MODEL_PLANNING_NODE")  # can reuse MODEL_PLANNING if you like
    system_prompt = (
        "You are the planning node in an SOP generation pipeline.\n"
        "Return ONLY a single JSON object with this exact shape:\n"
        '{"type":"function","name":"run_planning","parameters":{"prompt":"<string>"}}\n'
        "Do NOT include any surrounding text, markdown, code fences, or commentary."
    )

    # Here we pass the *graph message* (usually containing 'workflow_id::<id>') directly
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

    # Execute the local tool (async)
    return await run_planning(**params)


# -----------------------------------------------------------------------------
# NOTE: We intentionally do NOT create a `strands.Agent` here.
# Under Option B, graph code should call:
#   await run_planning_node(prompt, use_llama_dispatch=False)
# via an async-aware LocalNodeAgent that awaits coroutine handlers.
# -----------------------------------------------------------------------------