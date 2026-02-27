"""
QA Agent - Module X (Option B: client-side tool execution)

Performs quality assurance review of the formatted SOP document.

GRAPH INTEGRATION PATTERN:
  - The graph passes a plain string containing 'workflow_id::<id>'.
  - STATE_STORE holds SOPState keyed by workflow_id.
  - This module exposes:
      * async @tool run_qa(prompt: str) -> str         (does the real work)
      * async run_qa_node(prompt: str, use_llama_dispatch: bool=False) -> str
  - In the graph, wrap run_qa_node with LocalNodeAgent (see sop_workflow.py).

We do NOT rely on Bedrock server-side tool use. Tool decisions & execution are
done client-side. Optionally, a LLaMA JSON "function-call" hop is supported,
but still dispatched locally.
"""

import os
import re
import json
import logging
import asyncio
from typing import Any, Dict, Optional, List

import boto3
from strands import tool

from src.graph.state_schema import SOPState, QAResult, WorkflowStatus
from src.graph.state_store import STATE_STORE

# --- Import centralized system prompt (adjust path if your file lives elsewhere) ---
try:
    from src.prompts.system_prompts import QA_SYSTEM_PROMPT  # preferred path
except Exception:
    # Fallback for older layout where the file lived under agents/
    from src.agents.systems_prompt import QA_SYSTEM_PROMPT  # type: ignore

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")
# How much document text to include in the QA prompt (token control)
_MAX_DOC_CHARS = int(os.getenv("QA_MAX_DOC_CHARS", "6000"))


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
    Call Bedrock Converse API synchronously and extract returned text.
    This is blocking and should be invoked via asyncio.to_thread by async code.
    Raises on error so callers see the real exception.
    """
    logger.debug("=== BEDROCK CALL (QA) ===")
    logger.debug("Model: %s | Region: %s | max_tokens=%s", model_id, _REGION, max_tokens)
    logger.debug("System prompt len: %d chars", len(system_prompt))
    logger.debug("User prompt (first 400 chars):\n%s", (user_prompt or "")[:400])

    client = boto3.client("bedrock-runtime", region_name=_REGION)
    request_body = {
        "modelId": model_id,
        "system": [{"text": system_prompt}],
        "messages": [{"role": "user", "content": [{"text": user_prompt}]}],
        "inferenceConfig": {"maxTokens": max_tokens},
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
    Async wrapper that offloads the blocking boto3 call to a thread to avoid
    blocking the event loop.
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


def _find_json_objects(text: str) -> List[dict]:
    """
    Find JSON objects in text by brace balancing and parse those that are valid dicts.
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
    Optional Mode: Return the first object that looks like:
      {"type":"function","name":"run_qa","parameters": {...}}
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
    Strip code fences and parse JSON. Raises on failure.
    """
    t = _strip_code_fences(text)
    logger.debug("Parsing JSON (%d chars):\n%s", len(t), t[:800])
    return json.loads(t)


# -----------------------------------------------------------------------------
# Graph-level tool — does the ACTUAL QA and writes to STATE_STORE
# -----------------------------------------------------------------------------
@tool
async def run_qa(prompt: str) -> str:
    """
    Execute the SOP quality assurance review step.

    Reads the SOPState identified by the workflow_id embedded in the prompt,
    reviews the formatted document, saves the QAResult to STATE_STORE, and
    returns a summary string for the conditional edge / end of graph.

    Args:
        prompt: The graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_qa called | prompt: %s", (prompt or "")[:160])

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
        if not getattr(state, "formatted_document", None):
            raise ValueError("No formatted document available for QA review")

        # Prepare the document sample to control token usage
        doc = state.formatted_document or ""
        doc_sample = doc if len(doc) <= _MAX_DOC_CHARS else (doc[:_MAX_DOC_CHARS] + "...")

        # Use centralized system prompt
        system_prompt = QA_SYSTEM_PROMPT

        user_prompt = (
            f"QA REVIEW TASK:\n"
            f"- Topic: {state.topic}\n"
            f"- Industry: {state.industry}\n\n"
            f"DOCUMENT SAMPLE (truncated if necessary):\n{doc_sample}\n"
        )

        # Call LLM to produce JSON (small retry loop for resiliency)
        model_id = _get_model_id("MODEL_QA")
        last_err: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                raw_text = await _call_bedrock_async(
                    model_id, system_prompt, user_prompt, max_tokens=2048
                )
                break
            except Exception as e:
                last_err = e
                logger.warning("QA Bedrock call failed (attempt %d/3): %s", attempt, e)
                if attempt < 3:
                    await asyncio.sleep(0.75 * attempt)
        else:
            raise last_err or RuntimeError("Unknown Bedrock error during QA")

        qa_data = _parse_json_response(raw_text)

        # Validate & persist to state
        qa_result = QAResult(**qa_data)
        state.qa_result = qa_result
        state.status = WorkflowStatus.QA_COMPLETE
        state.current_node = "qa"
        if hasattr(state, "increment_tokens"):
            state.increment_tokens(1500)

        verdict = "APPROVED" if getattr(qa_result, "approved", False) else "NEEDS REVISION"
        score_val = float(getattr(qa_result, "score", 0.0) or 0.0)
        logger.info("QA complete — score=%.1f %s | workflow_id=%s", score_val, verdict, workflow_id)

        return (
            f"workflow_id::{workflow_id} | "
            f"QA complete: score={score_val:.1f}/10 — {verdict}"
        )

    except Exception as e:
        logger.exception("QA review FAILED for workflow_id=%s", workflow_id)
        # Provide a structured fallback QAResult to keep graph logic consistent
        try:
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
        except Exception:
            # If QAResult construction fails for any reason, ensure qa_result at least exists
            state.qa_result = None
        if hasattr(state, "add_error"):
            state.add_error(f"QA review failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | QA FAILED: {e}"


# -----------------------------------------------------------------------------
# Node entry point for Graph (client-side execution) — ASYNC WRAPPER
# -----------------------------------------------------------------------------
async def run_qa_node(
    prompt: str,
    *,
    use_llama_dispatch: bool = False
) -> str:
    """
    Entry point for the QA node under Option B. (ASYNC)

    Default (use_llama_dispatch=False):
      - Directly execute the local async tool `run_qa` (recommended).
        Avoids an extra LLM hop and is deterministic.

    Optional (use_llama_dispatch=True):
      - Ask LLaMA to return a single function-call JSON:
          {"type":"function","name":"run_qa","parameters":{"prompt":"..."}}
        Parse it locally and dispatch to the local tool. Still client-side.

    Returns:
      The tool result string to pass to the next node.
    """
    logger.info(">>> run_qa_node | use_llama_dispatch=%s", use_llama_dispatch)

    if not use_llama_dispatch:
        # Execute the local async tool (await)
        return await run_qa(prompt=prompt)

    # --- Optional LLaMA-dispatch path (parity with other nodes) ---
    model_id = _get_model_id("MODEL_QA_NODE")
    system_prompt = (
        "You are the quality assurance node in an SOP generation pipeline.\n"
        "Return ONLY a single JSON object with this exact shape:\n"
        '{"type":"function","name":"run_qa","parameters":{"prompt":"<string>"}}\n'
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
    if tool_call.get("name") != "run_qa":
        raise RuntimeError(
            f"Model requested tool '{tool_call.get('name')}', expected 'run_qa'."
        )
    params = tool_call.get("parameters") or {}
    if "prompt" not in params:
        raise RuntimeError("Tool call missing required 'parameters.prompt'.")

    return await run_qa(**params)


# -----------------------------------------------------------------------------
# NOTE:
# We intentionally do NOT export a `qa_agent = Agent(...)` here.
# Under Option B, your graph should wrap `run_qa_node` with LocalNodeAgent:
#
#   from src.agents.qa_agent import run_qa_node
#   qa_node = LocalNodeAgent("qa", lambda p: run_qa_node(p, use_llama_dispatch=False))
#   gb.add_node(qa_node, "qa")
# -----------------------------------------------------------------------------