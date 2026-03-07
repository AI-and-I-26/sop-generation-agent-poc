# src/agents/formatter_agent.py
"""
formatter_agent.py — Formatter Agent for the SOP pipeline.

ROLE IN PIPELINE:
    Node 4 of 5.  Takes the structured JSON sections from the content agent
    and renders them into Markdown that matches YOUR KB's formatting style.

DYNAMIC FORMATTING:
    The formatter receives kb_format_context — extracted from the actual KB
    documents during the research step.  It uses this to render:
      - Tables in the sections where the KB uses tables
      - Indented numbered subsections where the KB uses them
      - Plain prose where the KB uses plain prose
      - The exact column names observed in KB tables
      - The writing tone/style observed in KB documents

    No formatting rules are hardcoded here.  The same formatter works for
    any KB — the rendering adapts to whatever format context was discovered.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

from strands import Agent, tool
from strands.models import BedrockModel  # Using Anthropic via Bedrock inference profile

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE
from src.prompts.system_prompts import FORMATTER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ── CONFIGURATION ──────────────────────────────────────────────────────────────
# Default to Anthropic Claude (Bedrock inference profile).
_DEFAULT_MODEL_ID = (
    "arn:aws:bedrock:us-east-2:070797854596:inference-profile/global.anthropic.claude-sonnet-4-6"
)
_REGION = os.getenv("AWS_REGION", "us-east-2")


def _get_model_id(env_var: str) -> str:
    return os.getenv(env_var, _DEFAULT_MODEL_ID)


def _bedrock_model(env_var: str) -> BedrockModel:
    # This uses Anthropic Claude through Bedrock. If you switch to direct Anthropic later,
    # replace with the appropriate strands.models.AnthropicModel(...) if available in your stack.
    return BedrockModel(model_id=_get_model_id(env_var), region=_REGION)


# ── DOCUMENT HEADER ────────────────────────────────────────────────────────────

def _build_document_header(state: SOPState) -> Dict[str, Any]:
    """
    Build the document control header dict passed to the formatter.

    Contains metadata rendered at the top of the finished document:
    title, document ID, version, effective date, industry, and audience.
    """
    title = state.outline.title if state.outline else state.topic
    return {
        "title": title,
        "document_id": f"SOP-{datetime.now().strftime('%Y%m%d-%H%M')}",
        "version": "1.0",
        "effective_date": datetime.now().strftime("%d-%b-%Y"),
        "industry": state.industry,
        "target_audience": state.target_audience,
    }


# ── LLM FORMATTER ──────────────────────────────────────────────────────────────

async def _run_llm_formatter(state: SOPState) -> str:
    """
    Call Anthropic Claude (via Bedrock) to convert content_sections JSON into KB-format Markdown.

    Passes the full content_sections dict to FORMATTER_SYSTEM_PROMPT which
    knows the exact rendering rules for each section type.

    Returns the formatted Markdown string.
    """
    header = _build_document_header(state)

    payload = json.dumps(
        {
            "document_header": header,
            "sections": state.content_sections,
            "kb_format_context": state.kb_format_context or {},
        },
        indent=2,
        ensure_ascii=False,
    )

    user_prompt = (
        "Convert the following SOP JSON payload into KB-format Markdown "
        "following your system prompt rules exactly.\n\n"
        f"{payload}\n\n"
        'Return ONLY a JSON object with one key: "formatted_markdown" '
        "whose value is the complete Markdown string."
    )

    # IMPORTANT: Do NOT pass max_tokens (constructor-time) to Agent; it is not supported.
    llm = Agent(
        name="FormatterLLM",
        model=_bedrock_model("MODEL_FORMATTER"),
        system_prompt=FORMATTER_SYSTEM_PROMPT,
        # If you need output limits, pass them at the underlying model call level (Bedrock: maxTokens)
        # via your model wrapper, not here.
    )

    response = await llm.invoke_async(user_prompt)
    response_text = str(response).strip()

    # Strip code fences if present
    if response_text.startswith("```"):
        parts = response_text.split("```")
        if len(parts) >= 2:
            response_text = parts[1]
            if response_text.lower().startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

    # The model should return { "formatted_markdown": "..." }
    try:
        result = json.loads(response_text)
    except Exception:
        logger.warning("Formatter returned non-JSON; using raw response as markdown.")
        return response_text

    if isinstance(result, dict) and "formatted_markdown" in result:
        return result["formatted_markdown"]

    logger.warning("Formatter JSON missing 'formatted_markdown'; using raw response.")
    return response_text


# ── STRANDS TOOL ───────────────────────────────────────────────────────────────

@tool
async def run_formatting(prompt: str) -> str:
    """
    Execute the SOP formatting step.

    Reads the structured JSON sections from STATE_STORE, calls the LLM
    formatter, and writes the resulting Markdown back to SOPState.

    Args:
        prompt: Graph message string containing 'workflow_id::<id>'.

    Returns:
        "workflow_id::<id> | Formatting complete: ..." or error string.
    """
    logger.info(">>> run_formatting | prompt: %.120s", prompt)

    # ── Extract workflow_id ──────────────────────────────────────────────
    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        return f"ERROR: no state found for workflow_id={workflow_id}"

    try:
        if not state.content_sections:
            raise ValueError(
                "No content sections available for formatting. "
                "Ensure content_agent ran successfully."
            )

        # ── LLM rendering ────────────────────────────────────────────────
        formatted_md = await _run_llm_formatter(state)

        # Write to both fields for compatibility
        state.formatted_markdown = formatted_md
        state.formatted_document = formatted_md   # kept for backward compat
        state.status = WorkflowStatus.FORMATTED
        state.current_node = "formatter"
        state.increment_tokens(800)

        logger.info(
            "Formatting complete — %d chars | workflow_id=%s",
            len(formatted_md), workflow_id
        )

        return (
            f"workflow_id::{workflow_id} | "
            f"Formatting complete: document assembled with "
            f"{len(state.content_sections)} sections ({len(formatted_md)} chars)"
        )

    except Exception as e:
        logger.error("Formatting FAILED: %s", e, exc_info=True)
        state.add_error(f"Formatting failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Formatting FAILED: {e}"


# ── NODE AGENT ─────────────────────────────────────────────────────────────────

formatter_agent = Agent(
    name="FormatterNode",
    model=_bedrock_model("MODEL_FORMATTER"),
    system_prompt=(
        "You are the formatting node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_formatting tool "
        "with the full message as the prompt argument. "
        "Do not add any commentary — just call the tool and return its result."
    ),
    tools=[run_formatting],
    # Do NOT add max_tokens here.
)