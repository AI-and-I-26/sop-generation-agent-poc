#from strands import Agent, create_graph
from strands import Agent
from strands.models import BedrockModel
from strands.multiagent.graph import Graph, GraphBuilder  # both are available
from pydantic import BaseModel
import boto3

class SOPState(BaseModel):
    topic: str
    outline: str = ""
    status: str = "INIT"

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name='us-east-2')

# Create Planning Agent
#planning_agent = Agent(
 #   name="PlanningAgent",
 #   model="meta.llama3-1-70b-instruct-v1:0",
  #  bedrock_client=bedrock,
  #  system_prompt="""You are an expert SOP planning agent.

# Create Planning Agent
planning_model = BedrockModel(
    model_id="arn:aws:bedrock:us-east-2:070797854596:inference-profile/us.meta.llama3-3-70b-instruct-v1:0",
    region_name="us-east-2",      # required by BedrockModel
    temperature=0.7,
    max_tokens=2048
)

planning_agent = Agent(
    model=planning_model,
    system_prompt="""You are an expert SOP planning agent.
    
Your job is to create comprehensive outlines for Standard Operating Procedures.

Output Format:
Return a JSON object with this structure:
{
  "title": "SOP Title",
  "sections": [
    {
      "name": "Section Name",
      "subsections": ["Subsection 1", "Subsection 2"]
    }
  ]
}

Always include these main sections:
1. Purpose and Scope
2. Responsibilities
3. Required Materials/Equipment
4. Step-by-step Procedures
5. Safety Considerations
6. Quality Control
7. Troubleshooting
8. References"""
)

# Test the agent
async def test_planning_agent():
    response = await planning_agent.invoke_async(
        prompt="Create an SOP outline for Chemical Spill Response in a manufacturing facility."
    )
    #print(response)

# Run test
import asyncio
asyncio.run(test_planning_agent())

