"""
SOP Workflow - Fixed
"""

import logging
from strands.multiagent.graph import GraphBuilder
from src.graph.state_schema import SOPState, WorkflowStatus
from src.agents.planning_agent import PlanningAgent
#from src.agents.planning_agent import planning_tool
from src.agents.research_agent import research_node
from src.agents.content_agent import content_agent
from src.agents.formatter_agent import formatter_agent
from src.agents.qa_agent import qa_agent

logger = logging.getLogger(__name__)


def should_revise(state: SOPState) -> bool:
    if state.qa_result and not state.qa_result.approved:
        if state.retry_count < 2:
            state.retry_count += 1
            return True
    return False


def create_sop_workflow():

    gb = GraphBuilder()

    planning_node = PlanningAgent()

    # ✅ Add correct node functions
    gb.add_node(planning_node, "planning")
    gb.add_node(research_node, "research")
    gb.add_node(content_agent, "content")
    gb.add_node(formatter_agent, "formatter")
    gb.add_node(qa_agent, "qa")

    # Flow
    gb.add_edge("planning", "research")
    gb.add_edge("research", "content")
    gb.add_edge("content", "formatter")
    gb.add_edge("formatter", "qa")

    # Conditional loop
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
        initial_state.status = WorkflowStatus.FAILED
        initial_state.add_error(str(e))
        return initial_state
