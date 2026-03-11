"""
content_agent.py — Content Agent for the SOP pipeline.

ROLE IN PIPELINE:
    Node 3 of 5. After research, this agent writes the actual SOP text —
    one section at a time — using the outline from the planning agent and
    the KB-derived facts from the research agent.

SECTION-BY-SECTION APPROACH:
    Generates each of the 8 canonical SOP sections as separate Bedrock calls
    (direct boto3). This avoids Strands Agent loop unrecoverable states on
    max_tokens, enables our own overflow retry logic, and keeps prompts small.

KB ALIGNMENT:
    Each section call includes:
      - kb_format_context : formatting conventions extracted from the KB
      - section_insights  : KB-derived facts for that specific section
      - compliance requirements and best practices from research

PATCHES INCLUDED:
    1) Direct Bedrock calls with stop_reason handling (no inner Strands Agent).
    2) Overflow-safe retry: on 'max_tokens' retry once in concise mode
       with fewer facts and a word-cap hint.
    3) kb_format_context compaction (trim long lists) to reduce prompt size.
    4) Per-section persistence to STATE_STORE to avoid losing prior work.
    5) Optional split of PROCEDURE (6.0) into two Bedrock calls when many
       subsections are present, then concatenated.
    6) Env-driven caps for per-section max_tokens, facts, cites, and split threshold.
"""

import json
import logging
import os
import re
from math import ceil
from typing import Any, Dict, List, Optional, Tuple, Iterable

import boto3
from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE
from src.prompts.system_prompts import CONTENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ── CONFIGURATION ──────────────────────────────────────────────────────────────

_DEFAULT_MODEL_ARN = (
    "arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")

# Env-driven caps (tune without code changes)
_CONTENT_MAX_TOKENS_PER_SECTION = int(os.getenv("CONTENT_MAX_TOKENS_PER_SECTION", "3000"))
_CONTENT_MAX_FACTS_PER_SECTION  = int(os.getenv("CONTENT_MAX_FACTS_PER_SECTION", "12"))
_CONTENT_MAX_CITES_PER_SECTION  = int(os.getenv("CONTENT_MAX_CITES_PER_SECTION", "12"))
_PROCEDURE_SPLIT_MIN_SUBSECTIONS = int(os.getenv("CONTENT_PROCEDURE_SPLIT_MIN_SUBSECTIONS", "6"))

# Log effective caps for visibility
logger.info(
    "Content caps | TOKENS/section=%d, FACTS/section=%d, CITES/section=%d, PROCEDURE_SPLIT_MIN=%d",
    _CONTENT_MAX_TOKENS_PER_SECTION, _CONTENT_MAX_FACTS_PER_SECTION,
    _CONTENT_MAX_CITES_PER_SECTION, _PROCEDURE_SPLIT_MIN_SUBSECTIONS
)

def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ARN)


# ── CANONICAL SECTION ORDER ────────────────────────────────────────────────────

KB_SECTIONS = [
    "PURPOSE",
    "SCOPE",
    "RESPONSIBILITIES",
    "DEFINITIONS / ABBREVIATIONS",
    "MATERIALS",
    "PROCEDURE",
    "REFERENCES",
    "REVISION HISTORY",
]

SECTION_NUMBER_MAP: Dict[str, str] = {
    "PURPOSE":                     "1.0",
    "SCOPE":                       "2.0",
    "RESPONSIBILITIES":            "3.0",
    "DEFINITIONS / ABBREVIATIONS": "4.0",
    "MATERIALS":                   "5.0",
    "PROCEDURE":                   "6.0",
    "REFERENCES":                  "7.0",
    "REVISION HISTORY":            "8.0",
}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _extract_text_from_bedrock_body(body_json: Dict[str, Any]) -> str:
    """
    Extract concatenated text from an Anthropic Messages response body.
    Shape:
      { "content": [ {"type": "text", "text": "..."}, ... ], "stop_reason": "..." }
    """
    blocks = body_json.get("content", []) or []
    texts = [
        b.get("text", "")
        for b in blocks
        if isinstance(b, dict) and b.get("type") == "text"
    ]
    return "".join(texts).strip()


def _invoke_bedrock_text(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    model_id: Optional[str] = None,
    temperature: float = 0.2,
    region: Optional[str] = None,
) -> Tuple[str, Optional[str]]:
    """
    Call Bedrock Anthropic Messages API directly and return (text, stop_reason).
    """
    _read_to = int(os.getenv("CONTENT_READ_TIMEOUT", "300"))
    from botocore.config import Config as _BotoCfg
    client = boto3.client(
        "bedrock-runtime",
        region_name=region or _REGION,
        config=_BotoCfg(
            read_timeout=_read_to,
            connect_timeout=10,
            retries={"max_attempts": 1, "mode": "standard"},
        ),
    )
    model = model_id or _get_model_id("MODEL_CONTENT")
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system_prompt,
        "messages": [{"role": "user", "content": [{"type": "text", "text": user_prompt}]}],
    }
    resp = client.invoke_model(
        modelId=model,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body).encode("utf-8"),
    )
    raw = resp.get("body")
    body_json = json.loads(raw.read()) if raw is not None else {}
    text = _extract_text_from_bedrock_body(body_json)
    stop_reason = body_json.get("stop_reason")
    return text, stop_reason


def _group_insights_by_section(section_insights: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[str]]]:
    """
    Convert array-of-objects into a dict keyed by section (e.g., "6.0") with merged facts/citations.
    Input item shape: { "section": "6.0", "facts": [..], "citations": [..] }
    Output: { "6.0": { "facts": [...], "citations": [...] }, ... }
    """
    grouped: Dict[str, Dict[str, List[str]]] = {}
    for item in section_insights or []:
        if not isinstance(item, dict):
            continue
        sec = str(item.get("section") or "").strip()
        if not sec:
            continue
        facts = [f for f in (item.get("facts") or []) if isinstance(f, str) and f.strip()]
        cites = [c for c in (item.get("citations") or []) if isinstance(c, str) and c.strip()]
        node = grouped.setdefault(sec, {"facts": [], "citations": []})
        # de-dup extend
        for f in facts:
            if f not in node["facts"]:
                node["facts"].append(f)
        for c in cites:
            if c not in node["citations"]:
                node["citations"].append(c)
    return grouped


def _pick_insights_for_section(
    grouped: Dict[str, Dict[str, List[str]]],
    sec_num: str,
    max_facts: int,
    max_cites: int,
) -> Dict[str, List[str]]:
    """
    Select compact insights for a target section number:
      - exact match (e.g., '6.0')
      - plus any nested subsections (e.g., '6.1', '6.2')
    Cap counts to keep the prompt small.
    """
    facts: List[str] = []
    cites: List[str] = []

    exact = grouped.get(sec_num)
    if exact:
        facts.extend(exact.get("facts", []))
        cites.extend(exact.get("citations", []))

    prefix = sec_num + "."
    for k, v in grouped.items():
        if k != sec_num and k.startswith(prefix):
            for f in v.get("facts", []):
                if f not in facts:
                    facts.append(f)
            for c in v.get("citations", []):
                if c not in cites:
                    cites.append(c)

    return {"facts": facts[:max_facts], "citations": cites[:max_cites]}


def _pick_insights_for_prefixes(
    grouped: Dict[str, Dict[str, List[str]]],
    prefixes: Iterable[str],
    max_facts: int,
    max_cites: int,
) -> Dict[str, List[str]]:
    """
    Select insights for a set of section number prefixes, e.g., {'6.1', '6.2', '6.3'}.
    """
    facts: List[str] = []
    cites: List[str] = []
    pfx_list = [p.strip() for p in prefixes if p and isinstance(p, str)]
    for k, v in grouped.items():
        for p in pfx_list:
            if k == p or k.startswith(p + "."):
                for f in v.get("facts", []):
                    if f not in facts:
                        facts.append(f)
                for c in v.get("citations", []):
                    if c not in cites:
                        cites.append(c)
                break
    return {"facts": facts[:max_facts], "citations": cites[:max_cites]}


def _outline_subsections_for(state: SOPState, sec_num: str) -> List[Tuple[str, str]]:
    """
    Return list of (number, title) for immediate subsections of a top-level section.
    """
    if not state or not state.outline or not getattr(state.outline, "sections", None):
        return []
    for s in state.outline.sections:
        if s.number == sec_num and getattr(s, "subsections", None):
            out: List[Tuple[str, str]] = []
            for sub in s.subsections:
                title = getattr(sub, "title", "")
                number = getattr(sub, "number", "")
                if number and title:
                    out.append((number, title))
            return out
    return []


def _format_subsections_lines(subs: List[Tuple[str, str]]) -> str:
    if not subs:
        return ""
    return "\n".join(f"  {n} {t}" for n, t in subs)


def _compact_kb_format_ctx(ctx: Dict[str, Any], max_titles: int = 8, max_tables: int = 3) -> Dict[str, Any]:
    """
    Compact large kb_format_context structures to reduce prompt size without losing signal.
    """
    if not isinstance(ctx, dict):
        return ctx
    c = dict(ctx)
    if isinstance(c.get("section_titles"), list):
        c["section_titles"] = c["section_titles"][:max_titles]
    if isinstance(c.get("table_sections"), list):
        c["table_sections"] = c["table_sections"][:max_tables]
    if isinstance(c.get("special_elements"), list):
        c["special_elements"] = c["special_elements"][:5]
    if isinstance(c.get("subsection_sections"), list):
        c["subsection_sections"] = c["subsection_sections"][:10]
    if isinstance(c.get("prose_sections"), list):
        c["prose_sections"] = c["prose_sections"][:10]
    return c


def _make_section_prompt(
    section_name: str,
    sec_num: str,
    state: SOPState,
    fmt_ctx: Dict[str, Any],
    facts: List[str],
    cites: List[str],
    compliance: List[str],
    best_practices: List[str],
    outline_subsections_text: str,
    concise_hint: bool = False,
) -> str:
    kb_format_ctx_str = json.dumps(fmt_ctx, indent=2) if fmt_ctx else "(no kb_format_context — use standard SOP formatting)"
    facts_s = json.dumps(facts, indent=2) if facts else "(no KB facts for this section)"
    cites_s = json.dumps(cites[:min(5, len(cites))], indent=2) if cites else "(no citations)"
    compliance_str  = ", ".join(compliance) if compliance else "None"
    practices_str   = "; ".join(best_practices[:5]) if best_practices else "None"

    parts: List[str] = [
        f"Section Number: {sec_num}",
        f"Section Title:  {section_name}",
        f"Topic:          {state.topic}",
        f"Industry:       {state.industry}",
        f"Audience:       {state.target_audience}",
        "",
    ]
    if outline_subsections_text:
        parts += ["Outline subsections for this section:", outline_subsections_text, ""]
    parts += [
        "KB FORMAT CONTEXT — follow these conventions exactly:",
        kb_format_ctx_str,
        "",
        "KB FACTS — ground all statements in these facts (do not invent):",
        facts_s,
        "",
        "KB CITATIONS (for provenance; do not include raw URIs in the prose):",
        cites_s,
        "",
        f"Compliance requirements to reflect: {compliance_str}",
        f"Best practices to reflect: {practices_str}",
        "",
        "TASK:",
        "Write the complete, publication-ready content for this SOP section.",
        "Use a concise, imperative style consistent with the KB format context.",
        "Do NOT output JSON or code fences; return plain prose only.",
    ]
    if concise_hint:
        parts += ["", "CONCISE MODE: Keep this section succinct (<= 700 words)."]
    return "\n".join(parts)


# ── SECTION GENERATOR (direct Bedrock) ─────────────────────────────────────────

def _generate_section_direct(
    section_name: str,
    sec_num: str,
    state: SOPState,
    facts: List[str],
    cites: List[str],
    compliance: List[str],
    best_practices: List[str],
    outline_subsections_text: str,
) -> str:
    """
    Direct Bedrock generation with overflow-safe retry.
    Returns plain text.
    """
    fmt_ctx = _compact_kb_format_ctx(state.kb_format_context or {})
    # First attempt
    prompt = _make_section_prompt(
        section_name=section_name,
        sec_num=sec_num,
        state=state,
        fmt_ctx=fmt_ctx,
        facts=facts,
        cites=cites,
        compliance=compliance,
        best_practices=best_practices,
        outline_subsections_text=outline_subsections_text,
        concise_hint=False,
    )
    text, stop = _invoke_bedrock_text(
        system_prompt=CONTENT_SYSTEM_PROMPT,
        user_prompt=prompt,
        max_tokens=_CONTENT_MAX_TOKENS_PER_SECTION,
        model_id=_get_model_id("MODEL_CONTENT"),
        temperature=0.2,
    )

    if stop == "max_tokens" or not text:
        logger.warning("Section '%s' hit max_tokens or empty text on first attempt; retrying concise mode.", section_name)
        reduced_facts = facts[: max(3, len(facts) // 2)]
        prompt2 = _make_section_prompt(
            section_name=section_name,
            sec_num=sec_num,
            state=state,
            fmt_ctx=fmt_ctx,
            facts=reduced_facts,
            cites=cites[:max(3, len(cites)//2)],
            compliance=compliance,
            best_practices=best_practices,
            outline_subsections_text=outline_subsections_text,
            concise_hint=True,
        )
        text2, _ = _invoke_bedrock_text(
            system_prompt=CONTENT_SYSTEM_PROMPT,
            user_prompt=prompt2,
            max_tokens=max(1200, _CONTENT_MAX_TOKENS_PER_SECTION - 600),
            model_id=_get_model_id("MODEL_CONTENT"),
            temperature=0.2,
        )
        return (text2 or "").strip()

    return (text or "").strip()


# ── STRANDS TOOL ──────────────────────────────────────────────────────────────

@tool
async def run_content(prompt: str) -> str:
    """
    Execute the SOP content generation step.
    Generates ALL 8 canonical SOP sections sequentially (direct Bedrock).
    Stores results in SOPState.content_sections as { section_title: text }.

    Expected prompt contains: 'workflow_id::<id>'
    """
    logger.info(">>> run_content | prompt: %.160s", (prompt or ""))

    m = re.search(r"workflow_id::([^\s\|]+)", prompt or "")
    workflow_id = m.group(1) if m else ""
    if not workflow_id:
        return "ERROR: Missing workflow_id in prompt. Expected 'workflow_id::<id>'."

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        return f"ERROR: no state found for workflow_id={workflow_id}"

    try:
        if not state.outline or not getattr(state.outline, "sections", None):
            raise ValueError(
                "No outline available for content generation. "
                "Ensure planning agent completed successfully."
            )

        if not state.research:
            raise ValueError(
                "No research findings in state. Ensure research agent completed successfully."
            )

        # Pull research fields
        rf = state.research
        best_practices: List[str] = list(getattr(rf, "best_practices", []) or [])
        compliance: List[str]     = list(getattr(rf, "compliance_requirements", []) or [])
        section_insights_raw      = list(getattr(rf, "section_insights", []) or [])

        # FIX: Log available section_insights keys so lookup failures are visible in logs
        available_si_keys = []
        for si in section_insights_raw:
            if isinstance(si, dict):
                available_si_keys.append(str(si.get("section", "?")))
            else:
                available_si_keys.append(str(getattr(si, "section", "?")))
        logger.info(
            "section_insights: %d entries | keys=%s | workflow_id=%s",
            len(available_si_keys), available_si_keys, workflow_id,
        )

        # Group insights by section number according to the list schema
        grouped = _group_insights_by_section(section_insights_raw)

        # Prepare container; persist early to ensure structure exists
        state.content_sections = state.content_sections or {}
        STATE_STORE[workflow_id] = state

        # FIX: Use planning outline sections (domain-specific) instead of hardcoded KB_SECTIONS.
        # Falls back to KB_SECTIONS only when planning outline is unavailable.
        if state.outline and getattr(state.outline, "sections", None):
            sections_to_write = [
                (sec.title, sec.number)
                for sec in state.outline.sections
            ]
            logger.info(
                "Using planning outline: %d sections | workflow_id=%s",
                len(sections_to_write), workflow_id,
            )
        else:
            logger.warning(
                "Planning outline unavailable — falling back to canonical KB_SECTIONS | workflow_id=%s",
                workflow_id,
            )
            sections_to_write = [
                (name, SECTION_NUMBER_MAP.get(name, ""))
                for name in KB_SECTIONS
            ]

        # Generate sequentially (avoids rate throttling)
        for section_name, sec_num in sections_to_write:

            # Handle optional split for PROCEDURE if many subsections
            if "procedure" in section_name.lower() or "qualification" in section_name.lower():
                subs = _outline_subsections_for(state, sec_num)
                if len(subs) >= _PROCEDURE_SPLIT_MIN_SUBSECTIONS:
                    logger.info(
                        "Splitting PROCEDURE into two parts (subsections=%d) | workflow_id=%s",
                        len(subs), workflow_id
                    )
                    mid = ceil(len(subs) / 2)
                    part1_prefixes = [n for (n, _) in subs[:mid]]
                    part2_prefixes = [n for (n, _) in subs[mid:]]

                    sel1 = _pick_insights_for_prefixes(
                        grouped=grouped,
                        prefixes=part1_prefixes,
                        max_facts=_CONTENT_MAX_FACTS_PER_SECTION,
                        max_cites=_CONTENT_MAX_CITES_PER_SECTION,
                    )
                    sel2 = _pick_insights_for_prefixes(
                        grouped=grouped,
                        prefixes=part2_prefixes,
                        max_facts=_CONTENT_MAX_FACTS_PER_SECTION,
                        max_cites=_CONTENT_MAX_CITES_PER_SECTION,
                    )

                    outline1 = _format_subsections_lines([(n, t) for (n, t) in subs[:mid]])
                    outline2 = _format_subsections_lines([(n, t) for (n, t) in subs[mid:]])

                    text1 = _generate_section_direct(
                        section_name=f"{section_name} — Part 1",
                        sec_num=sec_num,
                        state=state,
                        facts=sel1.get("facts", []),
                        cites=sel1.get("citations", []),
                        compliance=compliance,
                        best_practices=best_practices,
                        outline_subsections_text=outline1,
                    )
                    state.content_sections[f"{section_name} (Part 1)"] = text1
                    state.increment_tokens(2000)
                    STATE_STORE[workflow_id] = state  # persist after part 1

                    text2 = _generate_section_direct(
                        section_name=f"{section_name} — Part 2",
                        sec_num=sec_num,
                        state=state,
                        facts=sel2.get("facts", []),
                        cites=sel2.get("citations", []),
                        compliance=compliance,
                        best_practices=best_practices,
                        outline_subsections_text=outline2,
                    )
                    # Concatenate parts for the canonical key as well
                    full_text = (text1.rstrip() + "\n\n" + text2.lstrip()).strip()
                    state.content_sections[section_name] = full_text
                    state.increment_tokens(2000)
                    STATE_STORE[workflow_id] = state  # persist after full combine

                    logger.info("Generated PROCEDURE in two parts | workflow_id=%s", workflow_id)
                    continue  # next section

            # Default single-pass generation for other sections (or small Procedure)
            selected = _pick_insights_for_section(
                grouped=grouped,
                sec_num=sec_num,
                max_facts=_CONTENT_MAX_FACTS_PER_SECTION,
                max_cites=_CONTENT_MAX_CITES_PER_SECTION,
            )
            subs = _outline_subsections_for(state, sec_num)
            outline_text = _format_subsections_lines(subs)

            logger.info(
                "Generating section '%s' (%s) | workflow_id=%s | facts=%d, cites=%d",
                section_name, sec_num, workflow_id,
                len(selected.get("facts", [])), len(selected.get("citations", []))
            )

            text = _generate_section_direct(
                section_name=section_name,
                sec_num=sec_num,
                state=state,
                facts=selected.get("facts", []),
                cites=selected.get("citations", []),
                compliance=compliance,
                best_practices=best_practices,
                outline_subsections_text=outline_text,
            )

            # Persist after each section
            state.content_sections[section_name] = text
            state.increment_tokens(2200)
            STATE_STORE[workflow_id] = state

        # Mark state
        state.status       = WorkflowStatus.WRITTEN
        state.current_node = "content"
        STATE_STORE[workflow_id] = state

        logger.info(
            "Content generation complete — %d sections | workflow_id=%s",
            len(state.content_sections or {}), workflow_id
        )

        return (
            f"workflow_id::{workflow_id} | "
            f"Content complete: {len(state.content_sections or {})} sections written for '{state.topic}'"
        )

    except Exception as e:
        logger.error("Content generation FAILED: %s", e, exc_info=True)
        state.add_error(f"Content generation failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        STATE_STORE[workflow_id] = state
        return f"workflow_id::{workflow_id} | Content FAILED: {e}"


# ── NODE AGENT ────────────────────────────────────────────────────────────────
# The outer agent just routes to the tool; low token budget is fine.

content_agent = Agent(
    name="ContentNode",
    model=BedrockModel(model_id=_get_model_id("MODEL_CONTENT")),
    system_prompt=(
        "You are the content generation node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_content tool "
        "with the full message as the prompt argument. "
        "Do not add any commentary — just call the tool and return its result."
    ),
    tools=[run_content],
)
