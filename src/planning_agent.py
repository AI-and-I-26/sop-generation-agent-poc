"""
Planning Agent - Fixed Version
"""

import os
import json
import logging
from strands import Agent
from strands.models import BedrockModel
from src.graph.state_schema import SOPState, SOPOutline, WorkflowStatus

logger = logging.getLogger(__name__)


class PlanningAgent:
    def __init__(self):
        model_id = os.getenv(
            "MODEL_PLANNING",
            "arn:aws:bedrock:us-east-2:070797854596:inference-profile/us.meta.llama3-3-70b-instruct-v1:0"
        )
        region = os.getenv("AWS_REGION", "us-east-2")

        self.agent = Agent(
            name="PlanningAgent",
            model=BedrockModel(model_id=model_id, region=region),
            system_prompt=self._get_system_prompt(),
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )

    def _get_system_prompt(self) -> str:
        return """You are an expert SOP planning agent.
Return ONLY valid JSON matching the required structure.
"""

    async def execute(self, state: SOPState) -> SOPState:
        try:
            prompt = f"""
Create a detailed SOP outline:

Topic: {state.topic}
Industry: {state.industry}
Audience: {state.target_audience}
"""

            response = await self.agent.invoke_async(prompt)
            outline_data = json.loads(response.content)

            outline = SOPOutline(**outline_data)

            state.outline = outline
            state.status = WorkflowStatus.PLANNED
            state.current_node = "planning"
            state.increment_tokens(1500)

        except Exception as e:
            state.add_error(f"Planning failed: {str(e)}")
            state.status = WorkflowStatus.FAILED

        return state



        async def __call__(self, state: SOPState) -> SOPState:
                prompt = self.build_prompt(state)
                response = await self.agent.invoke_async(prompt)
                outline_data = json.loads(response.content)
                state.outline = SOPOutline(**outline_data)
                state.status = WorkflowStatus.PLANNED
                return state


