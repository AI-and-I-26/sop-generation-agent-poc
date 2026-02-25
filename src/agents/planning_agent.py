"""
Planning Agent - Module 4, Section 4.2

Creates structured SOP outlines using Strand Agent with JSON schema enforcement.
"""

import os
import json
import logging
from strands import Agent
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, SOPOutline, WorkflowStatus

logger = logging.getLogger(__name__)


class PlanningAgent:
    """
    Planning Agent using Strand SDK.
    Generates comprehensive SOP outlines with proper structure.
    """

    def __init__(self):
        model_id = os.getenv(
            "MODEL_PLANNING",
            "arn:aws:bedrock:us-east-2:070797854596:inference-profile/us.meta.llama3-3-70b-instruct-v1:0",
        )
        region = os.getenv("AWS_REGION", "us-east-2")

        self.agent = Agent(
            name="PlanningAgent",
            model=BedrockModel(model_id=model_id, region=region),
            system_prompt=self._get_system_prompt(),
            max_tokens=2048,
        )

        logger.info("Initialized PlanningAgent with model: %s", model_id)

    def _get_system_prompt(self) -> str:
        return """You are an expert SOP planning agent.

Your job is to create comprehensive, well-structured outlines for Standard Operating Procedures.

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

OUTPUT FORMAT:
Return ONLY valid JSON with this structure:
{
  "title": "Complete SOP Title",
  "industry": "Industry Name",
  "sections": [
    {
      "number": "1",
      "title": "Purpose and Scope",
      "subsections": ["1.1 Purpose", "1.2 Scope"]
    }
  ],
  "estimated_pages": 8
}

Use hierarchical numbering (1, 1.1, 1.1.1).
"""

    async def create_outline(
        self,
        topic: str,
        industry: str,
        target_audience: str,
        requirements: list = None,
    ) -> SOPOutline:

        user_prompt = f"""Create a detailed SOP outline for:

Topic: {topic}
Industry: {industry}
Target Audience: {target_audience}
Additional Requirements: {', '.join(requirements or [])}

Return valid JSON with all required sections."""

        # invoke_async returns an AgentResult — use str() to extract text
        response = await self.agent.invoke_async(user_prompt)
        response_text = str(response).strip()

        # Strip markdown code fences the model may have added
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        outline_data = json.loads(response_text)
        outline = SOPOutline(**outline_data)

        logger.info("Created outline with %d sections", len(outline.sections))
        return outline

    async def execute(self, state: SOPState) -> SOPState:
        try:
            outline = await self.create_outline(
                topic=state.topic,
                industry=state.industry,
                target_audience=state.target_audience,
                requirements=state.requirements,
            )
            state.outline = outline
            state.status = WorkflowStatus.PLANNED
            state.current_node = "planning"
            state.increment_tokens(1500)

        except Exception as e:
            logger.error("Planning failed: %s", e)
            state.add_error(f"Planning failed: {str(e)}")
            state.status = WorkflowStatus.FAILED

        return state


# ---------------------------------------------------------------------------
# FIX: Graph node must be a plain async function (SOPState) -> SOPState.
#
# Previous versions wrapped this in Agent(tools=[planning_tool]) and added
# that Agent as the graph node. When the graph called it, it passed the
# SOPState object directly as the agent prompt, which raised:
#   ValueError: Input prompt must be of type: `str | list[ContentBlock] | Messages | None`
#
# The correct pattern: register a plain async function with gb.add_node().
# The Strands graph will call planning_node(state) directly.
# ---------------------------------------------------------------------------

async def planning_node(state: SOPState) -> SOPState:
    """Graph node function for the planning step."""
    agent = PlanningAgent()
    return await agent.execute(state)
