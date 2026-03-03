"""
content_agent.py — Content Agent for the SOP pipeline.

ROLE IN PIPELINE:
    Node 3 of 5.  After research, this agent writes the actual SOP text —
    one section at a time — using the outline from the planning agent and
    the KB-derived facts from the research agent.

SECTION-BY-SECTION APPROACH:
    Instead of asking the model to write the entire document in one shot
    (which risks truncation, hallucination, and format drift), this agent
    loops over the eight KB sections and generates each as a separate
    structured JSON call.  This gives:
      - Smaller, focused prompts per section
      - Consistent JSON schema per section (enforced in the system prompt)
      - Per-section KB insights from the research agent's section_insights

KB ALIGNMENT:
    Each section call includes:
      - The KB insights for that specific section (from research.section_insights)
      - The compliance requirements
      - The list of KB best practices
    This grounds the content in actual KB material rather than hallucination.

STRANDS GRAPH PATTERN: same as planning_agent.py — @tool + outer Agent node.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict

import boto3
from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE
from src.prompts.system_prompts import CONTENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ── CONFIGURATION ──────────────────────────────────────────────────────────────

_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")


def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _bedrock_model(env_var: str) -> BedrockModel:
    return BedrockModel(model_id=_get_model_id(env_var))


# ── SECTION ORDERING ───────────────────────────────────────────────────────────
# The eight KB sections in canonical order.  The content agent iterates these
# in sequence so that the formatter can render them in the correct order.
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

# Map section name → section number (for section_insights lookup)
SECTION_NUMBER_MAP: Dict[str, str] = {
    "PURPOSE":                   "1.0",
    "SCOPE":                     "2.0",
    "RESPONSIBILITIES":          "3.0",
    "DEFINITIONS / ABBREVIATIONS": "4.0",
    "MATERIALS":                 "5.0",
    "PROCEDURE":                 "6.0",
    "REFERENCES":                "7.0",
    "REVISION HISTORY":          "8.0",
}


# ── LLM HELPER ─────────────────────────────────────────────────────────────────

async def _generate_section(
    section_name: str,
    state: SOPState,
    section_insights: Dict[str, Any],
    compliance: list,
    best_practices: list,
) -> Dict[str, Any]:
    """
    Call Claude via Strands Agent to write one SOP section.

    Args:
        section_name    : One of the eight KB section names.
        state           : Current SOPState (for topic / industry / audience).
        section_insights: KB-derived facts specific to this section.
        compliance      : List of applicable compliance requirements.
        best_practices  : List of KB best practices.

    Returns:
        Parsed JSON dict following the section's schema defined in CONTENT_SYSTEM_PROMPT.
    """

    # Serialise KB format context for this section
    # This tells the model how the KB documents are formatted so it can match them
    kb_format_ctx_str = (
        json.dumps(state.kb_format_context, indent=2)
        if state.kb_format_context
        else "(not available — use standard SOP formatting)"
    )

    # Retrieve outline subsections for this section (if planning produced them)
    outline_subsections: str = ""
    if state.outline:
        sec_num = SECTION_NUMBER_MAP.get(section_name, "")
        for sec in state.outline.sections:
            if sec.number == sec_num and sec.subsections:
                titles = [
                    f"  {sub.number} {sub.title}"
                    for sub in sec.subsections
                ]
                outline_subsections = "\n".join(titles)
                break

    # Serialise KB insights for this section
    insights_str = (
        json.dumps(section_insights, indent=2)
        if section_insights
        else "(no KB insights for this section)"
    )

    # Build the per-section user prompt
    user_prompt = (
        f"Section: {section_name}\n"
        f"Topic:   {state.topic}\n"
        f"Industry: {state.industry}\n"
        f"Target Audience: {state.target_audience}\n\n"
        + (f"Outline subsections for this section:\n{outline_subsections}\n\n" if outline_subsections else "")
        + f"KB FORMAT CONTEXT (formatting conventions from your Knowledge Base):\n{kb_format_ctx_str}\n\n"
        + f"KB Insights for this section:\n{insights_str}\n\n"
        f"Compliance requirements: {', '.join(compliance) if compliance else 'None'}\n"
        f"Best practices: {'; '.join(best_practices[:5]) if best_practices else 'None'}\n\n"
        "Write ONLY the JSON object for this section.\n"
        "Use the KB FORMAT CONTEXT to match the KB's writing style and structure.\n"
        "Use the KB Insights to ground the content in real KB facts.\n"
        "JSON only. No code fences. No commentary."
    )

    # Inner LLM agent — direct Bedrock call via Strands
    llm = Agent(
        name="ContentLLM",
        model=_bedrock_model("MODEL_CONTENT"),
        system_prompt=CONTENT_SYSTEM_PROMPT,
        max_tokens=3000,    # enough for the longest sections (PROCEDURE, SCOPE)
    )

    response = await llm.invoke_async(user_prompt)
    response_text = str(response).strip()

    # Strip code fences defensively (model should not add them but may)
    if response_text.startswith("```"):
        parts = response_text.split("```")
        if len(parts) >= 2:
            response_text = parts[1]
            if response_text.lower().startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

    return json.loads(response_text)


# ── STRANDS TOOL ───────────────────────────────────────────────────────────────

@tool
async def run_content(prompt: str) -> str:
    """
    Execute the SOP content generation step.

    Loops over all eight KB sections, generating each via a separate LLM call,
    and stores the results as a dict of { section_title → content_dict } in
    SOPState.content_sections.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.

    Returns:
        "workflow_id::<id> | Content complete: ..." or error string.
    """
    logger.info(">>> run_content | prompt: %.120s", prompt)

    # ── Extract workflow_id ──────────────────────────────────────────────
    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        return f"ERROR: no state found for workflow_id={workflow_id}"

    try:
        if not state.outline:
            raise ValueError("No outline available for content generation. "
                             "Ensure planning_agent ran successfully.")

        # ── Gather research context ──────────────────────────────────────
        # Pull compliance + best practices from research findings
        research_data = state.research.dict() if state.research else {}
        best_practices  = research_data.get("best_practices", [])
        compliance      = research_data.get("compliance_requirements", [])

        # section_insights is a dict keyed by section number ("1.0", "2.0", etc.)
        # Populated by the research agent's LLM synthesis step.
        all_section_insights: Dict[str, Any] = research_data.get("section_insights", {})

        content_sections: Dict[str, Any] = {}

        # ── Generate each section sequentially ──────────────────────────
        # Sequential (not concurrent) to keep prompts focused and avoid
        # rate-limit issues on Bedrock.
        for section_name in KB_SECTIONS:
            sec_num = SECTION_NUMBER_MAP.get(section_name, "")
            # Look up KB facts specific to this section
            section_insights = all_section_insights.get(sec_num, {})

            logger.info(
                "Generating section '%s' (%s) | workflow_id=%s",
                section_name, sec_num, workflow_id
            )

            section_data = await _generate_section(
                section_name=section_name,
                state=state,
                section_insights=section_insights,
                compliance=compliance,
                best_practices=best_practices,
            )

            # Store the section's full JSON dict under its title key
            content_sections[section_name] = section_data

            # Approximate token accounting (per section)
            state.increment_tokens(2500)

        # ── Write back to shared state ───────────────────────────────────
        state.content_sections = content_sections
        state.status = WorkflowStatus.WRITTEN
        state.current_node = "content"

        logger.info(
            "Content generation complete — %d sections | workflow_id=%s",
            len(content_sections), workflow_id
        )

        return (
            f"workflow_id::{workflow_id} | "
            f"Content complete: {len(content_sections)} sections written for '{state.topic}'"
        )

    except Exception as e:
        logger.error("Content generation FAILED: %s", e, exc_info=True)
        state.add_error(f"Content generation failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Content FAILED: {e}"


# ── NODE AGENT ─────────────────────────────────────────────────────────────────

content_agent = Agent(
    name="ContentNode",
    model=_bedrock_model("MODEL_CONTENT"),
    system_prompt=(
        "You are the content generation node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_content tool "
        "with the full message as the prompt argument. "
        "Do not add commentary — just call the tool and return its result."
    ),
    tools=[run_content],
)