"""
Research Agent - Module 5, Section 5.1

Performs research using RAG (Bedrock Knowledge Base) and other tools.

GRAPH INTEGRATION PATTERN: same as planning_agent.py — see that file for the
full explanation.  The outer Agent (research_agent) is the graph node; it
calls run_research via tool, which reads/writes STATE_STORE.
"""

import os
import json
import logging
from typing import Dict

from strands import Agent, tool
from strands.models import BedrockModel

from src.graph.state_schema import SOPState, ResearchFindings, WorkflowStatus
from src.agents.state_store import STATE_STORE

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain tools used by the inner LLM agent
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
    compliance_map = {
        "Manufacturing": ["OSHA 1910", "ISO 9001"],
        "Healthcare": ["HIPAA", "FDA 21 CFR"],
        "Laboratory": ["CLIA", "CAP Standards"],
    }
    requirements = compliance_map.get(industry, ["General Safety"])
    return json.dumps({"industry": industry, "requirements": requirements})


# ---------------------------------------------------------------------------
# Inner LLM agent (string prompt in → string findings out)
# ---------------------------------------------------------------------------

def _make_llm_agent() -> Agent:
    model_id = os.getenv(
        "MODEL_RESEARCH",
        "arn:aws:bedrock:us-east-2:070797854596:inference-profile/us.meta.llama3-3-70b-instruct-v1:0",
    )
    region = os.getenv("AWS_REGION", "us-east-2")

    return Agent(
        name="ResearchLLM",
        model=BedrockModel(model_id=model_id, region=region),
        system_prompt="""You are a research specialist for SOP development.
Find relevant information from knowledge bases and compliance databases.

TOOLS: search_knowledge_base, get_compliance_requirements

STRATEGY:
1. Search knowledge base for similar SOPs
2. Get compliance requirements for the industry
3. Extract best practices and cite sources

OUTPUT FORMAT — Return JSON only:
{
  "similar_sops": [{"title": "...", "relevance": 0.95, "key_points": ["..."]}],
  "compliance_requirements": ["Regulation 1"],
  "best_practices": ["Best practice 1"],
  "sources": ["Source 1"]
}""",
        tools=[search_knowledge_base, get_compliance_requirements],
        max_tokens=2048,
    )


# ---------------------------------------------------------------------------
# Graph-level tool — called by the research_agent node
# ---------------------------------------------------------------------------

@tool
async def run_research(prompt: str) -> str:
    """Execute the SOP research step.

    Reads the SOPState identified by the workflow_id embedded in the prompt,
    conducts research using knowledge base and compliance tools, saves findings
    to STATE_STORE, and returns a summary string for the next graph node.

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
        llm = _make_llm_agent()

        outline_summary = ""
        if state.outline:
            sections = [s.title for s in (state.outline.sections or [])]
            outline_summary = f"Outline sections: {', '.join(sections[:5])}"

        research_prompt = (
            f"Research the following SOP topic:\n"
            f"Topic: {state.topic}\n"
            f"Industry: {state.industry}\n"
            f"{outline_summary}\n\n"
            f"Use the available tools to search the knowledge base and get "
            f"compliance requirements. Return findings as JSON."
        )

        response = await llm.invoke_async(research_prompt)
        response_text = str(response).strip()

        # Strip markdown code fences if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        findings_data = json.loads(response_text)
        findings = ResearchFindings(**findings_data)

        state.research = findings
        state.status = WorkflowStatus.RESEARCHED
        state.current_node = "research"
        state.increment_tokens(2000)

        logger.info("Research complete — %d similar SOPs | workflow_id=%s",
                    len(findings.similar_sops), workflow_id)

        return (
            f"workflow_id::{workflow_id} | "
            f"Research complete: found {len(findings.similar_sops)} similar SOPs, "
            f"{len(findings.compliance_requirements)} compliance requirements"
        )

    except Exception as e:
        logger.error("Research failed: %s", e)
        state.add_error(f"Research failed: {str(e)}")
        state.status = WorkflowStatus.FAILED
        return f"workflow_id::{workflow_id} | Research FAILED: {e}"


# ---------------------------------------------------------------------------
# The Agent node registered with GraphBuilder
# ---------------------------------------------------------------------------

research_agent = Agent(
    name="ResearchNode",
    system_prompt=(
        "You are the research node in an SOP generation pipeline. "
        "When you receive a message, IMMEDIATELY call the run_research tool "
        "with the full message as the prompt argument. "
        "Do not add any commentary — just call the tool and return its result."
    ),
    tools=[run_research],
)
