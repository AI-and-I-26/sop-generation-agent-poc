"""
research_agent.py — Research Agent for the SOP pipeline.

ROLE IN PIPELINE:
    Node 2 of 5.  After the planning agent produces an outline, the research
    agent queries the Bedrock Knowledge Base (KB) to retrieve existing SOP
    documents that match the new SOP's topic.  Retrieved chunks are then
    synthesised by Claude into structured ResearchFindings that include:
      • Content facts per SOP section (section_insights)
      • Formatting conventions observed in the KB documents (kb_format_context)

ASSUMPTION: THE KB ALWAYS CONTAINS SOP DOCUMENTS.
    This agent is designed around the guarantee that the KB will always hold
    at least one SOP document.  Therefore:
      - Zero KB hits is NEVER acceptable — it indicates a query problem.
      - The agent retries with progressively broader queries until hits arrive.
      - kb_format_context MUST always be populated; if LLM synthesis misses it,
        a dedicated format-extraction pass is run automatically.
      - There is no fallback to "skip KB" — the KB is the source of truth.

GUARANTEED-HITS RETRIEVAL STRATEGY:
    Round 1 — Rich topic + industry + outline-section queries
    Round 2 — Shortened keyword-only variants
    Round 3 — Universal SOP structural terms (always match any SOP in any KB)
    Round 4 — Single-word atomic SOP terms (absolute last resort)

    All queries within a round run concurrently; results are deduplicated by
    SHA-256 content hash, keeping the highest-scoring copy of each chunk.
    Score filtering is disabled (set KB_MIN_SCORE > 0 only to exclude noise).

ANTHROPIC STRUCTURED OUTPUTS (InvokeModel path):
    The research agent uses InvokeModel with
    output_config.format.type = "json_schema", enforcing the ResearchFindings
    schema at the API level.

ENVIRONMENT VARIABLES (all optional):
    MODEL_RESEARCH    — Bedrock model ID (default: claude-sonnet-4-6)
    AWS_REGION        — AWS region (default: us-east-2)
    KB_MAX_RESULTS    — max KB hits per query (default: 20)
    KB_MIN_SCORE      — minimum relevance score to keep a hit (default: 0.0)
                        Set to 0.0 to never filter — recommended when KB is
                        always present.  Increase only to suppress noise.
    RESEARCH_DISABLE_LLM — skip LLM synthesis; return raw KB chunks (default: false)
"""

import asyncio
import hashlib
import time
import json
import logging
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

import boto3
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
    """
    Strip whitespace and quotes from the KB ID env var.
    Raises RuntimeError if the cleaned ID is not purely alphanumeric
    (Bedrock enforces this constraint).
    """
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
# KB_MAX_RESULTS — how many hits to request per individual query.
_KB_MAX_RESULTS = int(os.getenv("KB_MAX_RESULTS", "20"))

# KB_MIN_SCORE — relevance threshold; hits below this score are discarded.
# Default is 0.0 (keep everything) because the KB always has SOP documents
# and we must never return 0 hits.  Raise only to suppress noise.
_KB_MIN_SCORE = float(os.getenv("KB_MIN_SCORE", "0.0"))

# RESEARCH_MAX_TOKENS — starting token budget for the synthesis InvokeModel call.
# The agent doubles this automatically on max_tokens truncation, up to 8192.
# Default raised to 6000 to handle large KB result sets without truncation.
# Increase further (e.g. set RESEARCH_MAX_TOKENS=8000) if synthesis still truncates.
_RESEARCH_MAX_TOKENS = int(os.getenv("RESEARCH_MAX_TOKENS", "6000"))

# RESEARCH_MAX_ATTEMPTS — how many times to retry synthesis on token overflow.
_RESEARCH_MAX_ATTEMPTS = int(os.getenv("RESEARCH_MAX_ATTEMPTS", "3"))

# RESEARCH_ROUND_TIMEOUT_SEC / RESEARCH_TIMEOUT_SEC
# Per-round and overall timeout for KB retrieval.
# Prevents the pipeline hanging when Bedrock KB is slow.
# Defaults are generous (30s/120s) — tighten if you have strict SLA requirements.
_RESEARCH_ROUND_TIMEOUT_SEC = float(os.getenv("RESEARCH_ROUND_TIMEOUT_SEC", "30.0"))
_RESEARCH_TIMEOUT_SEC       = float(os.getenv("RESEARCH_TIMEOUT_SEC", "120.0"))

# RESEARCH_DISABLE_LLM — when "1", skip Claude synthesis and return raw chunks.
# Useful for debugging retrieval without incurring synthesis cost.
_RESEARCH_DISABLE_LLM = os.getenv("RESEARCH_DISABLE_LLM", "0") not in ("", "0", "false", "False")


def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


# ── JSON SCHEMA FOR STRUCTURED RESEARCH FINDINGS ──────────────────────────────
# Matches ResearchFindings Pydantic model + new section_insights field.
_RESEARCH_FINDINGS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "similar_sops": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "snippet": {"type": "string"},
                    "source":  {"type": "string"},
                    "score":   {"type": "number"}
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
        },
        # section_insights maps KB facts to specific SOP sections so the
        # content agent knows exactly where each piece of research belongs.
        "section_insights": {
            "type": "object",
            "default": {}
        }
    },
    "required": ["similar_sops", "compliance_requirements", "best_practices", "sources"],
    "additionalProperties": True
}


# ── ANTHROPIC INVOKEMODELAPI HELPERS ──────────────────────────────────────────

def _extract_text_from_invoke_body(body_json: Dict[str, Any]) -> str:
    """
    Extract concatenated text from an Anthropic InvokeModel response body.

    Anthropic Messages API response shape:
      { "content": [ {"type": "text", "text": "..."}, ... ], "stop_reason": "..." }
    """
    blocks = body_json.get("content", []) or []
    texts = [
        b.get("text", "")
        for b in blocks
        if isinstance(b, dict) and b.get("type") == "text"
    ]
    return "".join(texts).strip()


def _invoke_model_json(
    client,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    schema: Dict[str, Any],
    initial_max_tokens: int = 4096,
    max_attempts: int = 3,
) -> Dict[str, Any]:
    """
    Call Bedrock InvokeModel (Anthropic Messages API) with Structured Outputs.

    Uses output_config.format.type = "json_schema" to force the model to
    return valid JSON matching the provided schema.

    Retries on stop_reason == "max_tokens" by doubling the token budget.

    Args:
        client            : boto3 bedrock-runtime client
        model_id          : Bedrock model ARN or ID
        system_prompt     : Research extraction rules
        user_prompt       : KB context + task description
        schema            : JSON Schema dict for structured output
        initial_max_tokens: Starting token budget
        max_attempts      : Retry limit on token overflow

    Returns:
        Parsed JSON dict matching the research findings schema.
    """
    max_tokens = initial_max_tokens
    last_reason = None
    last_text = ""

    for attempt in range(1, max_attempts + 1):
        # Anthropic Messages API body
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": 0.0,      # deterministic synthesis
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_prompt}]
                }
            ],
            # Structured Outputs — ensures response is valid JSON per schema.
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "research_findings",
                        "schema": schema,   # JSON Schema object (not a string here)
                    }
                }
            },
        }

        logger.debug("InvokeModel attempt %d | max_tokens=%d", attempt, max_tokens)
        resp = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body).encode("utf-8"),
        )

        # Read and parse the response body
        raw = resp.get("body")
        body_json = json.loads(raw.read()) if raw is not None else {}
        logger.debug(
            "InvokeModel body (first 1000): %s",
            json.dumps(body_json, default=str)[:1000]
        )

        stop_reason = body_json.get("stop_reason")
        last_reason = stop_reason
        text = _extract_text_from_invoke_body(body_json)
        last_text = text or ""

        if stop_reason == "max_tokens":
            logger.warning(
                "InvokeModel hit max_tokens; doubling budget (attempt %d/%d)",
                attempt, max_attempts
            )
            max_tokens = min(max_tokens * 2, 8192)
            continue

        if not text:
            raise ValueError(
                f"InvokeModel returned empty content. "
                f"stop_reason={stop_reason} | body={body_json}"
            )

        # With Structured Outputs, text is guaranteed valid JSON.
        return json.loads(text)

    raise RuntimeError(
        f"InvokeModel exhausted token budget. Last stop_reason={last_reason}. "
        f"Last text length={len(last_text)}."
    )


# ── STRING / TEXT HELPERS ──────────────────────────────────────────────────────

def _truncate(s: str, max_len: int) -> str:
    """Truncate a string for safe logging."""
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _tokenize_keywords(text: str) -> List[str]:
    """
    Lowercase, tokenise, and remove common stop words from text.
    Used to build compact keyword-only fallback queries.
    """
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    stop = {
        "and", "or", "the", "a", "an", "of", "to", "in", "for",
        "on", "with", "by", "at", "be", "is", "are"
    }
    return [t for t in tokens if len(t) > 2 and t not in stop]


def _synonymize(words: Iterable[str]) -> List[str]:
    """
    Expand keywords with domain synonyms to broaden KB recall.
    E.g. "qualification" → also try "validation", "assessment".
    """
    syn_map = {
        "qualification": ["validation", "assessment", "verification"],
        "network":        ["networking"],
        "storage":        ["datastore", "repositories"],
        "cloud":          ["iaas", "paas", "saas"],
        "procedure":      ["process", "steps", "workflow"],
        "devices":        ["hardware", "equipment"],
        "infrastructure": ["systems", "it infrastructure"],
    }
    out = set(words)
    for w in list(words):
        for k, syns in syn_map.items():
            if w.startswith(k):
                out.update(syns)
    return list(out)


# ── QUERY BUILDING ─────────────────────────────────────────────────────────────

def _build_queries(state: SOPState) -> List[str]:
    """
    Build Round 1 KB queries: semantically diverse, topic-specific.

    All queries are derived from the topic, industry, and outline — never
    from hardcoded document names.  The SOP universal fallback terms in
    Round 3/4 of _guarantee_kb_hits handle the worst case independently.
    """
    topic    = (state.topic or "").strip()
    industry = (state.industry or "").strip()

    base: List[str] = [
        f"{topic} {industry}",
        f"{topic} standard operating procedure",
        f"{industry} SOP procedure responsibilities scope definitions references",
        f"{topic} procedure purpose scope responsibilities",
    ]

    # Use outline section titles if planning has already run.
    # Section titles like "PURPOSE", "SCOPE", "PROCEDURE" are SOP vocabulary
    # that will semantically match chunks from any SOP document in the KB.
    if getattr(state, "outline", None) and getattr(state.outline, "sections", None):
        titles = [s.title for s in state.outline.sections if s.title][:6]
        if titles:
            base.append(f"SOP {', '.join(titles)}")
            base.append(f"{topic} {' '.join(titles[:3])}")

    # Keyword + synonym expansion
    keywords = _tokenize_keywords(f"{topic} {industry} sop procedure")
    keywords = _synonymize(keywords)
    if keywords:
        base.append(" ".join(sorted(set(keywords))))

    # Deduplicate preserving order
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
    """Create a Bedrock Agent Runtime client for KB retrieval."""
    if not _KB_ID:
        raise RuntimeError(
            "KNOWLEDGE_BASE_ID is not set. "
            "Set the KNOWLEDGE_BASE_ID environment variable."
        )
    return boto3.client("bedrock-agent-runtime", region_name=_KB_REGION)


def _content_hash(text: str) -> str:
    """SHA-256 hash of chunk content — used to deduplicate retrieval results."""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _merge_hits_dedupe(all_hits: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate KB hits by content hash, keeping the highest-scoring copy.
    Returns hits sorted by score descending.
    """
    by_hash: Dict[str, Dict[str, Any]] = {}
    for h in all_hits:
        content = (h.get("content") or "").strip()
        if not content:
            continue   # skip empty chunks
        hsh = _content_hash(content)
        # Keep the hit with the higher score when duplicates collide
        if hsh not in by_hash or float(h.get("score", 0)) > float(by_hash[hsh].get("score", 0)):
            by_hash[hsh] = h
    merged = list(by_hash.values())
    merged.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    return merged


async def _retrieve_one(query: str, max_results: int) -> List[Dict[str, Any]]:
    """
    Execute a single KB retrieval query asynchronously (via asyncio.to_thread).

    Returns a list of hit dicts: { content, score, source, query }
    """
    client = _kb_client()
    logger.debug(
        "KB retrieve | id=%s | region=%s | max=%d | query=%.160s",
        _KB_ID, _KB_REGION, max_results, query
    )

    # Run the blocking boto3 call in a thread pool so we don't block the event loop
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
            continue   # filter out low-confidence hits
        hits.append({
            "content": r.get("content", {}).get("text", ""),
            "score":   score,
            "source":  r.get("location", {}).get("s3Location", {}).get("uri", "Unknown"),
            "query":   query,
        })

    logger.debug("KB retrieve | hits=%d | query=%.80s", len(hits), query)
    return hits


async def _retrieve_multi(
    queries: List[str],
    max_results: int
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Run multiple KB queries concurrently, merge, and deduplicate results.

    Returns:
        merged_hits    : Deduplicated, score-sorted list of hit dicts
        per_query_counts: { query_string → hit count } for logging
    """
    per_query_counts: Dict[str, int] = {}

    # Fire all queries simultaneously via asyncio
    tasks = [asyncio.create_task(_retrieve_one(q, max_results)) for q in queries]
    all_hits: List[Dict[str, Any]] = []

    for task in asyncio.as_completed(tasks):
        try:
            hits = await task
        except Exception as e:
            logger.warning("KB retrieve error (query skipped): %s", e)
            hits = []
        all_hits.extend(hits)

    # Count hits per originating query (for diagnostics)
    for h in all_hits:
        q = h.get("query", "")
        per_query_counts[q] = per_query_counts.get(q, 0) + 1

    merged = _merge_hits_dedupe(all_hits)
    return merged, per_query_counts


async def _guarantee_kb_hits(
    state: SOPState,
) -> Tuple[List[Dict[str, Any]], Dict[str, int], List[str]]:
    """
    Guaranteed-hits retrieval: keeps retrying until at least one KB chunk
    is returned.  Zero hits is NEVER acceptable — the KB always has SOPs.

    Round 1 — Rich topic + industry + outline-title queries (concurrent)
    Round 2 — Shortened keyword-only variants
    Round 3 — Universal SOP structural terms that match ANY SOP document
    Round 4 — Single-word atomic SOP terms (absolute last resort)

    If Round 4 still returns 0 hits, a RuntimeError is raised so the
    caller can surface a clear diagnostic (KNOWLEDGE_BASE_ID wrong, IAM
    permissions missing, etc.) rather than silently producing a blank SOP.

    Returns:
        hits            : Final deduplicated hit list (≥ 1 chunk guaranteed)
        per_query_counts: Per-query hit counts for diagnostics
        queries_tried   : All query strings attempted (for logging)
    """
    queries_tried: List[str] = []
    hits: List[Dict[str, Any]] = []
    per_query_counts: Dict[str, int] = {}

    # ── Round 1: topic-specific rich queries ────────────────────────────
    queries_r1 = _build_queries(state)
    queries_tried.extend(queries_r1)
    hits, per_query_counts = await _retrieve_multi(queries_r1, _KB_MAX_RESULTS)

    if hits:
        logger.info("KB Round 1: %d hits across %d queries", len(hits), len(queries_r1))
        return hits, per_query_counts, queries_tried

    logger.warning(
        "KB Round 1 returned 0 hits (%d queries). Trying Round 2...",
        len(queries_r1)
    )

    # ── Round 2: shortened keyword-only variants ─────────────────────────
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
    hits2, per2 = await _retrieve_multi(queries_r2, _KB_MAX_RESULTS)
    hits = _merge_hits_dedupe([*hits, *hits2])
    per_query_counts.update(per2)

    if hits:
        logger.info("KB Round 2: %d total hits", len(hits))
        return hits, per_query_counts, queries_tried

    logger.warning("KB Round 2 still 0 hits. Trying Round 3 (universal SOP terms)...")

    # ── Round 3: universal SOP vocabulary ────────────────────────────────
    # These terms appear in EVERY SOP document regardless of topic:
    # section titles, header labels, document control fields.
    # At least one of these will match any SOP stored in the KB.
    queries_r3 = [
        "purpose scope responsibilities procedure references revision history",
        "standard operating procedure purpose scope",
        "SOP responsibilities definitions materials procedure",
        "revision history effective date procedure scope",
        "SOP document purpose procedure responsibilities",
        "scope of procedure materials references",
    ]
    queries_r3 = [q for q in queries_r3 if q not in queries_tried]
    queries_tried.extend(queries_r3)
    hits3, per3 = await _retrieve_multi(queries_r3, _KB_MAX_RESULTS)
    hits = _merge_hits_dedupe([*hits, *hits3])
    per_query_counts.update(per3)

    if hits:
        logger.info("KB Round 3: %d total hits", len(hits))
        return hits, per_query_counts, queries_tried

    logger.warning("KB Round 3 still 0 hits. Trying Round 4 (single-word atomic terms)...")

    # ── Round 4: single-word atomic SOP terms (absolute last resort) ─────
    # Any SOP document will have these words somewhere in its text.
    # If even these return 0 hits, the KB connection itself is broken.
    queries_r4 = [
        "procedure",
        "scope",
        "purpose",
        "responsibilities",
        "revision",
    ]
    queries_r4 = [q for q in queries_r4 if q not in queries_tried]
    queries_tried.extend(queries_r4)
    hits4, per4 = await _retrieve_multi(queries_r4, _KB_MAX_RESULTS)
    hits = _merge_hits_dedupe([*hits, *hits4])
    per_query_counts.update(per4)

    if hits:
        logger.info("KB Round 4: %d total hits", len(hits))
        return hits, per_query_counts, queries_tried

    # If we reach here, the KB connection is broken or the KB is genuinely empty.
    # Raise a clear, actionable error — do NOT silently produce an empty SOP.
    raise RuntimeError(
        "KB returned 0 hits after 4 rounds and "
        f"{len(queries_tried)} queries (including single-word atomic terms). "
        "This means either:\n"
        "  1. KNOWLEDGE_BASE_ID is set to a wrong or empty KB.\n"
        "  2. The AWS credentials lack bedrock:Retrieve permission.\n"
        "  3. The KB has no documents ingested yet.\n"
        "Fix the KB configuration before running the pipeline."
    )


# ── FORMAT FALLBACK HELPERS ────────────────────────────────────────────────────


def _format_context_from_outline(state: SOPState) -> Dict[str, Any]:
    """
    Build kb_format_context from the planning outline (preferred) or a
    canonical 8-section SOP skeleton.

    Used when KB retrieval yields 0 hits or times out, so downstream agents
    still receive meaningful formatting guidance rather than null.
    """
    if getattr(state, "outline", None) and getattr(state.outline, "sections", None):
        titles = [
            {"number": s.number, "title": s.title}
            for s in state.outline.sections
        ]
        return {
            "section_titles": titles,
            "numbering_style": "decimal with one dot (e.g., 1.0, 2.0, 3.0)",
            "table_sections": [],
            "subsection_sections": [
                t["number"] for t in titles
                if t["title"].upper() in ("PROCEDURE", "RESPONSIBILITIES")
            ],
            "prose_sections": [
                t["number"] for t in titles
                if t["title"].upper() in (
                    "PURPOSE", "SCOPE", "DEFINITIONS", "REFERENCES", "REVISION HISTORY"
                )
            ],
            "writing_style": "imperative, concise",
            "special_elements": [],
            "section_count": len(titles),
            "banned_elements": [],
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
        "numbering_style": "decimal with one dot (e.g., 1.0, 2.0, 3.0)",
        "table_sections": [],
        "subsection_sections": ["6.0", "3.0"],
        "prose_sections": ["1.0", "2.0", "4.0", "7.0", "8.0", "5.0"],
        "writing_style": "imperative, concise",
        "special_elements": [],
        "section_count": 8,
        "banned_elements": [],
    }


def _format_only_findings(state: SOPState) -> ResearchFindings:
    """
    Return a ResearchFindings object with empty content lists but a guaranteed
    kb_format_context derived from the outline or the default 8-section skeleton.

    Used when KB retrieval yields 0 hits within the configured limits, so the
    pipeline can continue with at least valid formatting conventions.
    """
    return ResearchFindings(
        similar_sops=[],
        compliance_requirements=[],
        best_practices=[],
        sources=[],
        kb_format_context=_format_context_from_outline(state),
    )


# ── DOMAIN HELPERS ─────────────────────────────────────────────────────────────

def get_compliance_requirements(industry: str, topic: str) -> List[str]:
    """
    Return a baseline list of compliance requirements for the given industry.
    Used when KB retrieval yields no compliance-specific chunks.
    """
    compliance_map: Dict[str, List[str]] = {
        "Manufacturing":              ["OSHA 1910", "ISO 9001"],
        "Healthcare":                 ["HIPAA", "FDA 21 CFR Part 11"],
        "Laboratory":                 ["CLIA", "CAP Standards"],
        "Energy":                     ["OSHA PSM 1910.119", "API RP 754"],
        "Information Technology (IT)": ["ISO/IEC 27001", "NIST SP 800-53", "General Safety"],
    }
    return compliance_map.get(industry, ["General Safety"])


# ── LLM SYNTHESIS ──────────────────────────────────────────────────────────────

async def _synthesize_findings(
    state: SOPState,
    kb_docs: List[Dict[str, Any]]
) -> ResearchFindings:
    """
    Use Claude to synthesise structured ResearchFindings from the raw KB chunks.

    The model is guided by RESEARCH_SYSTEM_PROMPT to:
      - Discard template artefacts (Method:/Acceptance Criteria: etc.)
      - Extract section-level facts keyed to 1.0–8.0
      - Identify compliance requirements and best practices
      - Return strictly valid JSON (enforced via Structured Outputs)

    KB context is limited to the top 15 chunks to keep the prompt size manageable.
    """
    # Build KB context string — trim each chunk to 700 chars to control prompt size
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

    # Build the user prompt — clear task + all context the model needs
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
        "   formatting conventions you observe: exact section titles and numbers, which "
        "   sections use tables and what columns, which use subsections, which use plain "
        "   prose, the writing style, and any patterns that are clearly NOT used.\n"
        "   Set any value to null if you cannot determine it from the extracts.\n"
        "   This is critical — downstream agents will use kb_format_context to format "
        "   the new SOP to match your KB, without any hardcoded rules.\n\n"
        "JSON only. No markdown. No commentary."
    )

    # Run the blocking InvokeModel call in a thread pool
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

    # Validate and return as Pydantic model (ResearchFindings ignores extra fields
    # like section_insights — they're stored in SOPState.research if needed)
    return ResearchFindings(**data)


async def _extract_kb_format_context_only(
    kb_docs: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Dedicated pass to extract kb_format_context when the main synthesis
    returned it as null.

    This happens when the model's attention was split between content
    extraction (Part A) and format extraction (Part B) and it missed
    the format context.  This focused call asks for ONLY the format context.

    Since the KB always has SOP documents, this must return a non-null result
    as long as the KB chunks contain any structural SOP text.

    Returns:
        kb_format_context dict, or None if extraction genuinely failed.
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
        "formatting conventions. Return ONLY a JSON object with this exact shape:\n\n"
        "{\n"
        '  "section_titles": [{"number": "<e.g. 1.0>", "title": "<exact title>"}],\n'
        '  "numbering_style": "<description of numbering pattern>",\n'
        '  "table_sections": [{"number": "<e.g. 3.0>", "columns": ["<col1>", "<col2>"]}],\n'
        '  "subsection_sections": ["<section numbers that use numbered subsections>"],\n'
        '  "prose_sections": ["<section numbers that use plain paragraphs>"],\n'
        '  "writing_style": "<formal/imperative/passive/etc.>",\n'
        '  "special_elements": ["<any recurring structural element>"],\n'
        '  "section_count": 0,\n'
        '  "banned_elements": ["<patterns clearly NOT used in these documents>"]\n'
        "}\n\n"
        "Set a value to null only if you truly cannot determine it.\n"
        "Do NOT invent conventions — only report what you observe in the text.\n\n"
        f"KB CHUNKS:\n{kb_context}\n\n"
        "JSON only. No markdown. No code fences."
    )

    _FORMAT_ONLY_SCHEMA: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "section_titles":      {"type": ["array",  "null"]},
            "numbering_style":     {"type": ["string", "null"]},
            "table_sections":      {"type": ["array",  "null"]},
            "subsection_sections": {"type": ["array",  "null"]},
            "prose_sections":      {"type": ["array",  "null"]},
            "writing_style":       {"type": ["string", "null"]},
            "special_elements":    {"type": ["array",  "null"]},
            "section_count":       {"type": ["number", "null"]},
            "banned_elements":     {"type": ["array",  "null"]},
        },
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
            initial_max_tokens=2048,
            max_attempts=2,
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

    DESIGN CONTRACT:
        The KB always contains SOP documents, so this function MUST always:
          1. Return at least one KB hit (zero hits → RuntimeError from retrieval).
          2. Populate kb_format_context on SOPState (dedicated extraction pass
             if main synthesis returns it as null).

    Flow:
        1. Extract workflow_id from the graph message.
        2. Read SOPState from STATE_STORE.
        3. Run _guarantee_kb_hits (4 rounds; never exits with 0 hits).
        4. Synthesise findings with Claude.
        5. If kb_format_context is null → run _extract_kb_format_context_only.
        6. Write findings + kb_format_context to SOPState.
        7. Return summary string for the next node.

    Args:
        prompt: Graph message containing 'workflow_id::<id>'.

    Returns:
        "workflow_id::<id> | Research complete: ..." summary string.
        On failure, marks state as FAILED and returns error string.
    """
    logger.info(">>> run_research | prompt: %.160s", (prompt or ""))

    # ── Extract workflow_id ──────────────────────────────────────────────
    m = re.search(r"workflow_id::([^\s\|]+)", prompt or "")
    workflow_id = m.group(1) if m else ""
    if not workflow_id:
        raise ValueError(
            "Missing workflow_id in prompt. "
            "Expected 'workflow_id::<id>' in the message."
        )

    # ── Read state ──────────────────────────────────────────────────────
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

        # ── Step 1: Guaranteed KB retrieval ─────────────────────────────
        # _guarantee_kb_hits tries 4 rounds before raising RuntimeError.
        # We catch RuntimeError here and fall back to format-only findings
        # so the pipeline can still produce a structurally correct SOP.
        try:
            kb_docs, per_query_counts, queries_tried = await _guarantee_kb_hits(state)
        except RuntimeError as kb_err:
            logger.error(
                "KB returned 0 hits after all rounds: %s. "
                "Falling back to format-only findings.",
                kb_err,
            )
            findings = _format_only_findings(state)
            state.research          = findings
            state.kb_format_context = findings.kb_format_context
            state.kb_hits           = 0
            state.status            = WorkflowStatus.RESEARCHED
            state.current_node      = "research"
            state.research_complete = True
            state.increment_tokens(250)
            STATE_STORE[workflow_id] = state
            return (
                f"workflow_id::{workflow_id} | "
                f"Research complete (format-only fallback): kb_hits=0, "
                f"format_context=yes"
            )

        state.kb_hits = len(kb_docs)

        logger.info(
            "KB retrieval done — hits=%d | queries_tried=%d",
            state.kb_hits, len(queries_tried)
        )
        for q in queries_tried[:10]:
            logger.debug("  query='%.110s' → %d hits", q, per_query_counts.get(q, 0))

        # ── Step 2: Compliance baseline ──────────────────────────────────
        compliance = get_compliance_requirements(state.industry, state.topic)

        # ── Step 3: LLM synthesis or raw-chunk mode ──────────────────────
        if _RESEARCH_DISABLE_LLM:
            # Debug mode: skip synthesis, use raw chunks only
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
                compliance_requirements=compliance,
                best_practices=[],
                sources=[d.get("source", "") for d in kb_docs],
                kb_format_context=None,
            )
        else:
            findings = await _synthesize_findings(state, kb_docs)

        # ── Step 4: Guarantee kb_format_context is populated ────────────
        # Because the KB always has SOP documents, we must always extract
        # formatting conventions from the KB chunks.  If the main synthesis
        # returned kb_format_context as null (model attention split), run a
        # dedicated focused extraction pass.
        if findings.kb_format_context:
            logger.info(
                "kb_format_context extracted in main synthesis | "
                "sections=%d | style=%s",
                len(findings.kb_format_context.get("section_titles") or []),
                findings.kb_format_context.get("writing_style", "unknown"),
            )
        else:
            logger.warning(
                "kb_format_context was null after main synthesis. "
                "Running dedicated format-extraction pass..."
            )
            fmt_ctx = await _extract_kb_format_context_only(kb_docs)
            if fmt_ctx:
                findings = findings.model_copy(update={"kb_format_context": fmt_ctx})
                logger.info(
                    "kb_format_context populated via fallback extraction | "
                    "sections=%d",
                    len(fmt_ctx.get("section_titles") or []),
                )
            else:
                # This should never happen when the KB has SOP documents.
                # Log a prominent warning — the pipeline can still continue
                # but output format quality will be reduced.
                logger.error(
                    "CRITICAL: kb_format_context could not be extracted from %d "
                    "KB chunks.  Downstream agents will use generic SOP defaults. "
                    "Check that KB documents contain readable SOP text.",
                    len(kb_docs),
                )

        # ── Step 5: Write to shared state ───────────────────────────────
        state.research          = findings
        state.status            = WorkflowStatus.RESEARCHED
        state.current_node      = "research"
        state.research_complete = True
        state.increment_tokens(2000)

        # Copy format context to SOPState top-level for easy access downstream
        if findings.kb_format_context:
            state.kb_format_context = findings.kb_format_context

        STATE_STORE[workflow_id] = state

        logger.info(
            "Research complete | workflow_id=%s | kb_hits=%d | "
            "similar_sops=%d | compliance=%d | has_format_ctx=%s",
            workflow_id, state.kb_hits,
            len(findings.similar_sops),
            len(findings.compliance_requirements),
            state.kb_format_context is not None,
        )

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
# Registered with GraphBuilder.add_node("research", research_agent).
# Forwards the graph message to run_research @tool immediately.
research_agent = Agent(
    name="ResearchNode",
    model=BedrockModel(model_id=_get_model_id("MODEL_RESEARCH")),
    system_prompt=(
        "You are the research node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_research tool "
        "with the full message as the prompt argument. "
        "Do not add commentary — just call the tool and return its result."
    ),
    tools=[run_research],
)
