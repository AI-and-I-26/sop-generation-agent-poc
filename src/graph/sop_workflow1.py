"""
SOP Workflow - Using ONLY Strands SDK

This file replaces supervisor_agent.py and uses Strands' built-in StateGraph.
NO LangGraph needed - Strands has everything built-in!

Development Order: Step 14 (Final step!)
"""

import logging
#from strands import StateGraph
from strands.multiagent.graph import Graph, GraphBuilder  # both are available
from src.graph.state_schema import SOPState, WorkflowStatus
#from src.agents.planning_agent import planning_node
from src.agents.planning_agent import planning_agent
from src.agents.research_agent import research_agent
from src.agents.content_agent import content_agent
from src.agents.formatter_agent import formatter_agent
from src.agents.qa_agent import qa_agent

logger = logging.getLogger(__name__)


def should_revise(state: SOPState) -> str:
    """
    Conditional routing logic after QA review
    
    Args:
        state: Current SOPState
        
    Returns:
        "revise" to go back to content generation
        "finish" to end workflow
    """
    
    # Check if QA approved
    if state.qa_result and state.qa_result.approved:
        logger.info("✓ QA approved - finishing workflow")
        state.status = WorkflowStatus.COMPLETED
        return "finish"
    
    # Check max retries (limit to 2)
    if state.retry_count >= 2:
        logger.warning("⚠ Max retries (2) reached - finishing workflow")
        state.status = WorkflowStatus.COMPLETED
        state.add_error("Max retries reached")
        return "finish"
    
    # Needs revision
    logger.info(f"⟳ Needs revision - retry {state.retry_count + 1}/2")
    state.retry_count += 1
    return "revise"



def create_sop_workflow():
    """
    Planning → Research → Content → Formatter → QA → (Revise if needed) → End
    """
   
    gb = GraphBuilder()

    #print("DEBUG planning_node =",planning_agent)
    #print("TYPE =", type(planning_agent))

    # Add agents
    
    gb.add_node(planning_agent, "planning")
    gb.add_node(research_agent, "research")
    gb.add_node(content_agent, "content")
    gb.add_node(formatter_agent, "formatter")
    gb.add_node(qa_agent, "qa")

    print("gb id:", id(gb))

    # 1) Inspect registered node IDs (uses a private attr just for debugging)
    node_ids = list(getattr(gb, "_nodes", {}).keys())
    print("Registered nodes:", node_ids)

    #print(gb.nodes)

    
 # define the predicate
    def should_revise(state) -> bool:
        qa_result = state.results.get("qa")
        if not qa_result:
            return False
        return bool(getattr(qa_result, "metadata", {}) or {}.get("needs_revision", False))


    # Base DAG edges
    gb.add_edge("planning", "research")
    gb.add_edge("research", "content")
    gb.add_edge("content", "formatter")
    gb.add_edge("formatter", "qa")

    # Conditional loop
    gb.add_edge("qa", "content", condition=should_revise)

    # Entry point
    gb.set_entry_point("planning")

    # Build the executable Strands graph
  
    workflow = gb.build()

    logger.info("✓ SOP workflow built successfully")

    return workflow


# Create workflow instance
sop_workflow = create_sop_workflow()

print("DEBUG build result type:", type(sop_workflow))
print("DEBUG entry points:", [n.node_id for n in sop_workflow.entry_points])


async def generate_sop(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: list = None
) -> SOPState:
    """
    Generate SOP document using the workflow
    
    This is the main entry point for SOP generation.
    
    Args:
        topic: SOP topic/title
        industry: Industry domain
        target_audience: Target users
        requirements: Additional requirements (optional)
        
    Returns:
        Final SOPState with generated document
        
    Example:
        >>> result = await generate_sop(
        ...     topic="Fire Evacuation Procedures",
        ...     industry="Office Buildings",
        ...     target_audience="All employees"
        ... )
        >>> print(f"Status: {result.status}")
        >>> print(f"QA Score: {result.qa_result.score}")
        >>> print(result.formatted_document)
    """
    
    # Create initial state
    initial_state = SOPState(
        topic=topic,
        industry=industry,
        target_audience=target_audience,
        requirements=requirements or [],
        workflow_id=f"sop-{hash(topic)}"
    )
    
    logger.info("=" * 70)
    logger.info(f"Starting SOP Generation Workflow")
    logger.info(f"Topic: {topic}")
    logger.info(f"Industry: {industry}")
    logger.info("=" * 70)
    
    try:
        # Invoke workflow (Strands handles all execution)
        final_state = await sop_workflow.invoke_async(initial_state)
        
        # Log results
        logger.info("=" * 70)
        logger.info("Workflow Completed!")
        logger.info(f"Status: {final_state.status}")
        logger.info(f"Tokens Used: {final_state.tokens_used}")
        
        if final_state.qa_result:
            logger.info(f"QA Score: {final_state.qa_result.score}/10")
            logger.info(f"Approved: {final_state.qa_result.approved}")
        
        if final_state.errors:
            logger.warning(f"Errors: {len(final_state.errors)}")
            for error in final_state.errors:
                logger.warning(f"  - {error}")
        
        logger.info("=" * 70)
        
        return final_state
        
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}")
        initial_state.status = WorkflowStatus.FAILED
        initial_state.add_error(f"Workflow error: {str(e)}")
        return initial_state


# Synchronous wrapper for non-async contexts
def generate_sop_sync(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: list = None
) -> SOPState:
    """
    Synchronous wrapper for generate_sop
    
    Use this if you're not in an async context.
    """
    import asyncio
    return asyncio.run(generate_sop(topic, industry, target_audience, requirements))