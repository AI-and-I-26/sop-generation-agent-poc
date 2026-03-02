import os
import re
import json
import asyncio
import logging
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Iterable

# -----------------------------
# External dependencies
# -----------------------------
import boto3
from strands import tool

# -----------------------------
# Domain types & state store
# -----------------------------
from src.graph.state_schema import SOPState, ResearchFindings, WorkflowStatus
from src.graph.state_store import STATE_STORE

# -----------------------------
# System prompt import
# -----------------------------
from src.prompts.system_prompts import RESEARCH_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Configuration (regions, models, knowledge base)
# -----------------------------------------------------------------------------
_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6"
)

_REGION = os.getenv("AWS_REGION", "us-east-2")
_KB_REGION = os.getenv("AWS_REGION", "us-east-2")


def _sanitize_kb_id(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    cleaned = raw.strip().strip('"').strip("'").strip()
    # Bedrock KB IDs are alphanumeric (service enforces)
    if cleaned and not cleaned.isalnum():
        raise RuntimeError(
            f"KNOWLEDGE_BASE_ID contains non-alphanumeric characters: {repr(raw)} -> {repr(cleaned)}"
        )
    return cleaned or None


_KB_ID = _sanitize_kb_id("1NR6BI4TNO")

# Retrieval / behavior flags
_KB_MAX_RESULTS = int(os.getenv("KB_MAX_RESULTS", "20"))
_KB_MIN_HITS = int(os.getenv("KB_MIN_HITS", "1"))
_KB_MIN_SCORE = float(os.getenv("KB_MIN_SCORE", "0.0"))

_RESEARCH_REQUIRE_KB = os.getenv("RESEARCH_REQUIRE_KB", "1") not in ("", "0", "false", "False", "FALSE")
_RESEARCH_FALLBACK = os.getenv("RESEARCH_FALLBACK", "0") not in ("", "0", "false", "False", "FALSE")
_RESEARCH_DISABLE_LLM = os.getenv("RESEARCH_DISABLE_LLM", "0") not in ("", "0", "false", "False", "FALSE")

# NEW: Force multiple rounds of queries until min hits are met
_KB_FORCE_HITS = os.getenv("KB_FORCE_HITS", "1") not in ("", "0", "false", "False", "FALSE")
_KB_MAX_ROUNDS = int(os.getenv("KB_MAX_ROUNDS", "3"))

# -----------------------------------------------------------------------------
# JSON extraction helpers (legacy — kept for safety, used by llama dispatch path)
# -----------------------------------------------------------------------------
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
_TRAILING_COMMA_RE = re.compile(r",\s*(?=[}\]])")


def _strip_code_fences(text: str) -> str:
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


def _extract_first_braced_object(s: str) -> str:
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
                    return s[start: i + 1]
    return ""


def _extract_json_block(text: str) -> str:
    if not text:
        return ""
    m = _JSON_FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    fence = re.search(r"```([\s\S]*?)```", text)
    if fence:
        inner = fence.group(1).strip()
        if inner.lower().startswith("json"):
            inner = inner[4:].strip()
        cand = _extract_first_braced_object(inner)
        if cand:
            return cand.strip()
    cand = _extract_first_braced_object(text)
    return cand.strip()


def _escape_ctrl_in_strings(s: str) -> str:
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
    return _TRAILING_COMMA_RE.sub("", s)


def _loads_lenient(text: str) -> dict:
    if not text:
        raise json.JSONDecodeError("empty", "", 0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fixed = _escape_ctrl_in_strings(text)
        fixed = _remove_trailing_commas(fixed)
        return json.loads(fixed)

# -----------------------------------------------------------------------------
# Bedrock helpers
# -----------------------------------------------------------------------------
def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


# ---- Anthropic via InvokeModel (Structured outputs) -------------------------
def _extract_text_from_invoke_body(body_json: Dict[str, Any]) -> str:
    """
    Anthropic Messages API (InvokeModel) returns:
      - 'content': [ { "type":"text", "text":"..." }, ... ]
      - 'stop_reason': 'end_turn' | 'max_tokens' | ...
    Concatenate all text blocks into a single string.
    """
    blocks = body_json.get("content", []) or []
    texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    return "".join(texts).strip()


def _invoke_model_json(
    client,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    schema: Dict[str, Any],
    *,
    initial_max_tokens: int = 4096,
    max_attempts: int = 3,
) -> Dict[str, Any]:
    """
    Invoke Anthropic (Messages API) with Structured outputs via output_config.format.
    Retries on stop_reason == 'max_tokens' by increasing max_tokens.
    """
    max_tokens = initial_max_tokens
    last_reason = None
    last_text = None

    for attempt in range(1, max_attempts + 1):
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt}
                    ],
                }
            ],
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "research_findings",
                        "schema": schema,        # JSON Schema object (not string)
                        # "strict": True,        # enable if you want all fields required strictly by schema
                    },
                }
            },
        }

        logger.debug("InvokeModel attempt %d | max_tokens=%s", attempt, max_tokens)
        resp = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body).encode("utf-8"),
        )

        # Read the model body as JSON
        raw = resp.get("body")
        body_json = json.loads(raw.read()) if raw is not None else {}
        logger.debug("Raw InvokeModel body: %s", json.dumps(body_json, default=str)[:2000])

        stop_reason = body_json.get("stop_reason")
        last_reason = stop_reason

        text = _extract_text_from_invoke_body(body_json)
        last_text = text or ""

        if stop_reason == "max_tokens":
            logger.warning("InvokeModel hit max_tokens; escalating and retrying (attempt %d).", attempt)
            max_tokens = min(max_tokens * 2, 8192)  # keep within model limits
            continue

        if not text:
            raise ValueError(f"Empty content from InvokeModel. stop_reason={stop_reason} | body={body_json}")

        # Structured outputs: text is guaranteed valid JSON per schema on successful completion
        return json.loads(text)

    raise RuntimeError(
        f"InvokeModel did not complete within token budget. Last stop_reason={last_reason}. "
        f"Last text length={len(last_text)}."
    )


# ---- Legacy raw-text Converse helpers (used only by optional llama dispatch) -
def _call_bedrock_sync(model_id: str, system_prompt: str, user_prompt: str, *, max_tokens: int = 2048) -> str:
    """
    Legacy raw-text call (kept for optional paths).
    """
    logger.debug("=== BEDROCK CALL (Research - raw text) ===")
    logger.debug("Model: %s | Region: %s | max_tokens=%s", model_id, _REGION, max_tokens)
    logger.debug("System prompt len: %d chars", len(system_prompt))
    logger.debug("User prompt (first 400 chars):\n%s", (user_prompt or "")[:400])

    client = boto3.client("bedrock-runtime", region_name=_REGION)
    body = {
        "modelId": model_id,
        "system": [{"text": system_prompt}],
        "messages": [{"role": "user", "content": [{"text": user_prompt}]}],
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0},
    }
    resp = client.converse(**body)
    logger.debug("Raw Bedrock response: %s", json.dumps(resp, default=str))

    content = resp.get("output", {}).get("message", {}).get("content", [])
    if not content:
        raise ValueError(f"Bedrock returned empty content. Full response: {resp}")
    text = "\n".join([p.get("text", "") for p in content if "text" in p]).strip()
    if not text:
        raise ValueError(f"Bedrock returned blank text. Full response: {resp}")
    logger.debug("Extracted text (%d chars):\n%s", len(text), text[:800])
    return text


async def _call_bedrock_async(model_id: str, system_prompt: str, user_prompt: str, *, max_tokens: int = 2048) -> str:
    return await asyncio.to_thread(_call_bedrock_sync, model_id, system_prompt, user_prompt, max_tokens=max_tokens)

# -----------------------------------------------------------------------------
# KB retrieval helpers (multi-query, concurrent, dedupe)
# -----------------------------------------------------------------------------
def _truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else (s[: max_len - 3] + "...")


def _tokenize_keywords(text: str) -> List[str]:
    text = (text or "").lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    # Remove very short tokens / stop-ish tokens
    stop = {"and", "or", "the", "a", "an", "of", "to", "in", "for", "on", "with", "by", "at", "be", "is", "are"}
    return [t for t in tokens if len(t) > 2 and t not in stop]


def _synonymize(words: Iterable[str]) -> List[str]:
    syn_map = {
        "qualification": ["validation", "assessment", "verification"],
        "network": ["networking"],
        "storage": ["datastore", "repositories"],
        "cloud": ["iaas", "paas", "saas"],
        "procedure": ["process", "steps", "workflow"],
        "devices": ["hardware", "equipment"],
        "infrastructure": ["systems", "it infrastructure"],
    }
    out = set(words)
    for w in list(words):
        for k, syns in syn_map.items():
            if w.startswith(k):
                out.update(syns)
    return list(out)


def _build_queries(state: SOPState) -> List[str]:
    """
    Build a robust set of semantically-overlapping queries that maximize KB hit probability.
    """
    topic = (state.topic or "").strip()
    industry = (state.industry or "").strip()
    # Base/primary
    base = [
        f"{topic} — qualification procedure for network devices, storage systems, and cloud platforms in {industry}",
        f"IT infrastructure qualification SOP: network devices, storage, cloud platforms. {industry}",
        f"Infrastructure qualification process: planning, testing, validation, maintenance, requalification",
    ]
    # Outline-driven
    outline_titles = []
    if getattr(state, "outline", None) and getattr(state.outline, "sections", None):
        outline_titles = [s.title for s in (state.outline.sections or [])][:6]
        if outline_titles:
            base.append(f"SOP sections: {', '.join(outline_titles)} — infrastructure qualification")

    # Keyword + synonym passes
    kw = _tokenize_keywords(
        f"{topic} {industry} infrastructure qualification network devices storage cloud platforms sop procedure lifecycle"
    )
    kw = _synonymize(kw)
    if kw:
        base.append(" ".join(sorted(set(kw))))

    # Compliance anchor (helps generic hits)
    base.append("OSHA ISO HIPAA FDA CLIA CAP general safety compliance requirements for IT infrastructure qualification")

    # De-duplicate while preserving order
    seen = set()
    queries = []
    for q in base:
        qn = q.strip()
        if qn and qn not in seen:
            seen.add(qn)
            queries.append(qn)
    return queries


def _kb_client():
    if not _KB_ID:
        raise RuntimeError("KNOWLEDGE_BASE_ID is not set.")
    return boto3.client("bedrock-agent-runtime", region_name=_KB_REGION)


def _content_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _merge_hits_dedupe(all_hits: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate by normalized content hash and prefer higher score for duplicates.
    """
    by_hash: Dict[str, Dict[str, Any]] = {}
    for h in all_hits:
        content = (h.get("content") or "").strip()
        if not content:
            continue
        if _KB_MIN_SCORE and float(h.get("score", 0.0)) < _KB_MIN_SCORE:
            continue
        hsh = _content_hash(content)
        if hsh not in by_hash or float(h.get("score", 0.0)) > float(by_hash[hsh].get("score", 0.0)):
            by_hash[hsh] = h
    merged = list(by_hash.values())
    merged.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    return merged


def _mk_retrieve_call(query: str, max_results: int) -> Tuple[str, Dict[str, Any]]:
    return (
        query,
        {
            "knowledgeBaseId": _KB_ID,
            "retrievalQuery": {"text": query},
            "retrievalConfiguration": {"vectorSearchConfiguration": {"numberOfResults": max_results}},
        },
    )


async def _retrieve_one(query: str, max_results: int) -> List[Dict[str, Any]]:
    client = _kb_client()
    logger.debug(
        "KB retrieve: id=%s | region=%s | max=%d | query=%s", _KB_ID, _KB_REGION, max_results, _truncate(query, 160)
    )
    resp = await asyncio.to_thread(client.retrieve, **_mk_retrieve_call(query, max_results)[1])
    out: List[Dict[str, Any]] = []
    for r in resp.get("retrievalResults", []):
        out.append(
            {
                "content": r.get("content", {}).get("text", ""),
                "score": r.get("score", 0.0),
                "source": r.get("location", {}).get("s3Location", {}).get("uri", "Unknown"),
                "query": query,
            }
        )
    logger.debug("KB retrieve: hits=%d | query=%s", len(out), _truncate(query, 80))
    return out


async def _retrieve_multi(queries: List[str], max_results: int) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Run multiple queries concurrently and merge results.
    Returns: (merged_hits, per_query_hit_counts)
    """
    per_query_hit_counts: Dict[str, int] = {}
    tasks = [asyncio.create_task(_retrieve_one(q, max_results)) for q in queries]
    all_hits: List[Dict[str, Any]] = []
    for t in asyncio.as_completed(tasks):
        try:
            hits = await t
        except Exception as e:
            logger.warning("KB retrieve error: %s", e)
            hits = []
        all_hits.extend(hits)
    # Count by originating query
    for h in all_hits:
        q = h.get("query", "")
        per_query_hit_counts[q] = per_query_hit_counts.get(q, 0) + 1
    merged = _merge_hits_dedupe(all_hits)
    return merged, per_query_hit_counts

# -----------------------------------------------------------------------------
# Domain helpers
# -----------------------------------------------------------------------------
def get_compliance_requirements(industry: str, topic: str) -> List[str]:
    compliance_map = {
        "Manufacturing": ["OSHA 1910", "ISO 9001"],
        "Healthcare": ["HIPAA", "FDA 21 CFR"],
        "Laboratory": ["CLIA", "CAP Standards"],
        "Energy": ["OSHA PSM 1910.119", "API RP 754"],
        "Information Technology (IT)": ["General Safety"],
    }
    return compliance_map.get(industry, ["General Safety"])


def _build_minimal_findings_dict(topic: str, industry: str, audience: str, compliance: List[str]) -> Dict[str, Any]:
    return {
        "similar_sops": [],
        "compliance_requirements": compliance,
        "best_practices": [],
        "sources": [],
    }

# -----------------------------------------------------------------------------
# LLM synthesis (Structured outputs via InvokeModel)
# -----------------------------------------------------------------------------
# JSON Schema for ResearchFindings
_RESEARCH_FINDINGS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "similar_sops": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "snippet": {"type": "string"},
                    "source": {"type": "string"},
                    "score": {"type": "number"}
                },
                "required": ["snippet", "source"],
                "additionalProperties": True
            },
            "default": []
        },
        "compliance_requirements": {
            "type": "array",
            "items": {"type": "string"},
            "default": []
        },
        "best_practices": {
            "type": "array",
            "items": {"type": "string"},
            "default": []
        },
        "sources": {
            "type": "array",
            "items": {"type": "string"},
            "default": []
        }
    },
    "required": ["similar_sops", "compliance_requirements", "best_practices", "sources"],
    "additionalProperties": True
}


async def _synthesize_findings(state: SOPState, kb_docs: List[Dict[str, Any]]) -> ResearchFindings:
    # Trim context for the LLM
    kb_context_lines = []
    for i, doc in enumerate(kb_docs[:15]):  # avoid giant prompts
        content = (doc.get("content") or "").strip()
        score = float(doc.get("score", 0.0))
        source = doc.get("source", "Unknown")
        if not content:
            continue
        kb_context_lines.append(f"- [{i+1}] score={score:.3f} source={source}\n  {_truncate(content, 700)}")
    kb_context = "\n".join(kb_context_lines) or "(no KB results)"
    compliance = get_compliance_requirements(state.industry, state.topic)
    compliance_str = ", ".join(compliance)

    model_id = _get_model_id("MODEL_RESEARCH")
    system_prompt = RESEARCH_SYSTEM_PROMPT

    # Direct structured-output call (sync in thread)
    def _invoke() -> Dict[str, Any]:
        client = boto3.client("bedrock-runtime", region_name=_REGION)
        return _invoke_model_json(
            client=client,
            model_id=model_id,
            system_prompt=system_prompt,
            user_prompt=(
                "Synthesize research findings for the SOP task using the knowledge base extracts below. "
                "Return ONLY a JSON object matching the provided schema (no commentary).\n\n"
                f"TOPIC: {state.topic}\n"
                f"INDUSTRY: {state.industry}\n"
                f"TARGET AUDIENCE: {state.target_audience}\n"
                f"ADDITIONAL REQUIREMENTS: {', '.join(state.requirements or [])}\n\n"
                f"COMPLIANCE (baseline): {compliance_str}\n\n"
                f"KNOWLEDGE BASE EXTRACTS:\n{kb_context}\n\n"
                "Populate 'similar_sops' with the most relevant snippets and their sources and scores, "
                "list actionable 'best_practices', enumerate 'compliance_requirements', and include a flat 'sources' list."
            ),
            schema=_RESEARCH_FINDINGS_SCHEMA,
            initial_max_tokens=4096,
            max_attempts=3,
        )

    data = await asyncio.to_thread(_invoke)
    return ResearchFindings(**data)

# -----------------------------------------------------------------------------
# Main research flow
# -----------------------------------------------------------------------------
async def _guarantee_kb_hits(state: SOPState) -> Tuple[List[Dict[str, Any]], Dict[str, int], List[str]]:
    """
    Multi-round, multi-query strategy to ensure at least KB_MIN_HITS are returned.
    Returns: (merged_hits, per_query_hit_counts, queries_tried)
    """
    queries_tried: List[str] = []
    round_idx = 0

    # Round 1: Rich multi-query from topic+industry+outline
    queries_r1 = _build_queries(state)
    queries_tried.extend(queries_r1)
    hits, per_query_counts = await _retrieve_multi(queries_r1, _KB_MAX_RESULTS)
    if len(hits) >= _KB_MIN_HITS or not _KB_FORCE_HITS:
        return hits, per_query_counts, queries_tried
    round_idx += 1
    logger.warning("KB Round %d: only %d hits; expanding...", round_idx, len(hits))

    # Round 2: Shortened / keyword-only variants
    short_topic = " ".join(_tokenize_keywords(state.topic))[:160]
    short_ind = " ".join(_tokenize_keywords(state.industry))[:80]
    queries_r2 = list({
        short_topic,
        f"{short_topic} {short_ind}",
        "infrastructure qualification steps planning testing validation maintenance",
        "network devices storage cloud platforms qualification sop",
    } - {""})
    queries_tried.extend(queries_r2)
    hits2, per2 = await _retrieve_multi(queries_r2, max(10, _KB_MAX_RESULTS))
    hits = _merge_hits_dedupe([*hits, *hits2])
    per_query_counts.update(per2)
    if len(hits) >= _KB_MIN_HITS or not _KB_FORCE_HITS:
        return hits, per_query_counts, queries_tried
    round_idx += 1
    logger.warning("KB Round %d: only %d hits; expanding...", round_idx, len(hits))

    # Round 3: Compliance-anchored probes (generic but useful)
    queries_r3 = [
        "SOP infrastructure qualification compliance responsibilities and references",
        "OSHA ISO HIPAA CLIA CAP infrastructure qualification responsibilities procedure",
        "IT systems validation SOP responsibilities definitions revision history",
    ]
    queries_tried.extend(queries_r3)
    hits3, per3 = await _retrieve_multi(queries_r3, max(10, _KB_MAX_RESULTS))
    hits = _merge_hits_dedupe([*hits, *hits3])
    per_query_counts.update(per3)

    return hits, per_query_counts, queries_tried

# -----------------------------------------------------------------------------
# Graph-level tool — performs research and persists to STATE_STORE
# -----------------------------------------------------------------------------
@tool
async def run_research(prompt: str) -> str:
    logger.info(">>> run_research called | prompt: %s", (prompt or "")[:160])

    # Extract workflow id
    m = re.search(r"workflow_id::([^\s\|]+)", prompt or "")
    workflow_id = m.group(1) if m else ""
    if not workflow_id:
        raise ValueError("Missing workflow_id in prompt; expected 'workflow_id::<id>' within the message content.")

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = f"ERROR: no state found for workflow_id='{workflow_id}' | store keys: {list(STATE_STORE.keys())}"
        logger.error(msg)
        return msg

    # Reset gating flag defensively
    try:
        state.research_complete = False
    except Exception:
        pass

    logger.info("State found | topic='%s' industry='%s' audience='%s'", state.topic, state.industry, state.target_audience)

    try:
        if not _KB_ID:
            raise RuntimeError("KNOWLEDGE_BASE_ID is not set.")

        # Run multi-round, multi-query retrieval until we meet minimum hits
        kb_docs, per_query_counts, queries_tried = await _guarantee_kb_hits(state)
        state.kb_hits = len(kb_docs)

        logger.warning(
            "KB Retrieval Summary — hits=%d | min_required=%d | queries=%d",
            state.kb_hits, _KB_MIN_HITS, len(queries_tried)
        )
        for q in queries_tried[:10]:
            logger.warning("  - '%s' -> %s hits", _truncate(q, 110), per_query_counts.get(q, 0))
        if len(queries_tried) > 10:
            logger.warning("  ... (%d more queries tried)", len(queries_tried) - 10)

        # Enforce KB requirements
        if _RESEARCH_REQUIRE_KB and state.kb_hits < _KB_MIN_HITS:
            raise RuntimeError(
                f"KB returned {state.kb_hits} hits after {min(_KB_MAX_ROUNDS, 3)} rounds and "
                f"{len(queries_tried)} queries; failing due to RESEARCH_REQUIRE_KB=1."
            )

        # Build compliance baseline
        compliance = get_compliance_requirements(state.industry, state.topic)

        # If LLM synthesis is disabled, persist minimal findings (still grounded on KB sources list)
        if _RESEARCH_DISABLE_LLM:
            findings = ResearchFindings(
                similar_sops=[{"snippet": (d.get("content") or "")[:600], "source": d.get("source", ""), "score": d.get("score", 0.0)} for d in kb_docs],
                compliance_requirements=compliance,
                best_practices=[],
                sources=[d.get("source", "") for d in kb_docs],
            )
        else:
            # Synthesize structured findings with the LLM using top KB chunks
            findings = await _synthesize_findings(state, kb_docs)

        # Persist and gate
        state.research = findings
        state.status = WorkflowStatus.RESEARCHED
        state.current_node = "research"
        state.research_complete = True

        if hasattr(state, "increment_tokens"):
            state.increment_tokens(2000)

        STATE_STORE[workflow_id] = state

        logger.warning(
            "Router hint — research_complete=%s | wid=%s | kb_hits=%s | state_id=%s | keys=%s",
            getattr(state, "research_complete", None), workflow_id, state.kb_hits, id(state), list(STATE_STORE.keys())
        )

        return (
            f"workflow_id::{workflow_id} | "
            f"Research complete: kb_hits={state.kb_hits}, "
            f"{len(getattr(findings, 'similar_sops', []) or [])} similar SOPs, "
            f"{len(getattr(findings, 'compliance_requirements', []) or [])} compliance requirements"
        )

    except Exception as e:
        logger.exception("Research FAILED for workflow_id=%s", workflow_id)

        if _RESEARCH_REQUIRE_KB:
            if hasattr(state, "add_error"):
                state.add_error(f"Research failed (KB required): {str(e)}")
            state.status = WorkflowStatus.FAILED
            state.research_complete = False
            STATE_STORE[workflow_id] = state
            logger.warning(
                "Router hint — research_complete=%s | wid=%s | kb_hits=%s | state_id=%s | keys=%s",
                getattr(state, "research_complete", None), workflow_id, getattr(state, "kb_hits", None), id(state), list(STATE_STORE.keys())
            )
            return f"workflow_id::{workflow_id} | Research FAILED (KB required): {e}"

        # Optional deterministic fallback
        if _RESEARCH_FALLBACK:
            try:
                compliance = get_compliance_requirements(state.industry, state.topic)
                minimal = _build_minimal_findings_dict(state.topic, state.industry, state.target_audience, compliance)
                findings = ResearchFindings(**minimal)
                state.research = findings
                state.status = WorkflowStatus.RESEARCHED
                state.current_node = "research"
                state.research_complete = True
                state.kb_hits = int(getattr(state, "kb_hits", 0) or 0)
                STATE_STORE[workflow_id] = state
                logger.warning("Research fallback used — minimal findings persisted.")
                logger.warning(
                    "Router hint — research_complete=%s | wid=%s | kb_hits=%s | state_id=%s | keys=%s",
                    getattr(state, "research_complete", None), workflow_id, state.kb_hits, id(state), list(STATE_STORE.keys())
                )
                return (
                    f"workflow_id::{workflow_id} | Research fallback used: "
                    f"kb_hits={state.kb_hits}, "
                    f"{len(getattr(findings, 'similar_sops', []) or [])} similar SOPs, "
                    f"{len(getattr(findings, 'compliance_requirements', []) or [])} compliance requirements"
                )
            except Exception as fallback_err:
                logger.error("Research fallback FAILED: %s", fallback_err)

        # Hard failure path
        if hasattr(state, "add_error"):
            state.add_error(f"Research failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        state.research_complete = False
        STATE_STORE[workflow_id] = state
        logger.warning(
            "Router hint — research_complete=%s | wid=%s | kb_hits=%s | state_id=%s | keys=%s",
            getattr(state, "research_complete", None), workflow_id, getattr(state, "kb_hits", None), id(state), list(STATE_STORE.keys())
        )
        return f"workflow_id::{workflow_id} | Research FAILED: {e}"

# -----------------------------------------------------------------------------
# Node entry point
# -----------------------------------------------------------------------------
async def run_research_node(prompt: str, *, use_llama_dispatch: bool = False) -> str:
    logger.info(">>> run_research_node | use_llama_dispatch=%s", use_llama_dispatch)
    if not use_llama_dispatch:
        return await run_research(prompt=prompt)

    # Optional model-planned tool dispatch (still client-side; uses raw Converse path)
    model_id = _get_model_id("MODEL_RESEARCH_NODE")
    system_prompt = (
        "You are the research node in an SOP generation pipeline.\n"
        "Return ONLY a single JSON object with this exact shape:\n"
        '{"type":"function","name":"run_research","parameters":{"prompt":"<string>"}}\n'
        "Do NOT include any surrounding text, markdown, code fences, or commentary."
    )
    raw = await _call_bedrock_async(model_id, system_prompt, prompt, max_tokens=256)

    try:
        obj = json.loads(_strip_code_fences(raw))
    except Exception:
        obj = {}

    if not (isinstance(obj, dict) and obj.get("type") == "function" and obj.get("name") == "run_research"):
        raise RuntimeError(f"Model did not return a parseable tool call JSON. Got: {raw[:500]}...")

    params = obj.get("parameters") or {}
    if "prompt" not in params:
        raise RuntimeError("Tool call missing required 'parameters.prompt'.")

    return await run_research(**params)

# Alias for compatibility
research_tool = run_research_node
