"""
SOP Workflow - Fixed for Strands Graph API

KEY INSIGHT (learned from 3 failed attempts):
  GraphBuilder.add_node() ONLY accepts Agent or MultiAgentBase instances.
  - @tool functions        → "DecoratedFunctionTool is not supported"
  - plain async functions  → "function is not supported"
  - Agent(tools=[...])     → works, BUT the graph passes a plain string between
                             nodes, not your SOPState object — so state must be
                             shared via a side channel (module-level dict store).

ARCHITECTURE:
  - A module-level STATE_STORE dict holds the live SOPState, keyed by workflow_id.
  - Each Agent node has @tool functions that read/write from STATE_STORE.
  - The graph passes a simple "workflow_id::<id>" string between nodes.
  - sop_workflow.py injects the initial state before invoking the graph,
    then reads the final state from STATE_STORE after completion.
"""

import logging
import asyncio
from strands.multiagent.graph import GraphBuilder
from src.graph.state_schema import SOPState, WorkflowStatus
from src.agents.planning_agent import planning_agent
from src.agents.research_agent import research_agent
from src.agents.content_agent import content_agent
from src.agents.formatter_agent import formatter_agent
from src.agents.qa_agent import qa_agent

# Shared state store — populated before graph invocation, read after
from src.agents.state_store import STATE_STORE

logger = logging.getLogger(__name__)


def create_sop_workflow():

    gb = GraphBuilder()

    # All nodes are Agent instances — the only type the graph supports
    gb.add_node(planning_agent,   "planning")
    gb.add_node(research_agent,   "research")
    gb.add_node(content_agent,    "content")
    gb.add_node(formatter_agent,  "formatter")
    gb.add_node(qa_agent,         "qa")

    def should_revise(state) -> bool:
        """
        Conditional edge predicate. `state` here is the Strands GraphState,
        not SOPState. We look up our SOPState from STATE_STORE using the
        workflow_id that is threaded through the graph as a string message.
        """
        # Extract workflow_id from the accumulated graph messages
        workflow_id = _extract_workflow_id_from_graph_state(state)
        if not workflow_id:
            return False

        sop_state: SOPState = STATE_STORE.get(workflow_id)
        if not sop_state:
            return False

        qa_result = getattr(sop_state, "qa_result", None)
        if qa_result and not getattr(qa_result, "approved", True):
            retry_count = getattr(sop_state, "retry_count", 0)
            if retry_count < 2:
                sop_state.retry_count = retry_count + 1
                logger.info("QA revision requested — retry %d/2", sop_state.retry_count)
                return True

        return False

    # Linear flow
    gb.add_edge("planning",  "research")
    gb.add_edge("research",  "content")
    gb.add_edge("content",   "formatter")
    gb.add_edge("formatter", "qa")

    # Conditional revision loop
    gb.add_edge("qa", "content", condition=should_revise)

    gb.set_entry_point("planning")

    return gb.build()


def _extract_workflow_id_from_graph_state(graph_state) -> str:
    """Extract our workflow_id token from the Strands GraphState messages."""
    try:
        messages = getattr(graph_state, "messages", []) or []
        for msg in reversed(messages):
            content = ""
            if isinstance(msg, dict):
                content = str(msg.get("content", ""))
            elif hasattr(msg, "content"):
                content = str(msg.content)
            if "workflow_id::" in content:
                return content.split("workflow_id::")[1].split()[0].strip()
    except Exception:
        pass
    return ""


sop_workflow = create_sop_workflow()


async def generate_sop(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: list = None,
) -> SOPState:

    initial_state = SOPState(
        topic=topic,
        industry=industry,
        target_audience=target_audience,
        requirements=requirements or [],
        workflow_id=f"sop-{abs(hash(topic))}",
    )

    # Register state so agent tools can find it
    workflow_id = initial_state.workflow_id
    STATE_STORE[workflow_id] = initial_state

    # The graph receives a plain string prompt — we embed the workflow_id so
    # each agent node can locate the SOPState via STATE_STORE
    graph_prompt = (
        f"workflow_id::{workflow_id} | "
        f"Generate a Standard Operating Procedure for: {topic} | "
        f"Industry: {industry} | Audience: {target_audience}"
    )

    logger.info("=" * 60)
    logger.info("Starting SOP Generation | Topic: %s | Industry: %s", topic, industry)
    logger.info("=" * 60)

    try:
        await sop_workflow.invoke_async(graph_prompt)

        final_state: SOPState = STATE_STORE.get(workflow_id, initial_state)

        logger.info("Workflow complete | Status: %s | Tokens: %s",
                    final_state.status, getattr(final_state, "tokens_used", "N/A"))

        return final_state

    except Exception as e:
        logger.error("Workflow failed: %s", e)
        initial_state.status = WorkflowStatus.FAILED
        initial_state.add_error(str(e))
        return initial_state

    finally:
        # Clean up store entry
        STATE_STORE.pop(workflow_id, None)


def generate_sop_sync(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: list = None,
) -> SOPState:
    """Synchronous wrapper — use when not inside an existing event loop."""
    return asyncio.run(generate_sop(topic, industry, target_audience, requirements))
