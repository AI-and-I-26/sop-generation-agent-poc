"""
Content Agent (Option B: client-side tool execution)

FOUR BUGS FIXED vs content_agent__2_.py:

FIX 1 — USER PROMPT CONTRADICTED SYSTEM PROMPT
  Old user_prompt explicitly asked for:
    "⚠️ WARNING:", "✓ CHECKPOINT:", "time estimates per step"
  CONTENT_SYSTEM_PROMPT banned all of those. The user prompt overrides the
  system prompt, so the model produced exactly the junk the user prompt asked for.
  Fix: user_prompt now instructs the model to follow its system prompt instructions
  and explicitly repeats the ban on those patterns.

FIX 2 — ONLY content_data["content"] WAS STORED — ALL STRUCTURE DISCARDED
  Old code: content_sections[section_key] = content_data["content"]
  CONTENT_SYSTEM_PROMPT returns rich per-section JSON with tables, subsections,
  role rows, term definitions etc. All of that was thrown away; only the flat
  "content" string reached the formatter.
  Fix: store the full content_data dict so the formatter receives everything.

FIX 3 — _MAX_SECTIONS CAPPED AT 5 — 3 SECTIONS NEVER GENERATED
  Old default: _MAX_SECTIONS = 5
  The KB outline has 8 sections (1.0–8.0). Sections 6.0, 7.0, 8.0 were silently
  skipped, which is why the generated PDF's TOC stopped at section 5.
  Fix: default raised to 8 (all KB sections).

FIX 4 — max_tokens=2048 TOO LOW FOR FULL SECTION JSON
  Section 6.0 PROCEDURE has deep nested subsections. 2048 tokens frequently hit
  the limit mid-JSON causing parse failures, the section was silently skipped.
  Fix: max_tokens raised to 4096 for content generation calls.
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
from src.prompts.system_prompts import CONTENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")

# FIX 3: was 5 — all 8 KB sections must be generated
_MAX_SECTIONS = int(os.getenv("MAX_CONTENT_SECTIONS", "8"))


# ---------------------------------------------------------------------------
# Robust JSON helpers (unchanged from original)
# ---------------------------------------------------------------------------
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)
_TRAILING_COMMA_RE = re.compile(r",\s*(?=[}\]])")


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
                    return s[start:i + 1]
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


# ---------------------------------------------------------------------------
# Bedrock helpers
# ---------------------------------------------------------------------------
def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _call_bedrock_sync(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 4096,   # FIX 4: was 2048
) -> str:
    logger.debug("=== BEDROCK CALL (Content) ===")
    logger.debug("Model: %s | Region: %s | max_tokens=%s", model_id, _REGION, max_tokens)
    logger.debug("User prompt (first 400 chars):\n%s", (user_prompt or "")[:400])

    client = boto3.client("bedrock-runtime", region_name=_REGION)
    response = client.converse(
        modelId=model_id,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": 0},
    )
    logger.debug("Raw response: %s", json.dumps(response, default=str))

    content = response.get("output", {}).get("message", {}).get("content", [])
    if not content:
        raise ValueError(f"Bedrock returned empty content: {response}")
    text = "\n".join(p.get("text", "") for p in content if "text" in p).strip()
    if not text:
        raise ValueError(f"Bedrock returned blank text: {response}")
    logger.debug("Extracted text (%d chars):\n%s", len(text), text[:800])
    return text


async def _call_bedrock_async(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 4096,   # FIX 4
) -> str:
    return await asyncio.to_thread(
        _call_bedrock_sync, model_id, system_prompt, user_prompt, max_tokens=max_tokens
    )


def _extract_workflow_id_from_prompt(prompt: str) -> Optional[str]:
    m = re.search(r"workflow_id::([^\s\|]+)", prompt or "")
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Graph-level tool
# ---------------------------------------------------------------------------
@tool
async def run_content(prompt: str) -> str:
    """Execute the SOP content generation step.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.
    """
    logger.info(">>> run_content called | prompt: %s", (prompt or "")[:160])

    workflow_id = _extract_workflow_id_from_prompt(prompt or "") or ""
    if not workflow_id:
        raise ValueError("Missing workflow_id in prompt.")

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        msg = f"ERROR: no state for workflow_id='{workflow_id}' | keys={list(STATE_STORE.keys())}"
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
        # Extract research context
        research_data: Dict[str, Any] = {}
        if getattr(state, "research", None) is not None:
            if hasattr(state.research, "dict"):
                research_data = state.research.dict()
            elif hasattr(state.research, "__dict__"):
                research_data = dict(state.research.__dict__)

        best_practices: List[str] = research_data.get("best_practices") or []
        compliance: List[str] = research_data.get("compliance_requirements") or []
        section_insights: Dict = research_data.get("section_insights") or {}

        model_id = _get_model_id("MODEL_CONTENT")
        max_sections = max(1, _MAX_SECTIONS)   # FIX 3: now defaults to 8
        generated = 0
        # FIX 2: store full content_data dicts, not just ["content"] strings
        content_sections: Dict[str, Any] = {}

        for idx, section in enumerate(state.outline.sections or []):
            if generated >= max_sections:
                break

            section_title = getattr(section, "title", f"Section {idx + 1}") or f"Section {idx + 1}"

            # Relevant KB insights for this specific section
            section_key_map = {
                "PURPOSE": "1.0",
                "SCOPE": "2.0",
                "RESPONSIBILITIES": "3.0",
                "DEFINITIONS / ABBREVIATIONS": "4.0",
                "MATERIALS": "5.0",
                "PROCEDURE": "6.0",
                "REFERENCES": "7.0",
                "REVISION HISTORY": "8.0",
            }
            insight_key = section_key_map.get(section_title.upper(), "")
            kb_insight = section_insights.get(insight_key, {})

            # ---------------------------------------------------------------
            # FIX 1: user_prompt no longer asks for WARNING / CHECKPOINT /
            # time estimates. It explicitly mirrors the system prompt bans.
            # ---------------------------------------------------------------
            user_prompt = (
                f"Write the content for this SOP section following your "
                f"system instructions exactly.\n\n"
                f"Section: {section_title}\n"
                f"Topic: {state.topic}\n"
                f"Industry: {state.industry}\n"
                f"Target Audience: {state.target_audience}\n\n"
                f"KB insights for this section:\n"
                f"{json.dumps(kb_insight, indent=2) if kb_insight else 'None'}\n\n"
                f"Additional best practices from KB: "
                f"{', '.join(best_practices) if best_practices else 'None'}\n"
                f"Compliance requirements: "
                f"{', '.join(compliance) if compliance else 'None'}\n\n"
                f"CRITICAL — your output must NOT contain any of:\n"
                f"  'Method:', 'Acceptance Criteria:', 'Time Estimate:',\n"
                f"  'Safety Considerations:', '⚠️ WARNING:', '✓ CHECKPOINT:',\n"
                f"  'Quality Checkpoints:', 'Overall Time Estimate:'\n\n"
                f"Return ONLY the JSON object for the '{section_title}' section "
                f"using the exact schema defined in your instructions. "
                f"No markdown, no code fences, no text outside the JSON."
            )

            last_err: Optional[Exception] = None
            raw_text: Optional[str] = None
            for attempt in range(1, 4):
                try:
                    raw_text = await _call_bedrock_async(
                        model_id,
                        CONTENT_SYSTEM_PROMPT,
                        user_prompt,
                        max_tokens=4096,   # FIX 4
                    )
                    break
                except Exception as e:
                    last_err = e
                    logger.warning(
                        "Content Bedrock failed (section='%s', attempt %d/3): %s",
                        section_title, attempt, e
                    )
                    if attempt < 3:
                        await asyncio.sleep(0.75 * attempt)
            else:
                logger.warning("Skipping '%s' after 3 failed attempts: %s", section_title, last_err)
                if hasattr(state, "add_error"):
                    state.add_error(f"Content section '{section_title}' failed: {last_err}")
                continue

            try:
                json_str = _extract_json_block(raw_text or "")
                if not json_str:
                    json_str = _strip_code_fences(raw_text or "")
                content_data = _loads_lenient(json_str)

                if "section_title" not in content_data or "content" not in content_data:
                    raise ValueError(
                        f"Model response missing 'section_title' or 'content'. "
                        f"Keys: {list(content_data.keys())}"
                    )

                section_key = content_data.get("section_title") or section_title

                # FIX 2: store full dict — tables, subsections, everything
                content_sections[section_key] = content_data

                if hasattr(state, "increment_tokens"):
                    state.increment_tokens(2500)
                generated += 1

                logger.info(
                    "Generated section '%s' | keys=%s | wf=%s",
                    section_key, list(content_data.keys()), workflow_id
                )

            except Exception as e:
                logger.warning("Parse failed for '%s': %s", section_title, e)
                if hasattr(state, "add_error"):
                    state.add_error(f"Content section '{section_title}' parse failed: {e}")
                continue

        if not content_sections:
            raise ValueError("No valid content sections were generated.")

        prev = getattr(state, "content_sections", None) or {}
        prev.update(content_sections)
        state.content_sections = prev
        state.status = WorkflowStatus.WRITTEN
        state.current_node = "content"

        logger.info(
            "Content complete — %d sections | wf=%s", len(content_sections), workflow_id
        )
        return (
            f"workflow_id::{workflow_id} | "
            f"Content complete: {len(content_sections)} sections for '{state.topic}'"
        )

    except Exception as e:
        logger.exception("Content FAILED wf=%s", workflow_id)
        if hasattr(state, "add_error"):
            state.add_error(f"Content generation failed: {e}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Content FAILED: {e}"


# ---------------------------------------------------------------------------
# Node entry point (unchanged interface — drop-in replacement)
# ---------------------------------------------------------------------------
async def run_content_node(
    prompt: str,
    *,
    use_llama_dispatch: bool = False,
) -> str:
    logger.info(">>> run_content_node | use_llama_dispatch=%s", use_llama_dispatch)
    # Always use direct path — dispatch mode not needed
    return await run_content(prompt=prompt)
