"""
Planning Agent - Module 4, Section 4.2

Creates structured SOP outlines using Strand Agent with JSON schema enforcement.
"""

import os
import json
import logging
from typing import Dict, Any
from strands import Agent, tool
from strands.models import BedrockModel
import boto3

from src.graph.state_schema import SOPState, SOPOutline, WorkflowStatus

logger = logging.getLogger(__name__)


class PlanningAgent:
    """
    Planning Agent using Strand SDK

    Generates comprehensive SOP outlines with proper structure.
    Uses JSON schema enforcement for consistent outputs.
    """

    def __init__(self):
        model_id = os.getenv(
            "MODEL_PLANNING",
            "arn:aws:bedrock:us-east-2:070797854596:inference-profile/us.meta.llama3-3-70b-instruct-v1:0",
        )
        region = os.getenv("AWS_REGION", "us-east-2")

        # FIX: Removed unsupported `response_format` kwarg from Agent constructor.
        # Strands Agent does not accept response_format; JSON enforcement is done
        # via the system prompt instruction instead.
        self.agent = Agent(
            name="PlanningAgent",
            model=BedrockModel(model_id=model_id, region=region),
            system_prompt=self._get_system_prompt(),
            max_tokens=2048,
        )

        logger.info(f"Initialized PlanningAgent with model: {model_id}")

    def _get_system_prompt(self) -> str:
        """Get system prompt for planning agent"""
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
        """
        Create SOP outline

        Args:
            topic: SOP topic
            industry: Industry domain
            target_audience: Target users
            requirements: Additional requirements

        Returns:
            SOPOutline object
        """

        user_prompt = f"""Create a detailed SOP outline for:

Topic: {topic}
Industry: {industry}
Target Audience: {target_audience}
Additional Requirements: {', '.join(requirements or [])}

Return valid JSON with all required sections."""

        try:
            assert self.agent is not None, "PlanningAgent.agent is None — constructor failed"
            logger.debug("DEBUG type(self.agent) = %s", type(self.agent))

            # FIX: Strands Agent.__call__ / invoke_async returns an AgentResult object.
            # Convert to string with str() before JSON parsing — NOT response.content.
            response = await self.agent.invoke_async(user_prompt)
            response_text = str(response)

            # Strip any markdown code fences the model may have added
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            # Parse JSON
            outline_data = json.loads(response_text)

            # Validate with Pydantic
            outline = SOPOutline(**outline_data)

            logger.info(f"Created outline with {len(outline.sections)} sections")

            return outline

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from agent: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating outline: {e}")
            raise

    async def execute(self, state: SOPState) -> SOPState:
        """
        Execute planning agent (Strand node function)

        Args:
            state: Current SOPState

        Returns:
            Updated SOPState
        """
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
            state.add_error(f"Planning failed: {str(e)}")
            state.status = WorkflowStatus.FAILED

        return state


@tool
async def planning_tool(state: SOPState) -> SOPState:
    """Planning tool: executes the PlanningAgent logic."""
    agent = PlanningAgent()
    return await agent.execute(state)


# Create the Strands Agent that wraps the planning_tool for graph node use
planning_agent = Agent(
    tools=[planning_tool],
)