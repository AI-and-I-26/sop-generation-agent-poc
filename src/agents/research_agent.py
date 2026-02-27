"""
Research Agent - Module 5, Section 5.1 (Option B: client-side tool execution)

Performs research using RAG (Bedrock Knowledge Base) and other tools.

GRAPH INTEGRATION PATTERN:
  - The graph sends a plain string that includes 'workflow_id::<id>'.
  - We keep a module-level STATE_STORE keyed by workflow_id (same as planning).
  - This module exposes:
      * async @tool run_research(prompt: str) -> str   (does the real work)
      * async run_research_node(prompt: str, use_llama_dispatch: bool=False) -> str
  - The graph should call run_research_node(prompt, use_llama_dispatch=False)
    via the LocalNodeAgent wrapper (see sop_workflow.py refactor).

We do NOT rely on Bedrock server-side tool use. All tool decisions and execution
happen client-side. We optionally allow a LLaMA-driven "function-call JSON" string
that we parse and dispatch locally if use_llama_dispatch=True.
"""

import os
import re
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional

import boto3
from strands import tool

from src.graph.state_schema import SOPState, ResearchFindings, WorkflowStatus
from src.graph.state_store import STATE_STORE

# --- Import centralized system prompt (adjust path if your file lives elsewhere) ---
try:
    from src.prompts.system_prompts import RESEARCH_SYSTEM_PROMPT  # preferred path
except Exception:
    # Fallback for older layout where the file lived under agents/
    from src.agents.systems_prompt import RESEARCH_SYSTEM_PROMPT  # type: ignore

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")
_KB_REGION = os.getenv("AWS_REGION", "us-east-2")  # keep consistent by default
_KB_ID = os.getenv("KNOWLEDGE_BASE_ID", "1NR6BI4TNO")  # must be set for KB retrieval


# -----------------------------------------------------------------------------
# Robust JSON extraction & lenient parsing helpers
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
# LLM (Bedrock) helpers — Option B uses Converse ONLY for text generation
# -----------------------------------------------------------------------------
def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _call_bedrock_sync(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 2048
) -> str:
    """
    Call Bedrock Converse API synchronously and extract the returned text.
    This is blocking and should be called from a thread (see _call_bedrock_async).
    Raises on error so callers see the real exception.
    """
    logger.debug("=== BEDROCK CALL (Research) ===")
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

    # NOTE: Do not set responseFormat here; your SDK/model rejects it.
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
    max_tokens: int = 2048
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
      {"type":"function","name":"run_research","parameters": {...}}
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


# -----------------------------------------------------------------------------
# Domain helpers (sync by design; call via asyncio.to_thread from async context)
# -----------------------------------------------------------------------------
def _truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else (s[: max_len - 3] + "...")


def search_knowledge_base(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search Bedrock Knowledge Base for similar SOPs and procedures.
    Returns a Python list of {content, score, source}.
    """
    results: List[Dict[str, Any]] = []
    if not _KB_ID:
        logger.warning("KNOWLEDGE_BASE_ID is not set. Skipping KB retrieval.")
        return results

    try:
        kb_client = boto3.client("bedrock-agent-runtime", region_name=_KB_REGION)
        resp = kb_client.retrieve(
            knowledgeBaseId=_KB_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": max_results}
            },
        )
        for r in resp.get("retrievalResults", []):
            results.append({
                "content": r.get("content", {}).get("text", ""),
                "score": r.get("score", 0.0),
                "source": (
                    r.get("location", {})
                     .get("s3Location", {})
                     .get("uri", "Unknown")
                ),
            })
        return results
    except Exception as e:
        logger.error("KB search error: %s", e)
        return results


def get_compliance_requirements(industry: str, topic: str) -> List[str]:
    """
    Get compliance/regulatory requirements for an industry and topic.
    (Static baseline map — extend/replace with real compliance services as needed.)
    """
    compliance_map = {
        "Manufacturing": ["OSHA 1910", "ISO 9001"],
        "Healthcare": ["HIPAA", "FDA 21 CFR"],
        "Laboratory": ["CLIA", "CAP Standards"],
        "Energy": ["OSHA PSM 1910.119", "API RP 754"],
    }
    return compliance_map.get(industry, ["General Safety"])


# -----------------------------------------------------------------------------
# Graph-level tool — does the ACTUAL research and writes to STATE_STORE
# -----------------------------------------------------------------------------
@tool
async def run_research(prompt: str) -> str:
    """
    Execute the SOP research step.

    Reads the SOPState identified by the workflow_id embedded in the prompt,
    conducts research using Bedrock Knowledge Base and a compliance helper,
    synthesizes best practices via LLaMA (JSON-only), saves findings to STATE_STORE,
    and returns a summary string for the next graph node.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_research called | prompt: %s", (prompt or "")[:160])

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

    logger.info("State found | topic='%s' industry='%s'", state.topic, state.industry)

    try:
        # 1) Retrieve RAG context (KB) and compliance baseline (client-side)
        outline_hint = ""
        if getattr(state, "outline", None) and getattr(state.outline, "sections", None):
            first_titles = [s.title for s in (state.outline.sections or [])][:5]
            outline_hint = f"Outline sections hint: {', '.join(first_titles)}"

        kb_query = f"{state.topic} in {state.industry}. {outline_hint}".strip()
        # Offload KB retrieval to a thread to avoid blocking the event loop
        kb_docs: List[Dict[str, Any]] = await asyncio.to_thread(
            search_knowledge_base, kb_query, 5
        )
        compliance = get_compliance_requirements(state.industry, state.topic)

        # 2) Build a compact context for the LLM to synthesize into strict JSON
        kb_context_lines = []
        for i, doc in enumerate(kb_docs):
            content = _truncate(doc.get("content", ""), 700)
            score = doc.get("score", 0.0)
            source = doc.get("source", "Unknown")
            kb_context_lines.append(f"- [{i+1}] score={score:.3f} source={source}\n  {content}")

        kb_context = "\n".join(kb_context_lines)
        compliance_str = ", ".join(compliance)

        system_prompt = RESEARCH_SYSTEM_PROMPT

        user_prompt = (
            f"RESEARCH TASK:\n"
            f"- Topic: {state.topic}\n"
            f"- Industry: {state.industry}\n"
            f"- Target audience: {state.target_audience}\n"
            f"- Additional requirements: {', '.join(state.requirements or [])}\n\n"
            f"COMPLIANCE (baseline): {compliance_str}\n\n"
            f"KNOWLEDGE BASE EXTRACTS:\n{kb_context or '(no KB results)'}\n"
        )

        # 3) Call the LLM to produce JSON (small retry loop for resiliency)
        model_id = _get_model_id("MODEL_RESEARCH")
        last_err: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                raw_text = await _call_bedrock_async(model_id, system_prompt, user_prompt, max_tokens=2048)
                break
            except Exception as e:
                last_err = e
                logger.warning("Bedrock call failed (attempt %d/3): %s", attempt, e)
                if attempt < 3:
                    await asyncio.sleep(0.75 * attempt)
        else:
            raise last_err or RuntimeError("Unknown Bedrock error during research")

        # --- Robust JSON extraction + lenient parsing ---
        json_str = _extract_json_block(raw_text)
        if not json_str:
            # final fallback to previous behavior (strip leading code fence if any)
            json_str = _strip_code_fences(raw_text)
        findings_data = _loads_lenient(json_str)

        # 4) Validate & persist to state
        findings = ResearchFindings(**findings_data)
        state.research = findings
        state.status = WorkflowStatus.RESEARCHED
        state.current_node = "research"
        if hasattr(state, "increment_tokens"):
            state.increment_tokens(2000)  # rough accounting

        logger.info(
            "Research complete — similar_sops=%d | compliance=%d | workflow_id=%s",
            len(findings.similar_sops or []),
            len(findings.compliance_requirements or []),
            workflow_id,
        )

        return (
            f"workflow_id::{workflow_id} | "
            f"Research complete: {len(findings.similar_sops or [])} similar SOPs, "
            f"{len(findings.compliance_requirements or [])} compliance requirements"
        )

    except Exception as e:
        logger.exception("Research FAILED for workflow_id=%s", workflow_id)
        if hasattr(state, "add_error"):
            state.add_error(f"Research failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Research FAILED: {e}"


# -----------------------------------------------------------------------------
# Node entry point for Graph (client-side execution) — ASYNC WRAPPER
# -----------------------------------------------------------------------------
async def run_research_node(
    prompt: str,
    *,
    use_llama_dispatch: bool = False
) -> str:
    """
    Entry point for the RESEARCH node under Option B. (ASYNC)

    Default (use_llama_dispatch=False):
      - Directly execute the local tool `run_research` (recommended).
        This avoids an extra LLM hop and is deterministic.

    Optional (use_llama_dispatch=True):
      - Ask LLaMA to return a single function-call JSON:
          {"type":"function","name":"run_research","parameters":{"prompt":"..."}}
        Parse it locally and dispatch to the local tool. Still client-side.

    Returns:
      The tool result string to pass to the next node.
    """
    logger.info(">>> run_research_node | use_llama_dispatch=%s", use_llama_dispatch)

    if not use_llama_dispatch:
        # Execute the local async tool (await)
        return await run_research(prompt=prompt)

    # --- Optional LLaMA-dispatch path (kept for parity with planning) ---
    model_id = _get_model_id("MODEL_RESEARCH_NODE")
    system_prompt = (
        "You are the research node in an SOP generation pipeline.\n"
        "Return ONLY a single JSON object with this exact shape:\n"
        '{"type":"function","name":"run_research","parameters":{"prompt":"<string>"}}\n'
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
    if tool_call.get("name") != "run_research":
        raise RuntimeError(
            f"Model requested tool '{tool_call.get('name')}', expected 'run_research'."
        )
    params = tool_call.get("parameters") or {}
    if "prompt" not in params:
        raise RuntimeError("Tool call missing required 'parameters.prompt'.")

    return await run_research(**params)


# -----------------------------------------------------------------------------
# NOTE:
# We intentionally do NOT export a `research_agent = Agent(...)` here.
# Under Option B, your graph should wrap `run_research_node` with LocalNodeAgent:
#
#   research_node = LocalNodeAgent("research", lambda p: run_research_node(p, use_llama_dispatch=False))
#   gb.add_node(research_node, "research")
# -----------------------------------------------------------------------------