# research_agent.py — Research Agent for the SOP pipeline.
#
# ROLE IN PIPELINE:
#     Node 2 of 5.  After the planning agent produces an outline, the research
#     agent queries the Bedrock Knowledge Base (KB) to retrieve existing SOP
#     documents that match the new SOP's topic.  Retrieved chunks are then
#     synthesised by Claude into structured ResearchFindings that include:
#       • Content facts per SOP section (section_insights)
#       • Formatting conventions observed in the KB documents (kb_format_context)
#
# ASSUMPTION: THE KB ALWAYS CONTAINS SOP DOCUMENTS.
#     This agent is designed around the guarantee that the KB will always hold
#     at least one SOP document.  However, to meet runtime/SLA constraints, this
#     tuned version will *not* run indefinitely; if it cannot obtain KB hits
#     promptly, it will *return format-only results* so downstream nodes can
#     continue with reliable formatting.
#
# CHANGES (Performance & Robustness):
#   • Time-bounded KB retrieval (max rounds + per-round + overall timeout).
#   • No token doubling in LLM calls; single attempt by default with a smaller cap.
#   • If KB retrieval yields 0 hits or times out, skip LLM synthesis and return
#     a ResearchFindings object with kb_format_context derived from the outline
#     (or a standard 8-section SOP skeleton).
#   • Structured Outputs (InvokeModel) uses Bedrock-safe JSON Schemas (no unions,
#     no defaults, no array cardinality keywords) and logs ValidationException details.
#   • Robust JSON parsing fallback with a light “repair” pass to prevent decode errors.
#
# GUARANTEED-HITS RETRIEVAL STRATEGY (time-bounded):
#     Round 1 — Rich topic + industry + outline-section queries (concurrent)
#     Round 2 — Shortened keyword-only variants (concurrent)
#     If no hits after configured rounds/time → return format-only findings.
#
# ENVIRONMENT VARIABLES (all optional):
#     MODEL_RESEARCH            — Bedrock model ID (default: claude-sonnet-4-6)
#     AWS_REGION                — AWS region (default: us-east-2)
#     KB_MAX_RESULTS            — max KB hits per query (default: 20)
#     KB_MIN_SCORE              — min relevance score (default: 0.0)
#     RESEARCH_DISABLE_LLM      — skip LLM synthesis (default: false)
#
#     # NEW TUNING KNOBS:
#     RESEARCH_MAX_ROUNDS       — 1..4 (default: 2)
#     RESEARCH_ROUND_TIMEOUT_SEC— per-round timeout in seconds (default: 6.0)
#     RESEARCH_TIMEOUT_SEC      — overall retrieval timeout in seconds (default: 20.0)
#     RESEARCH_MAX_TOKENS       — LLM max tokens for InvokeModel (default: 1536)
#     RESEARCH_MAX_ATTEMPTS     — LLM attempts (default: 1; no doubling)
#

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError
from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import ResearchFindings, SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE
from src.prompts.system_prompts import RESEARCH_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ── CONFIGURATION ──────────────────────────────────────────────────────────────

_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION    = os.getenv("AWS_REGION", "us-east-2")
_KB_REGION = os.getenv("AWS_REGION", "us-east-2")


def _sanitize_kb_id(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    cleaned = raw.strip().strip('"').strip("'").strip()
    if cleaned and not cleaned.isalnum():
        raise RuntimeError(
            f"KNOWLEDGE_BASE_ID contains non-alphanumeric chars: "
            f"{repr(raw)} → {repr(cleaned)}"
        )
    return cleaned or None


# KB ID must be set via KNOWLEDGE_BASE_ID environment variable.
_KB_ID = _sanitize_kb_id(os.getenv("KNOWLEDGE_BASE_ID"))

# ── Retrieval tuning ────────────────────────────────────────────────────────────
_KB_MAX_RESULTS = int(os.getenv("KB_MAX_RESULTS", "20"))
_KB_MIN_SCORE  = float(os.getenv("KB_MIN_SCORE", "0.0"))

# LLM control (synthesis):
_RESEARCH_DISABLE_LLM = os.getenv("RESEARCH_DISABLE_LLM", "0") not in ("", "0", "false", "False")

# NEW: performance knobs
_RESEARCH_MAX_ROUNDS        = max(1, min(4, int(os.getenv("RESEARCH_MAX_ROUNDS", "2"))))
_RESEARCH_ROUND_TIMEOUT_SEC = float(os.getenv("RESEARCH_ROUND_TIMEOUT_SEC", "6.0"))
_RESEARCH_TIMEOUT_SEC       = float(os.getenv("RESEARCH_TIMEOUT_SEC", "20.0"))
_RESEARCH_MAX_TOKENS        = int(os.getenv("RESEARCH_MAX_TOKENS", "1536"))
_RESEARCH_MAX_ATTEMPTS      = max(1, int(os.getenv("RESEARCH_MAX_ATTEMPTS", "1")))


def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


# ── JSON SCHEMA FOR STRUCTURED RESEARCH FINDINGS (Bedrock‑safe) ──
_RESEARCH_FINDINGS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "similar_sops": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "snippet": {"type": "string"},
                    "source":  {"type": "string"},
                    "score":   {"type": "number"}
                },
                "required": ["snippet", "source"]
            }
        },
        "compliance_requirements": {"type": "array", "items": {"type": "string"}},
        "best_practices":          {"type": "array", "items": {"type": "string"}},
        "sources":                 {"type": "array", "items": {"type": "string"}},

        # Represent insights as an array of closed objects (map-like as entries)
        "section_insights": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "section_number": {"type": "string"},  # e.g., "6.0"
                    "fact":           {"type": "string"},
                    "source":         {"type": "string"}
                },
                "required": ["section_number", "fact"]
            }
        },

        # Close the formatting context shape so Bedrock accepts the schema
        "kb_format_context": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "section_titles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "number": {"type": "string"},
                            "title":  {"type": "string"}
                        },
                        "required": ["number", "title"]
                    }
                },
                "numbering_style": {"type": "string"},
                "table_sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "number":  {"type": "string"},
                            "columns": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["number", "columns"]
                    }
                },
                "subsection_sections": {"type": "array", "items": {"type": "string"}},
                "prose_sections":      {"type": "array", "items": {"type": "string"}},
                "writing_style":       {"type": "string"},
                "special_elements":    {"type": "array", "items": {"type": "string"}},
                "section_count":       {"type": "number"},
                "banned_elements":     {"type": "array", "items": {"type": "string"}}
            }
        }
    },
    "required": [
        "similar_sops",
        "compliance_requirements",
        "best_practices",
        "sources"
    ]
}


# ── INVOKEMODEL HELPERS (Anthropic on Bedrock with Structured Outputs) ────────

def _extract_text_from_invoke_body(body_json: Dict[str, Any]) -> str:
    blocks = body_json.get("content", []) or []
    texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    return "".join(texts).strip()


def _repair_malformed_json(text: str) -> str:
    """
    Attempt to repair common JSON issues:
      - strip code fences
      - drop leading prose
      - cut to last balanced top-level brace/bracket
      - remove trailing commas before } or ]
    """
    if not text:
        return text
    t = (text or "").strip()

    # Strip code fences if present
    if t.startswith("```"):
        parts = t.split("```")
        if len(parts) >= 2:
            t = parts[1]
            if t.lstrip().startswith("json"):
                t = t.lstrip()[4:]
        t = t.strip()

    # Drop leading prose before first JSON token
    first = min([i for i in [t.find("{"), t.find("[")] if i != -1], default=-1)
    if first > 0:
        t = t[first:]

    # Keep up to last balanced top-level brace/bracket
    stack, last = [], -1
    for i, ch in enumerate(t):
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack:
                opener = stack.pop()
                if (opener, ch) in (("{", "}"), ("[", "]")) and not stack:
                    last = i
    if last != -1:
        t = t[:last + 1]

    # Remove trailing comma before } or ]
    t = re.sub(r",\s*([}\]])", r"\1", t)
    return t.strip()


def _safe_parse_json_text(text: str) -> Dict[str, Any]:
    """
    Parse JSON; if it fails, run a light repair pass and parse again.
    """
    t = (text or "").strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        repaired = _repair_malformed_json(t)
        return json.loads(repaired)


def _invoke_model_json(
    client,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    schema: Dict[str, Any],
    initial_max_tokens: int = _RESEARCH_MAX_TOKENS,
    max_attempts: int = _RESEARCH_MAX_ATTEMPTS,
) -> Dict[str, Any]:
    """
    Call Bedrock InvokeModel (Anthropic Messages API) with Structured Outputs.

    - Uses output_config.format.type = "json_schema" with format.schema=<schema>.
    - Single (or minimal) attempt(s) — no token doubling — for bounded latency.
    - If the environment rejects output_config (ValidationException), we log the
      server message and retry once without structured outputs.
    """
    attempts_left = max(1, max_attempts)
    use_structured_outputs = True
    while attempts_left > 0:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": initial_max_tokens,
            "temperature": 0.0,
            "system": system_prompt,
            "messages": [{"role": "user", "content": [{"type": "text", "text": user_prompt}]}],
        }
        if use_structured_outputs:
            body["output_config"] = {
                "format": {
                    "type": "json_schema",
                    "schema": schema,  # Correct field for InvokeModel + Anthropic
                }
            }

        logger.debug(
            "InvokeModel | tokens=%d | structured=%s | attempts_left=%d",
            initial_max_tokens, use_structured_outputs, attempts_left
        )
        try:
            resp = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body).encode("utf-8"),
            )
        except ClientError as e:
            err = e.response.get("Error", {})
            code = err.get("Code")
            msg  = err.get("Message", str(e))
            if use_structured_outputs and code == "ValidationException":
                logger.warning(
                    "InvokeModel ValidationException (Structured Outputs rejected): %s",
                    msg
                )
                use_structured_outputs = False
                # Retry *once* without structured outputs
                continue
            raise

        raw = resp.get("body")
        body_json = json.loads(raw.read()) if raw is not None else {}
        text = _extract_text_from_invoke_body(body_json)
        if not text:
            raise ValueError(f"InvokeModel returned empty content. body={body_json}")
        return _safe_parse_json_text(text)

    raise RuntimeError("InvokeModel exhausted attempts without a response")


# ── STRING / TEXT HELPERS ──────────────────────────────────────────────────────

def _truncate(s: str, max_len: int) -> str:
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _tokenize_keywords(text: str) -> List[str]:
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    stop = {"and","or","the","a","an","of","to","in","for","on","with","by","at","be","is","are"}
    return [t for t in tokens if len(t) > 2 and t not in stop]


def _synonymize(words: Iterable[str]) -> List[str]:
    syn_map = {
        "qualification": ["validation", "assessment, verification".split(", ")[1], "verification"],
        "network":        ["networking"],
        "storage":        ["datastore", "repositories"],
        "cloud":          ["iaas", "paas", "saas"],
        "procedure":      ["process", "steps", "workflow"],
        "devices":        ["hardware", "equipment"],
        "infrastructure": ["systems", "it infrastructure"],
    }
    # Fix duplicate from split line above
    syn_map["qualification"] = ["validation", "assessment", "verification"]

    out = set(words)
    for w in list(words):
        for k, syns in syn_map.items():
            if w.startswith(k):
                out.update(syns)
    return list(out)


# ── QUERY BUILDING ─────────────────────────────────────────────────────────────

def _build_queries(state: SOPState) -> List[str]:
    topic    = (state.topic or "").strip()
    industry = (state.industry or "").strip()

    base: List[str] = [
        f"{topic} {industry}",
        f"{topic} standard operating procedure",
        f"{industry} SOP procedure responsibilities scope definitions references",
        f"{topic} procedure purpose scope responsibilities",
    ]

    if getattr(state, "outline", None) and getattr(state.outline, "sections", None):
        titles = [s.title for s in state.outline.sections if s.title][:6]
        if titles:
            base.append(f"SOP {', '.join(titles)}")
            base.append(f"{topic} {' '.join(titles[:3])}")

    keywords = _tokenize_keywords(f"{topic} {industry} sop procedure")
    keywords = _synonymize(keywords)
    if keywords:
        base.append(" ".join(sorted(set(keywords))))

    seen: set = set()
    queries: List[str] = []
    for q in base:
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            queries.append(q)
    return queries


# ── KB CLIENT + RETRIEVAL ──────────────────────────────────────────────────────

def _kb_client():
    if not _KB_ID:
        raise RuntimeError(
            "KNOWLEDGE_BASE_ID is not set. "
            "Set the KNOWLEDGE_BASE_ID environment variable."
        )
    return boto3.client("bedrock-agent-runtime", region_name=_KB_REGION)


def _content_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _merge_hits_dedupe(all_hits: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_hash: Dict[str, Dict[str, Any]] = {}
    for h in all_hits:
        content = (h.get("content") or "").strip()
        if not content:
            continue
        hsh = _content_hash(content)
        if hsh not in by_hash or float(h.get("score", 0)) > float(by_hash[hsh].get("score", 0)):
            by_hash[hsh] = h
    merged = list(by_hash.values())
    merged.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    return merged


async def _retrieve_one(query: str, max_results: int) -> List[Dict[str, Any]]:
    client = _kb_client()
    logger.debug(
        "KB retrieve | id=%s | region=%s | max=%d | query=%.160s",
        _KB_ID, _KB_REGION, max_results, query
    )

    resp = await asyncio.to_thread(
        client.retrieve,
        knowledgeBaseId=_KB_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={
            "vectorSearchConfiguration": {"numberOfResults": max_results}
        },
    )

    hits: List[Dict[str, Any]] = []
    for r in resp.get("retrievalResults", []):
        score = float(r.get("score", 0.0))
        if score < _KB_MIN_SCORE:
            continue
        hits.append({
            "content": r.get("content", {}).get("text", ""),
            "score":   score,
            "source":  r.get("location", {}).get("s3Location", {}).get("uri", "Unknown"),
            "query":   query,
        })
    logger.debug("KB retrieve | hits=%d | query=%.80s", len(hits), query)
    return hits


async def _retrieve_multi(queries: List[str], max_results: int) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    per_query_counts: Dict[str, int] = {}
    tasks = [asyncio.create_task(_retrieve_one(q, max_results)) for q in queries]
    all_hits: List[Dict[str, Any]] = []

    for task in asyncio.as_completed(tasks):
        try:
            hits = await task
        except Exception as e:
            logger.warning("KB retrieve error (query skipped): %s", e)
            hits = []
        all_hits.extend(hits)

    for h in all_hits:
        q = h.get("query", "")
        per_query_counts[q] = per_query_counts.get(q, 0) + 1

    merged = _merge_hits_dedupe(all_hits)
    return merged, per_query_counts


# ── TIME-BOUNDED KB RETRIEVAL ─────────────────────────────────────────────────

async def _try_kb_hits_timeboxed(state: SOPState) -> Tuple[List[Dict[str, Any]], Dict[str, int], List[str]]:
    """
    Attempt up to _RESEARCH_MAX_ROUNDS of retrieval with per-round and overall timeouts.
    If no hits by the end (or timeout), returns ([], {...}, queries_tried).
    """
    start_ts = time.monotonic()
    queries_tried: List[str] = []
    per_query_counts: Dict[str, int] = {}
    hits: List[Dict[str, Any]] = []

    # Round 1
    if _RESEARCH_MAX_ROUNDS >= 1:
        if time.monotonic() - start_ts > _RESEARCH_TIMEOUT_SEC:
            logger.warning("Overall research timeout reached before Round 1.")
            return [], per_query_counts, queries_tried

        queries_r1 = _build_queries(state)
        queries_tried.extend(queries_r1)
        try:
            hits, per1 = await asyncio.wait_for(
                _retrieve_multi(queries_r1, _KB_MAX_RESULTS),
                timeout=_RESEARCH_ROUND_TIMEOUT_SEC
            )
            if isinstance(hits, tuple):
                hits, per1 = hits  # safety
        except asyncio.TimeoutError:
            logger.warning("KB Round 1 timed out after %.1fs", _RESEARCH_ROUND_TIMEOUT_SEC)
            hits, per1 = [], {}
        per_query_counts.update(per1 if isinstance(per1, dict) else {})

        if hits:
            logger.info("KB Round 1: %d hits across %d queries", len(hits), len(queries_r1))
            return hits, per_query_counts, queries_tried

    # Round 2
    if _RESEARCH_MAX_ROUNDS >= 2:
        if time.monotonic() - start_ts > _RESEARCH_TIMEOUT_SEC:
            logger.warning("Overall research timeout reached before Round 2.")
            return hits, per_query_counts, queries_tried

        short_topic = " ".join(_tokenize_keywords(state.topic))[:160]
        short_ind   = " ".join(_tokenize_keywords(state.industry))[:80]
        queries_r2 = list({
            short_topic,
            f"{short_topic} {short_ind}",
            f"{state.topic} procedure responsibilities scope",
            f"{state.industry} {state.topic} SOP",
            f"{state.industry} {state.topic}",
        } - set(queries_tried))
        queries_tried.extend(queries_r2)

        try:
            round2, per2 = await asyncio.wait_for(
                _retrieve_multi(queries_r2, _KB_MAX_RESULTS),
                timeout=_RESEARCH_ROUND_TIMEOUT_SEC
            )
            if isinstance(round2, tuple):
                round2, per2 = round2
        except asyncio.TimeoutError:
            logger.warning("KB Round 2 timed out after %.1fs", _RESEARCH_ROUND_TIMEOUT_SEC)
            round2, per2 = [], {}

        hits = _merge_hits_dedupe([*hits, *round2])
        per_query_counts.update(per2 if isinstance(per2, dict) else {})

        if hits:
            logger.info("KB Round 2: %d total hits", len(hits))
            return hits, per_query_counts, queries_tried

    logger.info("KB retrieval finished with 0 hits after %d round(s).", _RESEARCH_MAX_ROUNDS)
    return [], per_query_counts, queries_tried


# ── FORMAT-ONLY FALLBACK (no KB hits or timed out) ────────────────────────────

def _format_context_from_outline(state: SOPState) -> Dict[str, Any]:
    """
    Build kb_format_context either from the planning outline (preferred)
    or a canonical 8-section SOP skeleton.
    """
    if getattr(state, "outline", None) and getattr(state.outline, "sections", None):
        section_titles = [{"number": s.number, "title": s.title} for s in state.outline.sections]
        return {
            "section_titles": section_titles,
            "numbering_style": "decimal with one dot (e.g., 1.0, 2.0, 3.0...)",
            "table_sections": [],
            "subsection_sections": [
                st["number"] for st in section_titles
                if st["title"].upper() in ("PROCEDURE", "RESPONSIBILITIES")
            ],
            "prose_sections": [
                st["number"] for st in section_titles
                if st["title"].upper() in ("PURPOSE", "SCOPE", "DEFINITIONS", "REFERENCES", "REVISION HISTORY")
            ],
            "writing_style": "imperative, concise",
            "special_elements": [],
            "section_count": len(section_titles),
            "banned_elements": []
        }

    # Canonical 8-section fallback
    default_titles = [
        {"number": "1.0", "title": "PURPOSE"},
        {"number": "2.0", "title": "SCOPE"},
        {"number": "3.0", "title": "RESPONSIBILITIES"},
        {"number": "4.0", "title": "DEFINITIONS"},
        {"number": "5.0", "title": "MATERIALS"},
        {"number": "6.0", "title": "PROCEDURE"},
        {"number": "7.0", "title": "REFERENCES"},
        {"number": "8.0", "title": "REVISION HISTORY"},
    ]
    return {
        "section_titles": default_titles,
        "numbering_style": "decimal with one dot (e.g., 1.0, 2.0, 3.0...)",
        "table_sections": [],
        "subsection_sections": ["6.0", "3.0"],
        "prose_sections": ["1.0", "2.0", "4.0", "7.0", "8.0", "5.0"],
        "writing_style": "imperative, concise",
        "special_elements": [],
        "section_count": 8,
        "banned_elements": []
    }


def _format_only_findings(state: SOPState) -> ResearchFindings:
    """Return ResearchFindings with empty content lists and a populated kb_format_context."""
    fmt = _format_context_from_outline(state)
    findings = ResearchFindings(
        similar_sops=[],
        compliance_requirements=[],
        best_practices=[],
        sources=[],
        kb_format_context=fmt,
    )
    return findings


# ── DOMAIN HELPERS ─────────────────────────────────────────────────────────────

def get_compliance_requirements(industry: str, topic: str) -> List[str]:
    compliance_map: Dict[str, List[str]] = {
        "Manufacturing":               ["OSHA 1910", "ISO 9001"],
        "Healthcare":                  ["HIPAA", "FDA 21 CFR Part 11"],
        "Laboratory":                  ["CLIA", "CAP Standards"],
        "Energy":                      ["OSHA PSM 1910.119", "API RP 754"],
        "Information Technology (IT)": ["ISO/IEC 27001", "NIST SP 800-53", "General Safety"],
    }
    return compliance_map.get(industry, ["General Safety"])


# ── LLM SYNTHESIS ──────────────────────────────────────────────────────────────

async def _synthesize_findings(state: SOPState, kb_docs: List[Dict[str, Any]]) -> ResearchFindings:
    """
    Use Claude to synthesise structured ResearchFindings from the raw KB chunks.
    Runs with a smaller token cap and no doubling for bounded latency.
    """
    kb_context_lines: List[str] = []
    for i, doc in enumerate(kb_docs[:15]):
        content = (doc.get("content") or "").strip()
        if not content:
            continue
        score  = float(doc.get("score", 0.0))
        source = doc.get("source", "Unknown")
        kb_context_lines.append(
            f"[{i+1}] score={score:.3f} | source={source}\n"
            f"  {_truncate(content, 700)}"
        )
    kb_context = "\n\n".join(kb_context_lines) or "(no KB results)"

    compliance     = get_compliance_requirements(state.industry, state.topic)
    compliance_str = ", ".join(compliance)
    model_id       = _get_model_id("MODEL_RESEARCH")

    user_prompt = (
        "Analyse the Knowledge Base extracts below and return ONLY a JSON object "
        "matching the provided schema.\n\n"
        f"TOPIC:               {state.topic}\n"
        f"INDUSTRY:            {state.industry}\n"
        f"TARGET AUDIENCE:     {state.target_audience}\n"
        f"ADDITIONAL REQs:     {', '.join(state.requirements or [])}\n\n"
        f"COMPLIANCE BASELINE: {compliance_str}\n\n"
        f"KNOWLEDGE BASE EXTRACTS:\n{kb_context}\n\n"
        "PART A — CONTENT EXTRACTION:\n"
        "1. Populate 'similar_sops' with the most relevant KB snippets, sources, and scores.\n"
        "2. List actionable 'best_practices' grounded in the KB content.\n"
        "3. Enumerate 'compliance_requirements' (augment the baseline from KB if possible).\n"
        "4. Include a flat 'sources' list.\n"
        "5. For 'section_insights': map each extracted fact to the SOP section number "
        "   where it belongs (use numbers from the KB documents themselves).\n\n"
        "PART B — FORMAT EXTRACTION:\n"
        "6. Carefully examine the KB extracts and populate 'kb_format_context' with the "
        "   formatting conventions you observe...\n"
        "JSON only. No markdown. No commentary."
    )

    def _invoke() -> Dict[str, Any]:
        client = boto3.client("bedrock-runtime", region_name=_REGION)
        return _invoke_model_json(
            client=client,
            model_id=model_id,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=_RESEARCH_FINDINGS_SCHEMA,
            initial_max_tokens=_RESEARCH_MAX_TOKENS,
            max_attempts=_RESEARCH_MAX_ATTEMPTS,
        )

    data = await asyncio.to_thread(_invoke)
    return ResearchFindings(**data)


async def _extract_kb_format_context_only(kb_docs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Secondary pass (used only when the main synthesis produced a null format context).
    """
    model_id = _get_model_id("MODEL_RESEARCH")

    kb_context_lines: List[str] = []
    for i, doc in enumerate(kb_docs[:10]):
        content = (doc.get("content") or "").strip()
        if not content:
            continue
        kb_context_lines.append(f"[{i+1}] {_truncate(content, 500)}")
    kb_context = "\n\n".join(kb_context_lines)
    if not kb_context:
        return None

    format_prompt = (
        "You are analysing Knowledge Base SOP document chunks to extract their "
        "formatting conventions. Return ONLY a JSON object with this exact shape..."
    )

    # Bedrock‑safe schema for format-only extraction (no unions/defaults/cardinality)
    _FORMAT_ONLY_SCHEMA: Dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "section_titles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "number": {"type": "string"},
                        "title":  {"type": "string"}
                    },
                    "required": ["number", "title"]
                }
            },
            "numbering_style": {"type": "string"},
            "table_sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "number":  {"type": "string"},
                        "columns": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["number", "columns"]
                }
            },
            "subsection_sections": {"type": "array", "items": {"type": "string"}},
            "prose_sections":      {"type": "array", "items": {"type": "string"}},
            "writing_style":       {"type": "string"},
            "special_elements":    {"type": "array", "items": {"type": "string"}},
            "section_count":       {"type": "number"},
            "banned_elements":     {"type": "array", "items": {"type": "string"}}
        },
        "required": ["section_titles"]
    }

    def _invoke() -> Dict[str, Any]:
        client = boto3.client("bedrock-runtime", region_name=_REGION)
        return _invoke_model_json(
            client=client,
            model_id=model_id,
            system_prompt=(
                "You extract SOP formatting conventions from document chunks. "
                "Return ONLY valid JSON — no markdown, no commentary."
            ),
            user_prompt=format_prompt,
            schema=_FORMAT_ONLY_SCHEMA,
            initial_max_tokens=min(_RESEARCH_MAX_TOKENS, 1024),
            max_attempts=1,
        )

    try:
        return await asyncio.to_thread(_invoke)
    except Exception as e:
        logger.warning("kb_format_context fallback extraction failed: %s", e)
    return None


# ── STRANDS TOOL ───────────────────────────────────────────────────────────────

@tool
async def run_research(prompt: str) -> str:
    """
    Execute the SOP research step.

    Behavior:
      • Try up to _RESEARCH_MAX_ROUNDS of KB retrieval with timeouts.
      • If 0 hits (or timeout), return format-only findings immediately.
      • Otherwise, run (bounded) LLM synthesis; if format ctx is still null,
        run format-only extraction pass.
    """
    logger.info(">>> run_research | prompt: %.160s", (prompt or ""))

    m = re.search(r"workflow_id::([^\s\|]+)", prompt or "")
    workflow_id = m.group(1) if m else ""
    if not workflow_id:
        raise ValueError(
            "Missing workflow_id in prompt. Expected 'workflow_id::<id>' in the message."
        )

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = (
            f"ERROR: no state found for workflow_id='{workflow_id}' "
            f"| store keys: {list(STATE_STORE.keys())}"
        )
        logger.error(msg)
        return msg

    state.research_complete = False
    logger.info(
        "Research | topic='%s' industry='%s' audience='%s'",
        state.topic, state.industry, state.target_audience
    )

    try:
        if not _KB_ID:
            raise RuntimeError(
                "KNOWLEDGE_BASE_ID environment variable is not set. "
                "Set it to your Bedrock Knowledge Base ID before running."
            )

        # ── Step 1: Time-bounded KB retrieval ───────────────────────────
        kb_docs, per_query_counts, queries_tried = await _try_kb_hits_timeboxed(state)
        state.kb_hits = len(kb_docs)

        if kb_docs:
            logger.info(
                "KB retrieval done — hits=%d | queries_tried=%d",
                state.kb_hits, len(queries_tried)
            )
            for q in queries_tried[:10]:
                logger.debug("  query='%.110s' → %d hits", q, per_query_counts.get(q, 0))
        else:
            logger.warning(
                "No KB hits within configured limits (rounds=%d, round_timeout=%.1fs, overall_timeout=%.1fs). "
                "Proceeding with format-only findings.",
                _RESEARCH_MAX_ROUNDS, _RESEARCH_ROUND_TIMEOUT_SEC, _RESEARCH_TIMEOUT_SEC
            )
            findings = _format_only_findings(state)
            state.research          = findings
            state.kb_format_context = findings.kb_format_context
            state.status            = WorkflowStatus.RESEARCHED
            state.current_node      = "research"
            state.research_complete = True
            state.increment_tokens(250)
            STATE_STORE[workflow_id] = state

            return (
                f"workflow_id::{workflow_id} | "
                f"Research complete (format-only): kb_hits=0, format_context=yes"
            )

        # ── Step 2: Synthesis (bounded) or raw-chunk mode ───────────────
        if _RESEARCH_DISABLE_LLM:
            logger.info("RESEARCH_DISABLE_LLM=1 — skipping Claude synthesis")
            findings = ResearchFindings(
                similar_sops=[
                    {
                        "snippet": (d.get("content") or "")[:600],
                        "source":  d.get("source", ""),
                        "score":   d.get("score", 0.0),
                    }
                    for d in kb_docs
                ],
                compliance_requirements=get_compliance_requirements(state.industry, state.topic),
                best_practices=[],
                sources=[d.get("source", "") for d in kb_docs],
                kb_format_context=None,
            )
        else:
            findings = await _synthesize_findings(state, kb_docs)

        # ── Step 3: Guarantee kb_format_context ─────────────────────────
        if findings.kb_format_context:
            logger.info(
                "kb_format_context extracted | sections=%d | style=%s",
                len(findings.kb_format_context.get("section_titles") or []),
                findings.kb_format_context.get("writing_style", "unknown"),
            )
        else:
            logger.warning(
                "kb_format_context was null after synthesis. "
                "Running dedicated format-extraction pass..."
            )
            fmt_ctx = await _extract_kb_format_context_only(kb_docs)
            if fmt_ctx:
                findings = findings.model_copy(update={"kb_format_context": fmt_ctx})
                logger.info(
                    "kb_format_context populated via fallback extraction | sections=%d",
                    len(fmt_ctx.get("section_titles") or []),
                )
            else:
                # Final safety: produce minimal format rather than continuing without it.
                findings = findings.model_copy(update={"kb_format_context": _format_context_from_outline(state)})
                logger.error(
                    "Format-extraction pass failed; using outline/default-based format context."
                )

        # ── Step 4: Write to shared state ───────────────────────────────
        state.research          = findings
        state.status            = WorkflowStatus.RESEARCHED
        state.current_node      = "research"
        state.research_complete = True
        state.increment_tokens(1200)
        if findings.kb_format_context:
            state.kb_format_context = findings.kb_format_context
        STATE_STORE[workflow_id] = state

        return (
            f"workflow_id::{workflow_id} | "
            f"Research complete: kb_hits={state.kb_hits}, "
            f"{len(findings.similar_sops)} similar SOPs, "
            f"{len(findings.compliance_requirements)} compliance requirements, "
            f"format_context={'yes' if state.kb_format_context else 'no'}"
        )

    except Exception as e:
        logger.exception("Research FAILED for workflow_id=%s", workflow_id)
        state.add_error(f"Research failed: {str(e)}")
        state.status            = WorkflowStatus.FAILED
        state.research_complete = False
        STATE_STORE[workflow_id] = state
        return f"workflow_id::{workflow_id} | Research FAILED: {e}"


# ── NODE AGENT ─────────────────────────────────────────────────────────────────

research_agent = Agent(
    name="ResearchNode",
    model=BedrockModel(model_id=_get_model_id("MODEL_RESEARCH")),
    system_prompt=(
        "You are the research node in an SOP generation pipeline. "
        "If and only if the incoming message contains the token 'workflow_id::', "
        "IMMEDIATELY call the run_research tool with the full message as the prompt argument. "
        "Otherwise, DO NOT call any tools and simply return the string 'noop'. "
        "Do not add any commentary."
    ),
    tools=[run_research],
)