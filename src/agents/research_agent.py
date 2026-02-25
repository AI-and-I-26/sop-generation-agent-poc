"""
Research Agent - Module 5, Section 5.1

Performs research using RAG (Bedrock Knowledge Base) and other tools.
Uses Strand Agent with Tool integration.
"""

import os
import json
import logging
from typing import Dict

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, ResearchFindings, WorkflowStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# FIX: Tool definitions must be module-level @tool-decorated functions.
#
# The original code defined tools inside helper methods (_create_kb_search_tool,
# _create_compliance_tool) and then wrapped them in a Tool() constructor call.
# Two problems:
#   1. `Tool` was never imported (the import line was commented out), causing
#      a NameError at runtime.
#   2. Strands does not use a Tool() wrapper at all — you simply pass the
#      @tool-decorated callable directly to Agent(tools=[...]).
#
# Solution: move the logic to module-level @tool functions and pass them
# straight to the Agent constructor.
# ---------------------------------------------------------------------------

@tool
def search_knowledge_base(query: str, max_results: int = 5) -> str:
    """Search Bedrock Knowledge Base for similar SOPs and procedures.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).
    """
    import boto3

    try:
        kb_client = boto3.client(
            "bedrock-agent-runtime",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )
        kb_id = os.getenv("KNOWLEDGE_BASE_ID")

        response = kb_client.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {"numberOfResults": max_results}
            },
        )

        results = []
        for result in response.get("retrievalResults", []):
            results.append({
                "content": result["content"]["text"],
                "score": result["score"],
                "source": result.get("location", {})
                    .get("s3Location", {})
                    .get("uri", "Unknown"),
            })

        return json.dumps(results)

    except Exception as e:
        logger.error("KB search error: %s", e)
        return json.dumps({"error": str(e)})


@tool
def get_compliance_requirements(industry: str, topic: str) -> str:
    """Get compliance and regulatory requirements for an industry and topic.

    Args:
        industry: The industry name (e.g. 'Manufacturing', 'Healthcare').
        topic: The SOP topic for which compliance is needed.
    """
    # Placeholder — replace with a real compliance API call as needed
    compliance_map = {
        "Manufacturing": ["OSHA 1910", "ISO 9001"],
        "Healthcare": ["HIPAA", "FDA 21 CFR"],
        "Laboratory": ["CLIA", "CAP Standards"],
    }
    requirements = compliance_map.get(industry, ["General Safety"])
    return json.dumps({"industry": industry, "requirements": requirements})


# ---------------------------------------------------------------------------
# ResearchAgent class
# ---------------------------------------------------------------------------

class ResearchAgent:
    """
    Research Agent using Strand SDK with Tools.
    Searches knowledge bases and retrieves relevant information for SOP generation.
    """

    def __init__(self):
        model_id = os.getenv(
            "MODEL_RESEARCH",
            "arn:aws:bedrock:us-east-2:070797854596:inference-profile/us.meta.llama3-3-70b-instruct-v1:0",
        )
        region = os.getenv("AWS_REGION", "us-east-2")

        # FIX: Removed unsupported `temperature` and `response_format` kwargs.
        # Pass @tool functions directly — no Tool() wrapper needed.
        self.agent = Agent(
            name="ResearchAgent",
            model=BedrockModel(model_id=model_id, region=region),
            system_prompt=self._get_system_prompt(),
            tools=[search_knowledge_base, get_compliance_requirements],
            max_tokens=2048,
        )

        logger.info("Initialized ResearchAgent with RAG tools")

    def _get_system_prompt(self) -> str:
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

    async def conduct_research(self, topic: str, industry: str, outline: Dict) -> ResearchFindings:

        prompt = f"""Research the following SOP topic:

Topic: {topic}
Industry: {industry}

Use the available tools to:
1. Search for similar SOPs in the knowledge base
2. Get compliance requirements for this industry
3. Identify best practices

Return comprehensive research findings in JSON format."""

        # FIX: Strands AgentResult must be converted with str() — NOT .content
        response = await self.agent.invoke_async(prompt)
        response_text = str(response).strip()

        # Strip markdown code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        findings_data = json.loads(response_text)
        findings = ResearchFindings(**findings_data)

        logger.info("Research found %d similar SOPs", len(findings.similar_sops))
        return findings

    async def execute(self, state: SOPState) -> SOPState:
        try:
            findings = await self.conduct_research(
                topic=state.topic,
                industry=state.industry,
                outline=state.outline.dict() if state.outline else {},
            )
            state.research = findings
            state.status = WorkflowStatus.RESEARCHED
            state.current_node = "research"
            state.increment_tokens(2000)

        except Exception as e:
            logger.error("Research failed: %s", e)
            state.add_error(f"Research failed: {str(e)}")
            state.status = WorkflowStatus.FAILED

        return state


# ---------------------------------------------------------------------------
# Graph node wiring
# ---------------------------------------------------------------------------

@tool
async def research_tool(state: SOPState) -> SOPState:
    """Research tool: executes the ResearchAgent logic."""
    agent = ResearchAgent()
    return await agent.execute(state)


# This Agent is what gets imported by sop_workflow.py and added as a graph node.
# GraphBuilder requires an Agent instance — NOT the raw research_tool function.
research_agent = Agent(
    tools=[research_tool],
)
