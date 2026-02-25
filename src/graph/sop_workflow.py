"""
SOP Workflow - Fixed
"""

import logging
from strands.multiagent.graph import GraphBuilder
from src.graph.state_schema import SOPState, WorkflowStatus

# FIX: Import plain async node functions, NOT Agent objects.
#
# The full error chain was:
#   1. First attempt:  added @tool functions as nodes
#      → ValueError: Node of type 'DecoratedFunctionTool' is not supported
#   2. Second attempt: added Agent(tools=[...]) wrappers as nodes
#      → ValueError: Input prompt must be of type: str | list[ContentBlock] | Messages | None
#
# Root cause of error #2: when the graph executes a node whose executor is an
# Agent, it calls agent.stream_async(node_input) where node_input is the
# SOPState object passed between nodes. The Agent expects a string/message
# prompt, not a Pydantic state object — hence the type error.
#
# Correct pattern: register plain async functions with signature
#   async def my_node(state: SOPState) -> SOPState
# The graph calls these directly with the state object, which is exactly what
# they expect. The Strands Agent is used *inside* those functions with a
# proper string prompt.
from src.agents.planning_agent import planning_node
from src.agents.research_agent import research_node
from src.agents.content_agent import content_agent
from src.agents.formatter_agent import formatter_agent
from src.agents.qa_agent import qa_agent

logger = logging.getLogger(__name__)


def create_sop_workflow():

    gb = GraphBuilder()

    # Register plain async node functions (SOPState -> SOPState)
    gb.add_node(planning_node, "planning")
    gb.add_node(research_node, "research")
    gb.add_node(content_agent, "content")
    gb.add_node(formatter_agent, "formatter")
    gb.add_node(qa_agent, "qa")

    def should_revise(state: SOPState) -> bool:
        """Return True only when QA rejected and retries remain."""
        qa_result = getattr(state, "qa_result", None)
        if qa_result and not qa_result.approved:
            retry_count = getattr(state, "retry_count", 0)
            if retry_count < 2:
                state.retry_count = retry_count + 1
                return True
        return False

    # Linear flow
    gb.add_edge("planning", "research")
    gb.add_edge("research", "content")
    gb.add_edge("content", "formatter")
    gb.add_edge("formatter", "qa")

    # Conditional revision loop
    gb.add_edge("qa", "content", condition=should_revise)

    gb.set_entry_point("planning")

    return gb.build()


sop_workflow = create_sop_workflow()


async def generate_sop(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: list = None,
):
    initial_state = SOPState(
        topic=topic,
        industry=industry,
        target_audience=target_audience,
        requirements=requirements or [],
        workflow_id=f"sop-{hash(topic)}"
    )

    try:
        final_state = await sop_workflow.invoke_async(initial_state)
        return final_state

    except Exception as e:
        logger.error("Workflow failed: %s", e)
        initial_state.status = WorkflowStatus.FAILED
        initial_state.add_error(str(e))
        return initial_state


def generate_sop_sync(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: list = None,
):
    """Synchronous wrapper — use when not inside an existing event loop."""
    import asyncio
    return asyncio.run(generate_sop(topic, industry, target_audience, requirements))
