"""
SOP Workflow - Using ONLY Strands SDK

This file replaces supervisor_agent.py and uses Strands' built-in StateGraph.
NO LangGraph needed - Strands has everything built-in!

Development Order: Step 14 (Final step!)
"""

import logging
from strands import StateGraph, END  # ✅ CORRECT: from strands (not langgraph!)
from src.graph.state_schema import SOPState, WorkflowStatus
from src.agents.planning_agent import planning_node
from src.agents.research_agent import research_node
from src.agents.content_agent import content_node
from src.agents.formatter_agent import formatter_node
from src.agents.qa_agent import qa_node

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
    Create SOP generation workflow using Strands StateGraph
    
    Workflow:
    Planning → Research → Content → Format → QA → (Revise if needed) → End
    
    Returns:
        Compiled Strands workflow
    """
    
    # Create Strands StateGraph
    workflow = StateGraph(SOPState)  # ✅ From strands package
    
    # Add all agent nodes
    workflow.add_node("planning", planning_node)
    workflow.add_node("research", research_node)
    workflow.add_node("content", content_node)
    workflow.add_node("formatter", formatter_node)
    workflow.add_node("qa", qa_node)
    
    # Set workflow entry point
    workflow.set_entry_point("planning")
    
    # Define sequential edges
    workflow.add_edge("planning", "research")
    workflow.add_edge("research", "content")
    workflow.add_edge("content", "formatter")
    workflow.add_edge("formatter", "qa")
    
    # Conditional edge from QA
    # If approved → END
    # If needs revision → back to content
    workflow.add_conditional_edges(
        "qa",
        should_revise,
        {
            "revise": "content",  # Loop back for revision
            "finish": END  # ✅ END from strands
        }
    )
    
    # Compile the workflow
    compiled_workflow = workflow.compile()
    
    logger.info("✓ SOP workflow compiled successfully")
    
    return compiled_workflow


# Create the workflow instance (singleton)
sop_workflow = create_sop_workflow()


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
        final_state = await sop_workflow.ainvoke(initial_state)
        
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
