"""
Research Agent - Module 5, Section 5.1

Performs research using RAG (Bedrock Knowledge Base) and other tools.
Uses Strand Agent with Tool integration.
"""

import os
import json
import logging
from typing import Dict, List,Callable,Any
from strands import Agent,tool
#from strands.tools import Tool
from strands import tool
#from strands.types import ModelConfig
from strands.models import BedrockModel


from src.graph.state_schema import SOPState, ResearchFindings, WorkflowStatus

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Research Agent using Strand SDK with Tools
    
    Searches knowledge bases and retrieves relevant information
    for SOP generation.
    """
    
    def __init__(self):
        """Initialize Research Agent with Strand and Tools"""
               
        # Define tools for the agent
        tools = [
            self._create_kb_search_tool(),
            self._create_compliance_tool()
        ]
       
        model_id = os.getenv("MODEL_RESEARCH", "arn:aws:bedrock:us-east-2:070797854596:inference-profile/us.meta.llama3-3-70b-instruct-v1:0")
        region   = os.getenv("AWS_REGION", "us-east-2")

        self.agent = Agent(
            name="ResearchAgent",
            model=BedrockModel(model_id=model_id, region=region),
            system_prompt=self._get_system_prompt(),
            tools=tools,  # Strand handles tool calling
            temperature=0.5,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        
        logger.info("Initialized ResearchAgent with RAG tools")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for research agent"""
        return """You are a research specialist for SOP development.

Your job is to find relevant information from knowledge bases and compliance databases.

TOOLS AVAILABLE:
- search_knowledge_base: Search for similar SOPs and procedures
- get_compliance_requirements: Fetch regulatory requirements

RESEARCH STRATEGY:
1. Search knowledge base for similar SOPs
2. Identify compliance requirements
3. Extract best practices
4. Cite all sources

OUTPUT FORMAT:
Return JSON with:
{
  "similar_sops": [
    {
      "title": "SOP Title",
      "relevance": 0.95,
      "key_points": ["Point 1", "Point 2"]
    }
  ],
  "compliance_requirements": ["Regulation 1", "Regulation 2"],
  "best_practices": ["Best practice 1"],
  "sources": ["Source 1"]
}
"""
    
    
    def _create_kb_search_tool(self) -> Callable[..., Any]:
        """Create and return the Knowledge Base search tool (as a decorated function)."""
        @tool
        def search_kb(query: str, max_results: int = 5) -> str:
            """Search Bedrock Knowledge Base"""
            import boto3
            
            try:
                kb_client = boto3.client('bedrock-agent-runtime', 
                                        region_name=os.getenv('AWS_REGION', 'us-east-1'))
                kb_id = os.getenv('KNOWLEDGE_BASE_ID')
                
                response = kb_client.retrieve(
                    knowledgeBaseId=kb_id,
                    retrievalQuery={'text': query},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': max_results
                        }
                    }
                )
                
                results = []
                for result in response.get('retrievalResults', []):
                    results.append({
                        'content': result['content']['text'],
                        'score': result['score'],
                        'source': result.get('location', {}).get('s3Location', {}).get('uri', 'Unknown')
                    })
                
                return json.dumps(results)
                
            except Exception as e:
                logger.error(f"KB search error: {e}")
                return json.dumps({"error": str(e)})
        
        return Tool(
            name="search_knowledge_base",
            description="Search Bedrock Knowledge Base for similar SOPs and procedures",
            function=search_kb,
            parameters={
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default 5)"
                }
            }
        )
    
    def _create_compliance_tool(self) -> Callable[..., Any]:
        """Create compliance requirements tool"""        
        @tool
        def get_compliance(industry: str, topic: str) -> str:
            """Get compliance requirements"""
            # Placeholder - integrate with compliance API
            compliance_map = {
                "Manufacturing": ["OSHA 1910", "ISO 9001"],
                "Healthcare": ["HIPAA", "FDA 21 CFR"],
                "Laboratory": ["CLIA", "CAP Standards"]
            }
            
            requirements = compliance_map.get(industry, ["General Safety"])
            return json.dumps({
                "industry": industry,
                "requirements": requirements
            })
        
        return Tool(
            name="get_compliance_requirements",
            description="Get relevant compliance and regulatory requirements",
            function=get_compliance,
            parameters={
                "industry": {"type": "string"},
                "topic": {"type": "string"}
            }
        )
    
    async def conduct_research(
        self,
        topic: str,
        industry: str,
        outline: Dict
    ) -> ResearchFindings:
        """
        Conduct research using tools
        
        Args:
            topic: SOP topic
            industry: Industry domain
            outline: Outline to research
            
        Returns:
            ResearchFindings object
        """
        
        prompt = f"""Research the following SOP topic:

Topic: {topic}
Industry: {industry}

Use the available tools to:
1. Search for similar SOPs in the knowledge base
2. Get compliance requirements for this industry
3. Identify best practices

Return comprehensive research findings in JSON format."""
        
        try:
            # Invoke agent (Strand handles tool calling automatically)
            response = await self.agent.invoke_async(prompt)
            
            # Parse response
            findings_data = json.loads(response.content)
            
            # Validate with Pydantic
            findings = ResearchFindings(**findings_data)
            
            logger.info(f"Research found {len(findings.similar_sops)} similar SOPs")
            
            return findings
            
        except Exception as e:
            logger.error(f"Research failed: {e}")
            raise
    
    async def execute(self, state: SOPState) -> SOPState:
        """Execute research agent"""
        try:
            findings = await self.conduct_research(
                topic=state.topic,
                industry=state.industry,
                outline=state.outline.dict() if state.outline else {}
            )
            
            state.research = findings
            state.status = WorkflowStatus.RESEARCHED
            state.current_node = "research"
            state.increment_tokens(2000)
            
        except Exception as e:
            state.add_error(f"Research failed: {str(e)}")
            state.status = WorkflowStatus.FAILED
        
        return state

"""
# Standalone node function for Strand StateGraph
async def research_node(state: SOPState) -> SOPState:
    agent = ResearchAgent()
    return await agent.execute(state) """

    
@tool
async def research_tool(state: SOPState) -> SOPState:
    #"""Planning tool: executes the PlanningAgent logic."""
    agent = ResearchAgent()
    return await agent.execute(state)

# Create the actual graph node executor
research_agent = Agent(
    tools=[research_tool],
    #system_prompt="Plan SOP steps before research."
)