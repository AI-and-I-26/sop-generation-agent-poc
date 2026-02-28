"""
Research Agent - Module 5, Section 5.1 (Option B: client-side tool execution)

Role:
  Performs research using RAG (Bedrock Knowledge Base) and other client-side helpers,
  then synthesizes findings with an LLM (Bedrock Converse) into structured JSON that
  is persisted to the graph's STATE_STORE.

GRAPH INTEGRATION PATTERN:
  - The graph sends a plain string that includes 'workflow_id::<id>'.
  - We keep a module-level STATE_STORE keyed by workflow_id (same as planning).
  - This module exposes:
      * async @tool run_research(prompt: str) -> str   (does the real work)
      * async run_research_node(prompt: str, use_llama_dispatch: bool=False) -> str
  - The graph should call run_research_node(prompt, use_llama_dispatch=False)
    via the LocalNodeAgent wrapper (see sop_workflow.py refactor).

ARCHITECTURE (Option B: client-side tool execution):
  - We do NOT rely on Bedrock server-side tool use.
  - All tool decisions and execution happen client-side.
  - Optionally, you can ask the model to output a JSON "function-call" string,
    parse it locally, validate, and then dispatch to the local tool. This preserves
    a function-calling surface while avoiding server-side invocation.

DEBUG LOGGING:
  Set LOG_LEVEL=DEBUG in your environment or add this to your entry point:
      import logging
      logging.basicConfig(level=logging.DEBUG)
  You will then see request/response details for Bedrock calls, as well as KB lookups.
"""

# -----------------------------
# Standard library imports
# -----------------------------
import os
import re
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional

# -----------------------------
# External dependencies
# -----------------------------
import boto3               # AWS SDK for Python: used for Bedrock Converse and KB runtime
from strands import tool   # Optional decorator marking callable as a "tool" for your orchestration

# -----------------------------
# Domain types & state store
# -----------------------------
from src.graph.state_schema import SOPState, ResearchFindings, WorkflowStatus
from src.graph.state_store import STATE_STORE

# -----------------------------
# System prompt import (new path preferred; fallback for older repo layout)
# -----------------------------

from src.prompts.system_prompts import RESEARCH_SYSTEM_PROMPT  # preferred path

# Module-level logger (inherits config from your entry point)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Configuration (regions, model, knowledge base)
# -----------------------------------------------------------------------------
# Default Bedrock model (Meta Llama 3.3 70B Instruct). Overridable via env vars.
_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)

# Region for Bedrock Converse API. Override via AWS_REGION.
_REGION = os.getenv("AWS_REGION", "us-east-2")

# Region for Bedrock Agent Runtime (Knowledge Base). Typically matches _REGION for lower latency.
_KB_REGION = os.getenv("AWS_REGION", "us-east-2")

# Knowledge Base ID used for RAG retrieval. Must be set in your environment to enable KB queries.
# If absent, KB retrieval is skipped with a warning.
_KB_ID = os.getenv("KNOWLEDGE_BASE_ID", "1NR6BI4TNO")

# -----------------------------------------------------------------------------
# Robust JSON extraction & lenient parsing helpers
# -----------------------------------------------------------------------------
# Precompiled regex: capture a JSON object within ```json ... ``` fenced blocks
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)

# Precompiled regex: match trailing commas before closing '}' or ']' (invalid in strict JSON)
_TRAILING_COMMA_RE = re.compile(r",\s*(?=[}\]])")


def _extract_first_braced_object(s: str) -> str:
    """
    Return the first balanced {...} object found in the text, else ''.

    Rationale:
      LLMs sometimes produce prose that surrounds JSON. We scan for the first
      balanced brace block to salvage likely JSON payloads.
    """
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
                    return s[start : i + 1]
    return ""


def _extract_json_block(text: str) -> str:
    """
    Try in order to extract a JSON object as text:
      1) ```json ... ```
      2) generic ``` ... ``` (then strip language and find first {...})
      3) first balanced {...} object from raw text

    Returns '' if nothing found.
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
    Escape raw control chars inside double-quoted strings to make JSON parseable:
      \n -> \\n, \r -> \\r, \t -> \\t

    Why:
      Some LLMs embed literal newlines/tabs within JSON string values. Strict
      json.loads rejects these; escaping them makes parsing more resilient.
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
    """
    Remove trailing commas that may appear in objects/arrays:
      {"a":1,} -> {"a":1}    [1,2,] -> [1,2]
    """
    return _TRAILING_COMMA_RE.sub("", s)


def _loads_lenient(text: str) -> dict:
    """
    Lenient JSON loader:
      - Try strict json.loads first.
      - On failure, escape control characters and remove trailing commas, then try again.

    Raises:
      json.JSONDecodeError if parsing still fails.
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
    """
    Resolve model ARN by environment variable (e.g., MODEL_RESEARCH / MODEL_RESEARCH_NODE),
    falling back to _DEFAULT_MODEL_ID.
    """
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _call_bedrock_sync(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 2048,
) -> str:
    """
    Synchronously call Bedrock Converse API and extract the returned text.

    Notes:
      * This is a blocking call (boto3). In async contexts we offload to a thread.
      * Consider setting temperature=0 for deterministic research output (JSON).
      * We do not set 'responseFormat' because some models reject it with Converse.
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

    response = client.converse(**request_body)
    logger.debug("Raw Bedrock response: %s", json.dumps(response, default=str))

    # Extract the concatenated "text" parts
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
    Async wrapper that offloads the blocking boto3 call to a worker thread, so the
    event loop remains responsive.
    """
    return await asyncio.to_thread(
        _call_bedrock_sync, model_id, system_prompt, user_prompt, max_tokens=max_tokens
    )


def _strip_code_fences(text: str) -> str:
    """
    Remove ```...``` or ```json ... ``` fences if present.
    (Kept for compatibility with older parsing paths.)
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
    Find JSON objects in free-form text by brace balancing and parse those that are valid dicts.

    Useful when the model returns prose around structured content.
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
    Optional Mode: Extract the first object that looks like a function call:
      {"type":"function","name":"run_research","parameters": {...}}

    Flow:
      1) Strip code fences
      2) Try json.loads on the full cleaned string
      3) Fallback to scanning for embedded dict objects
    """
    if not text:
        return None
    cleaned = _strip_code_fences(text)

    # Try entire content first
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
    """
    Extract workflow id from messages that follow the convention:
      "workflow_id::<id> | <rest of message>"
    """
    m = re.search(r"workflow_id::([^\s\|]+)", prompt or "")
    return m.group(1) if m else None


def _parse_json_response(text: str) -> dict:
    """
    Legacy JSON parser: strip code fences and parse JSON strictly.
    (Kept as a fallback; newer flow uses _extract_json_block + _loads_lenient.)
    """
    t = _strip_code_fences(text)
    logger.debug("Parsing JSON (%d chars):\n%s", len(t), t[:800])
    return json.loads(t)


# -----------------------------------------------------------------------------
# Domain helpers (sync by design; offload via asyncio.to_thread in async flows)
# -----------------------------------------------------------------------------
def _truncate(s: str, max_len: int) -> str:
    """
    Truncate a string to at most max_len characters, adding "..." if needed.
    Used to limit the size of KB snippets provided to the model.
    """
    return s if len(s) <= max_len else (s[: max_len - 3] + "...")


def search_knowledge_base(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search Bedrock Knowledge Base for semantically similar documents.

    Returns:
      A list of dicts with keys: {content, score, source}.

    Behavior:
      - If KNOWLEDGE_BASE_ID isn't set, logs a warning and returns an empty list.
      - Uses vector search configuration to retrieve top-N results.
      - Normalizes output across KB record variations.

    Caveats:
      - Requires appropriate IAM permissions for bedrock-agent-runtime:Retrieve.
      - Sources are reported from the KB 'location' metadata when available.
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
            results.append(
                {
                    "content": r.get("content", {}).get("text", ""),
                    "score": r.get("score", 0.0),
                    "source": (
                        r.get("location", {})
                        .get("s3Location", {})
                        .get("uri", "Unknown")
                    ),
                }
            )
        return results
    except Exception as e:
        logger.error("KB search error: %s", e)
        return results


def get_compliance_requirements(industry: str, topic: str) -> List[str]:
    """
    Return a baseline set of compliance/regulatory requirements for a given industry/topic.

    Note:
      This is a static placeholder map — suitable for a baseline signal during development.
      Replace/extend with calls to your actual compliance sources/services as needed.
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
    synthesizes best practices via LLaMA (expects JSON-only), saves findings to STATE_STORE,
    and returns a summary string for the next graph node.

    Args:
      prompt:
        Graph message string containing 'workflow_id::<id>'.

    Flow:
      1) Extract workflow_id and fetch SOPState from STATE_STORE; fail fast if missing.
      2) Build a KB query (optionally hinting with outline section titles if available).
      3) Retrieve KB docs (RAG) and baseline compliance requirements (client-side).
      4) Construct system+user prompts and call Bedrock with a small retry loop.
      5) Extract a JSON object robustly and parse it leniently into ResearchFindings.
      6) Persist findings into state; set status to RESEARCHED; update current_node/tokens.
      7) Return a compact status line including summary counts.

    Returns:
      A compact status message used by the next graph node.
    """
    logger.info(">>> run_research called | prompt: %s", (prompt or "")[:160])

    # 1) Identify the workflow/run
    workflow_id = _extract_workflow_id_from_prompt(prompt or "") or ""
    logger.debug("Extracted workflow_id: '%s'", workflow_id)

    if not workflow_id:
        # Fail fast catches graph wiring mistakes early
        raise ValueError(
            "Missing workflow_id in prompt; expected 'workflow_id::<id>' within the message content."
        )

    # Retrieve current state
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
        # 2) Build KB query (optionally use the first few outline section titles as hints)
        outline_hint = ""
        if getattr(state, "outline", None) and getattr(state.outline, "sections", None):
            first_titles = [s.title for s in (state.outline.sections or [])][:5]
            outline_hint = f"Outline sections hint: {', '.join(first_titles)}"

        kb_query = f"{state.topic} in {state.industry}. {outline_hint}".strip()

        # Offload blocking KB retrieval to a worker thread to keep event loop responsive
        kb_docs: List[Dict[str, Any]] = await asyncio.to_thread(
            search_knowledge_base, kb_query, 5
        )

        # 3) Gather baseline compliance set
        compliance = get_compliance_requirements(state.industry, state.topic)

        # Compose KB context (trim content to avoid passing huge text to the LLM)
        kb_context_lines = []
        for i, doc in enumerate(kb_docs):
            content = _truncate(doc.get("content", ""), 700)
            score = doc.get("score", 0.0)
            source = doc.get("source", "Unknown")
            kb_context_lines.append(
                f"- [{i+1}] score={score:.3f} source={source}\n  {content}"
            )
        kb_context = "\n".join(kb_context_lines)
        compliance_str = ", ".join(compliance)

        # 4) Prepare prompts for the LLM to synthesize JSON findings
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

        # Bedrock call with simple retry loop for resiliency
        model_id = _get_model_id("MODEL_RESEARCH")
        last_err: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                raw_text = await _call_bedrock_async(
                    model_id, system_prompt, user_prompt, max_tokens=2048
                )
                break
            except Exception as e:
                last_err = e
                logger.warning("Bedrock call failed (attempt %d/3): %s", attempt, e)
                if attempt < 3:
                    await asyncio.sleep(0.75 * attempt)
        else:
            # All attempts exhausted
            raise last_err or RuntimeError("Unknown Bedrock error during research")

        # 5) Robust JSON extraction + lenient parsing
        json_str = _extract_json_block(raw_text) or _strip_code_fences(raw_text)
        findings_data = _loads_lenient(json_str)

        # Validate against your domain dataclass (raises if shape/fields mismatch)
        findings = ResearchFindings(**findings_data)

        # 6) Persist to state and advance workflow
        state.research = findings
        state.status = WorkflowStatus.RESEARCHED
        state.current_node = "research"

        # Optional: rough token accounting by node (adjust to your telemetry)
        if hasattr(state, "increment_tokens"):
            state.increment_tokens(2000)

        logger.info(
            "Research complete — similar_sops=%d | compliance=%d | workflow_id=%s",
            len(findings.similar_sops or []),
            len(findings.compliance_requirements or []),
            workflow_id,
        )

        # 7) Compact summary for chaining to the next graph node
        return (
            f"workflow_id::{workflow_id} | "
            f"Research complete: {len(findings.similar_sops or [])} similar SOPs, "
            f"{len(findings.compliance_requirements or [])} compliance requirements"
        )

    except Exception as e:
        # Defensive failure path: mark the run as FAILED and store details on state
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
    use_llama_dispatch: bool = False,
) -> str:
    """
    Entry point for the RESEARCH node under Option B. (ASYNC)

    Modes:
      - Default (use_llama_dispatch=False):
          Directly execute the local tool `run_research(prompt=...)`.
          This avoids an extra LLM hop and is deterministic.

      - Optional (use_llama_dispatch=True):
          Ask the model to output ONLY a single function-call JSON:
            {"type":"function","name":"run_research","parameters":{"prompt":"<string>"}}
          Parse locally, validate the function name and required parameters,
          then dispatch to the local tool. Still 100% client-side execution.

    Returns:
      The tool result string to pass to the next node.
    """
    logger.info(">>> run_research_node | use_llama_dispatch=%s", use_llama_dispatch)

    if not use_llama_dispatch:
        # Recommended path: direct local tool execution
        return await run_research(prompt=prompt)

    # --- Optional: LLaMA-driven function-call string, parsed client-side ---
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

    # Safety: ensure the model is not attempting to call an unexpected function
    if tool_call.get("name") != "run_research":
        raise RuntimeError(
            f"Model requested tool '{tool_call.get('name')}', expected 'run_research'."
        )

    params = tool_call.get("parameters") or {}
    if "prompt" not in params:
        raise RuntimeError("Tool call missing required 'parameters.prompt'.")

    # Dispatch to the local async tool
    return await run_research(**params)


# -----------------------------------------------------------------------------
# NOTE:
# We intentionally do NOT export a `research_agent = Agent(...)` here.
# Under Option B, your graph should wrap `run_research_node` with LocalNodeAgent:
#
#   research_node = LocalNodeAgent("research", lambda p: run_research_node(p, use_llama_dispatch=False))
#   gb.add_node(research_node, "research")
#
# This keeps all tool execution on the client side while retaining a clean node interface.
# -----------------------------------------------------------------------------