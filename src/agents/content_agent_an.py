"""
Content Agent - Module 5, Section 5.1

Generates detailed SOP content using Strand Agent with few-shot prompting.

GRAPH INTEGRATION PATTERN: same as planning_agent.py — see that file.

BUG FIXED (this session):
  The outer node Agent had no `model` parameter — see planning_agent.py.
"""

import os
import json
import logging
from typing import Dict

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE

logger = logging.getLogger(__name__)

_DEFAULT_ARN = (
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
)

def _bedrock_model(env_var: str) -> BedrockModel:
    return BedrockModel(
        model_id=os.getenv(env_var, _DEFAULT_ARN),
        #region=os.getenv("AWS_REGION", "us-east-2"),
    )


# ---------------------------------------------------------------------------
# Inner LLM agent (string prompt in → string JSON out)
# ---------------------------------------------------------------------------

def _make_llm_agent() -> Agent:
    return Agent(
        name="ContentLLM",
        model=_bedrock_model("MODEL_CONTENT"),
        system_prompt="""You are a technical writer specializing in Standard Operating Procedures.

WRITING STYLE:
- Active voice and imperative mood ("Perform X" not "X should be performed")
- Specific and quantitative (exact numbers, temperatures, times)
- Clear and concise language
- Appropriate technical level for the target audience

FORMATTING REQUIREMENTS:
1. Number all procedure steps (1., 2., 3.)
2. Mark safety warnings:      ⚠️ WARNING: [warning text]
3. Mark critical notes:        ⚡ CRITICAL: [critical information]
4. Mark quality checkpoints:   ✓ CHECKPOINT: [what to verify]
5. Include time estimates per step

OUTPUT FORMAT — Return ONLY valid JSON:
{
  "section_title": "Section Name",
  "content": "## Section Name\\n\\n1. **Step One**\\n   - Detail\\n   - ⚠️ WARNING: ...\\n   - ✓ CHECKPOINT: ...\\n   - Estimated time: 30 seconds",
  "safety_warnings": ["Warning text"],
  "quality_checkpoints": ["Checkpoint text"],
  "time_estimate_minutes": 5
}""",
        max_tokens=2048,
    )


# ---------------------------------------------------------------------------
# Graph-level tool — called by the content_agent node
# ---------------------------------------------------------------------------

@tool
async def run_content(prompt: str) -> str:
    """Execute the SOP content generation step.

    Reads the SOPState identified by the workflow_id embedded in the prompt,
    generates detailed content for each outline section, saves results to
    STATE_STORE, and returns a summary string for the next graph node.

    Args:
        prompt: The graph message string containing 'workflow_id::<id>'.
    """
    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        return f"ERROR: no state found for workflow_id={workflow_id}"

    try:
        if not state.outline:
            raise ValueError("No outline available for content generation")

        llm = _make_llm_agent()
        research_data: Dict = state.research.dict() if state.research else {}
        best_practices = research_data.get("best_practices", [])
        compliance = research_data.get("compliance_requirements", [])

        content_sections = {}

        for section in state.outline.sections[:5]:
            section_prompt = (
                f"Write detailed content for this SOP section:\n\n"
                f"Section: {section.title}\n"
                f"Target Audience: {state.target_audience}\n\n"
                f"Relevant Information:\n"
                f"- Best Practices: {', '.join(best_practices) if best_practices else 'None'}\n"
                f"- Compliance: {', '.join(compliance) if compliance else 'None'}\n\n"
                f"Requirements:\n"
                f"1. Write clear, numbered steps\n"
                f"2. Include safety warnings where applicable\n"
                f"3. Add quality checkpoints\n"
                f"4. Provide time estimates\n"
                f"5. Use specific measurements and quantities\n\n"
                f"Return complete JSON with all required fields."
            )

            response = await llm.invoke_async(section_prompt)
            response_text = str(response).strip()

            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            content_data = json.loads(response_text)
            content_sections[section.title] = content_data["content"]

            state.increment_tokens(2500)
            logger.info("Generated content for section: %s | workflow_id=%s",
                        section.title, workflow_id)

        state.content_sections = content_sections
        state.status = WorkflowStatus.WRITTEN
        state.current_node = "content"

        logger.info("Content generation complete — %d sections | workflow_id=%s",
                    len(content_sections), workflow_id)

        return (
            f"workflow_id::{workflow_id} | "
            f"Content complete: {len(content_sections)} sections written for '{state.topic}'"
        )

    except Exception as e:
        logger.error("Content generation failed: %s", e)
        state.add_error(f"Content generation failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Content FAILED: {e}"


# ---------------------------------------------------------------------------
# The Agent node registered with GraphBuilder
# FIX: node Agent must have a model so it can actually invoke the tool.
# ---------------------------------------------------------------------------

content_agent = Agent(
    name="ContentNode",
    model=_bedrock_model("MODEL_CONTENT"),
    system_prompt=(
        "You are the content generation node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_content tool "
        "with the full message as the prompt argument. "
        "Do not add any commentary — just call the tool and return its result."
    ),
    tools=[run_content],
)