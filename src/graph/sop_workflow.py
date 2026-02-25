"""
SOP Workflow - Fixed
"""

import logging
from strands.multiagent.graph import GraphBuilder
from src.graph.state_schema import SOPState, WorkflowStatus

# FIX: Import the Agent objects (planning_agent, research_agent), NOT the raw
# @tool-decorated functions (planning_tool, research_tool).
# GraphBuilder.add_node() only accepts Strands Agent instances as node executors.
# Passing a DecoratedFunctionTool raises:
#   ValueError: Node 'planning' of type
#     '<class 'strands.tools.decorator.DecoratedFunctionTool'>' is not supported
from src.agents.planning_agent import planning_agent
from src.agents.research_agent import research_agent
from src.agents.content_agent import content_agent
from src.agents.formatter_agent import formatter_agent
from src.agents.qa_agent import qa_agent

logger = logging.getLogger(__name__)


def create_sop_workflow():

    gb = GraphBuilder()

    # Add Agent objects as nodes (NOT @tool functions)
    gb.add_node(planning_agent, "planning")
    gb.add_node(research_agent, "research")
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
