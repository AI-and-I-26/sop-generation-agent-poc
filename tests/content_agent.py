"""
content_agent.py — Content Agent for the SOP pipeline.

ROLE IN PIPELINE:
    Node 3 of 5.  After research, this agent writes the actual SOP text —
    one section at a time — using the outline from the planning agent and
    the KB-derived facts from the research agent.

SECTION-BY-SECTION APPROACH:
    Generates each of the 8 canonical SOP sections as a separate LLM call.
    This prevents truncation, hallucination, and format drift.

KB ALIGNMENT:
    Each section call includes:
      - kb_format_context : formatting conventions extracted from the KB
      - section_insights  : KB-derived facts for that specific section
      - compliance requirements and best practices from research

FIXES APPLIED:
    1. max_tokens=2048 removed from Agent() — it belongs on BedrockModel.
    2. Generates ALL 8 sections, not just outline.sections[:5].
    3. kb_format_context passed into every section prompt.
    4. section_insights normalised (list or dict) and passed per-section.
    5. content_sections stores the full section text string robustly
       (handles JSON with "content" key OR plain text response).
    6. CONTENT_SYSTEM_PROMPT imported from system_prompts.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE
from src.prompts.system_prompts import CONTENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ── CONFIGURATION ──────────────────────────────────────────────────────────────

_DEFAULT_ARN = (
    "arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")


def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_ARN)


def _bedrock_model(env_var: str, max_tokens: int = 3000) -> BedrockModel:
    """
    Create a BedrockModel with an explicit max_tokens budget.

    IMPORTANT: max_tokens belongs here on BedrockModel — NOT on Agent.__init__().
    Passing it to Agent() raises:
        TypeError: Agent.__init__() got an unexpected keyword argument 'max_tokens'
    """
    return BedrockModel(model_id=_get_model_id(env_var), max_tokens=max_tokens)


# ── CANONICAL SECTION ORDER ────────────────────────────────────────────────────
# All 8 standard SOP sections, generated in this fixed order regardless of
# how many sections the planner returned.

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


# ── INNER LLM AGENT ────────────────────────────────────────────────────────────

def _make_llm_agent() -> Agent:
    """
    Create the inner LLM agent used to generate each section.
    max_tokens is on BedrockModel — Agent() does not accept it.
    """
    return Agent(
        name="ContentLLM",
        model=_bedrock_model("MODEL_CONTENT", max_tokens=3000),
        system_prompt=CONTENT_SYSTEM_PROMPT,
    )


# ── SECTION GENERATOR ──────────────────────────────────────────────────────────

async def _generate_section(
    section_name: str,
    state: SOPState,
    section_insights: Any,
    compliance: List[str],
    best_practices: List[str],
) -> str:
    """
    Generate the text content for one SOP section.

    Returns a plain string ready for the formatter to embed into the document.
    """

    # KB format context — tells the model how the KB documents are structured
    kb_format_ctx_str = (
        json.dumps(state.kb_format_context, indent=2)
        if state.kb_format_context
        else "(not available — use standard SOP formatting)"
    )

    # Outline subsections for this section (from planning agent)
    outline_subsections: str = ""
    if state.outline:
        sec_num = SECTION_NUMBER_MAP.get(section_name, "")
        for sec in state.outline.sections:
            if sec.number == sec_num and getattr(sec, "subsections", None):
                outline_subsections = "\n".join(
                    f"  {sub.number} {sub.title}" for sub in sec.subsections
                )
                break

    # KB insights for this specific section
    insights_str = (
        json.dumps(section_insights, indent=2)
        if section_insights
        else "(no KB insights for this section)"
    )

    compliance_str  = ", ".join(compliance) if compliance else "None"
    practices_str   = "; ".join(best_practices[:5]) if best_practices else "None"

    prompt_parts = [
        f"Section: {section_name}",
        f"Topic:   {state.topic}",
        f"Industry: {state.industry}",
        f"Target Audience: {state.target_audience}",
        "",
    ]
    if outline_subsections:
        prompt_parts += [
            f"Outline subsections for this section:",
            outline_subsections,
            "",
        ]
    prompt_parts += [
        "KB FORMAT CONTEXT (match the KB's exact writing conventions):",
        kb_format_ctx_str,
        "",
        "KB Insights for this section (ground content in these facts):",
        insights_str,
        "",
        f"Compliance requirements: {compliance_str}",
        f"Best practices: {practices_str}",
        "",
        "Write the complete content for this section.",
        "Return plain text — no JSON wrapper, no code fences.",
        "Use the KB FORMAT CONTEXT to match writing style and structure.",
        "Use the KB Insights to ground every claim in real KB facts.",
    ]

    user_prompt = "\n".join(prompt_parts)

    llm = _make_llm_agent()
    response = await llm.invoke_async(user_prompt)
    return str(response).strip()


# ── STRANDS TOOL ───────────────────────────────────────────────────────────────

@tool
async def run_content(prompt: str) -> str:
    """
    Execute the SOP content generation step.

    Generates ALL 8 canonical SOP sections sequentially, grounding each
    section in KB format context and KB insights from the research agent.
    Stores results in SOPState.content_sections as { section_title: text }.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.

    Returns:
        "workflow_id::<id> | Content complete: N sections written" or error.
    """
    logger.info(">>> run_content | prompt: %.120s", prompt)

    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        return f"ERROR: no state found for workflow_id={workflow_id}"

    try:
        if not state.outline:
            raise ValueError(
                "No outline available for content generation. "
                "Ensure planning_agent ran successfully."
            )

        # Pull research context from state
        research_data  = state.research.dict() if state.research else {}
        best_practices = research_data.get("best_practices", [])
        compliance     = research_data.get("compliance_requirements", [])

        # Normalise section_insights — may be a dict keyed by section number
        # (e.g. {"1.0": "..."}) or a list of {section_number, fact, source}
        # entries depending on which research schema version is in use.
        raw_insights = research_data.get("section_insights", {})
        if isinstance(raw_insights, list):
            all_section_insights: Dict[str, Any] = {}
            for entry in raw_insights:
                if isinstance(entry, dict) and "section_number" in entry:
                    sn = entry["section_number"]
                    all_section_insights.setdefault(sn, []).append(
                        entry.get("fact", "")
                    )
        else:
            all_section_insights = raw_insights or {}

        content_sections: Dict[str, str] = {}

        # Generate ALL 8 sections sequentially (avoids Bedrock rate limits)
        for section_name in KB_SECTIONS:
            sec_num          = SECTION_NUMBER_MAP.get(section_name, "")
            section_insights = all_section_insights.get(sec_num, {})

            logger.info(
                "Generating section '%s' (%s) | workflow_id=%s",
                section_name, sec_num, workflow_id,
            )

            section_text = await _generate_section(
                section_name=section_name,
                state=state,
                section_insights=section_insights,
                compliance=compliance,
                best_practices=best_practices,
            )

            content_sections[section_name] = section_text
            state.increment_tokens(2500)

        state.content_sections = content_sections
        state.status       = WorkflowStatus.WRITTEN
        state.current_node = "content"

        logger.info(
            "Content generation complete — %d sections | workflow_id=%s",
            len(content_sections), workflow_id,
        )

        return (
            f"workflow_id::{workflow_id} | "
            f"Content complete: {len(content_sections)} sections written "
            f"for '{state.topic}'"
        )

    except Exception as e:
        logger.error("Content generation FAILED: %s", e, exc_info=True)
        state.add_error(f"Content generation failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Content FAILED: {e}"


# ── NODE AGENT ─────────────────────────────────────────────────────────────────
# max_tokens=1024 is sufficient — this outer agent only routes the message
# to run_content; it never generates large text itself.

content_agent = Agent(
    name="ContentNode",
    model=_bedrock_model("MODEL_CONTENT", max_tokens=1024),
    system_prompt=(
        "You are the content generation node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_content tool "
        "with the full message as the prompt argument. "
        "Do not add any commentary — just call the tool and return its result."
    ),
    tools=[run_content],
)
