"""
Research Agent - Fixed Version
"""

import os
import json
import logging
from strands import Agent
from strands.models import BedrockModel
from src.graph.state_schema import SOPState, ResearchFindings, WorkflowStatus

logger = logging.getLogger(__name__)


class ResearchAgent:
    def __init__(self):
        model_id = os.getenv(
            "MODEL_RESEARCH",
            "arn:aws:bedrock:us-east-2:070797854596:inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
        )
        region = os.getenv("AWS_REGION", "us-east-2")

        self.agent = Agent(
            name="ResearchAgent",
            model=BedrockModel(model_id=model_id, region=region),
            system_prompt="You are a research specialist. Return JSON.",
            temperature=0.5,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )

    async def execute(self, state: SOPState) -> SOPState:
        try:
            prompt = f"""
Research topic: {state.topic}
Industry: {state.industry}
"""

            response = await self.agent.invoke_async(prompt)
            findings_data = json.loads(response.content)

            findings = ResearchFindings(**findings_data)

            state.research = findings
            state.status = WorkflowStatus.RESEARCHED
            state.current_node = "research"
            state.increment_tokens(2000)

        except Exception as e:
            state.add_error(f"Research failed: {str(e)}")
            state.status = WorkflowStatus.FAILED

        return state


# ✅ Graph node wrapper
async def research_node(state: SOPState) -> SOPState:
    agent = ResearchAgent()
    return await agent.execute(state)
