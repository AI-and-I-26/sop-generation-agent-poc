"""
Planning Agent - Module 4, Section 4.2

Creates structured SOP outlines using Strand Agent with JSON schema enforcement.

GRAPH INTEGRATION PATTERN:
  The Strands graph only supports Agent instances as nodes, and passes plain
  string messages between them (not SOPState objects).  This Agent:
    1. Has a @tool (run_planning) that extracts the workflow_id from the
       string prompt, fetches SOPState from STATE_STORE, does the work,
       writes the result back to STATE_STORE, and returns a summary string.
    2. Its system_prompt instructs it to always call run_planning immediately.
  The Agent itself is registered with GraphBuilder as the "planning" node.
"""

import os
import json
import logging
from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, SOPOutline, WorkflowStatus
from src.agents.state_store import STATE_STORE

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Inner LLM agent (does the actual outline generation — takes a string prompt)
# ---------------------------------------------------------------------------

def _make_llm_agent() -> Agent:
    model_id = os.getenv(
        "MODEL_PLANNING",
        "arn:aws:bedrock:us-east-2:070797854596:inference-profile/us.meta.llama3-3-70b-instruct-v1:0",
    )
    region = os.getenv("AWS_REGION", "us-east-2")

    return Agent(
        name="PlanningLLM",
        model=BedrockModel(model_id=model_id, region=region),
        system_prompt="""You are an expert SOP planning agent.
Create comprehensive, well-structured outlines for Standard Operating Procedures.

MANDATORY SECTIONS (in order):
1. Purpose and Scope
2. Definitions and Abbreviations
3. Responsibilities and Authorities
4. Required Materials and Equipment
5. Safety Requirements and PPE
6. Detailed Step-by-Step Procedures
7. Quality Control and Verification
8. Emergency Procedures
9. Troubleshooting Guide
10. References and Related Documents
11. Revision History

OUTPUT FORMAT — Return ONLY valid JSON:
{
  "title": "Complete SOP Title",
  "industry": "Industry Name",
  "sections": [
    {"number": "1", "title": "Purpose and Scope", "subsections": ["1.1 Purpose", "1.2 Scope"]}
  ],
  "estimated_pages": 8
}
Use hierarchical numbering (1, 1.1, 1.1.1).""",
        max_tokens=2048,
    )


# ---------------------------------------------------------------------------
# Graph-level tool — called by the planning_agent node
# ---------------------------------------------------------------------------

@tool
async def run_planning(prompt: str) -> str:
    """Execute the SOP planning step.

    Reads the SOPState identified by the workflow_id embedded in the prompt,
    generates a structured outline, saves it back to STATE_STORE, and returns
    a summary string for the next graph node.

    Args:
        prompt: The graph message string containing 'workflow_id::<id>'.
    """
    # Extract workflow_id from prompt
    workflow_id = ""
    if "workflow_id::" in prompt:
        workflow_id = prompt.split("workflow_id::")[1].split()[0].strip()

    state: SOPState = STATE_STORE.get(workflow_id)
    if state is None:
        return f"ERROR: no state found for workflow_id={workflow_id}"

    try:
        llm = _make_llm_agent()

        user_prompt = (
            f"Create a detailed SOP outline for:\n"
            f"Topic: {state.topic}\n"
            f"Industry: {state.industry}\n"
            f"Target Audience: {state.target_audience}\n"
            f"Additional Requirements: {', '.join(state.requirements or [])}\n\n"
            f"Return valid JSON with all required sections."
        )

        response = await llm.invoke_async(user_prompt)
        response_text = str(response).strip()

        # Strip markdown code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        outline_data = json.loads(response_text)
        outline = SOPOutline(**outline_data)

        state.outline = outline
        state.status = WorkflowStatus.PLANNED
        state.current_node = "planning"
        state.increment_tokens(1500)

        logger.info("Planning complete — %d sections | workflow_id=%s",
                    len(outline.sections), workflow_id)

        return (
            f"workflow_id::{workflow_id} | "
            f"Planning complete: {len(outline.sections)} sections created for '{state.topic}'"
        )

    except Exception as e:
        logger.error("Planning failed: %s", e)
        state.add_error(f"Planning failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Planning FAILED: {e}"


# ---------------------------------------------------------------------------
# The Agent node registered with GraphBuilder
# ---------------------------------------------------------------------------

planning_agent = Agent(
    name="PlanningNode",
    system_prompt=(
        "You are the planning node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_planning tool "
        "with the full message as the prompt argument. "
        "Do not add any commentary — just call the tool and return its result."
    ),
    tools=[run_planning],
)
