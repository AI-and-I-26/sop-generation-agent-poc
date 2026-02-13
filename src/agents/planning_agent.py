"""
Planning Agent - Module 4, Section 4.2

Creates structured SOP outlines using Strand Agent with JSON schema enforcement.
"""

import os
import json
import logging
from typing import Dict, Any
from strands import Agent
from strands.types import ModelConfig

from src.graph.state_schema import SOPState, SOPOutline, WorkflowStatus

logger = logging.getLogger(__name__)


class PlanningAgent:
    """
    Planning Agent using Strand SDK
    
    Generates comprehensive SOP outlines with proper structure.
    Uses JSON schema enforcement for consistent outputs.
    """
    
    def __init__(self):
        """Initialize Planning Agent with Strand"""
        
        model_id = os.getenv('MODEL_PLANNING', 'meta.llama3-1-70b-instruct-v1:0')
        
        # Create Strand Agent
        self.agent = Agent(
            name="PlanningAgent",
            model=f"bedrock/{model_id}",
            system_prompt=self._get_system_prompt(),
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"},  # Force JSON output
            model_config=ModelConfig(
                region=os.getenv('AWS_REGION', 'us-east-1')
            )
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
        requirements: list = None
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
            # Invoke Strand agent
            response = await self.agent.ainvoke(user_prompt)
            
            # Parse JSON
            outline_data = json.loads(response.content)
            
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
                requirements=state.requirements
            )
            
            state.outline = outline
            state.status = WorkflowStatus.PLANNED
            state.current_node = "planning"
            state.increment_tokens(1500)
            
        except Exception as e:
            state.add_error(f"Planning failed: {str(e)}")
            state.status = WorkflowStatus.FAILED
        
        return state


# Standalone node function for Strand StateGraph
async def planning_node(state: SOPState) -> SOPState:
    """Planning node for Strand StateGraph"""
    agent = PlanningAgent()
    return await agent.execute(state)
