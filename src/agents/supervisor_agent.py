"""
Supervisor Agent - Module 5, Section 5.2

Orchestrates the multi-agent workflow using Strand StateGraph.
Manages routing, error handling, and retry logic.
"""

import logging
from typing import Literal
from strands import StateGraph, END

from src.graph.state_schema import SOPState, WorkflowStatus
from src.agents.planning_agent import planning_node
from src.agents.research_agent import research_node
from src.agents.content_agent import content_node
from src.agents.formatter_agent import formatter_node
from src.agents.qa_agent import qa_node

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent using Strand StateGraph
    
    Orchestrates the complete SOP generation workflow:
    Planning → Research → Content → Format → QA → (Revision if needed) → Complete
    """
    
    def __init__(self):
        """Initialize Supervisor with Strand StateGraph"""
        
        # Create Strand StateGraph
        self.graph = StateGraph(state_schema=SOPState)
        
        # Add all agent nodes
        self.graph.add_node("planning", planning_node)
        self.graph.add_node("research", research_node)
        self.graph.add_node("content", content_node)
        self.graph.add_node("formatter", formatter_node)
        self.graph.add_node("qa", qa_node)
        self.graph.add_node("increment_retry", self._increment_retry_node)
        
        # Set entry point
        self.graph.set_entry_point("planning")
        
        # Define workflow edges
        self.graph.add_edge("planning", "research")
        self.graph.add_edge("research", "content")
        self.graph.add_edge("content", "formatter")
        self.graph.add_edge("formatter", "qa")
        
        # Conditional edge from QA - approve or revise
        self.graph.add_conditional_edges(
            "qa",
            self._should_revise,
            {
                "revise": "increment_retry",  # Needs revision
                "finish": END  # Approved
            }
        )
        
        # After retry increment, go back to content generation
        self.graph.add_edge("increment_retry", "content")
        
        # Compile the graph
        self.workflow = self.graph.compile()
        
        logger.info("Initialized Supervisor with complete workflow graph")
    
    def _should_revise(self, state: SOPState) -> Literal["revise", "finish"]:
        """
        Conditional routing logic after QA
        
        Args:
            state: Current SOPState
            
        Returns:
            "revise" if needs revision and retries available
            "finish" if approved or max retries reached
        """
        
        # Check if QA approved
        if state.qa_result and state.qa_result.approved:
            logger.info("✓ QA approved - finishing workflow")
            state.status = WorkflowStatus.COMPLETED
            return "finish"
        
        # Check retry count (max 2 retries)
        if state.retry_count >= 2:
            logger.warning("⚠ Max retries reached - finishing with current version")
            state.status = WorkflowStatus.COMPLETED
            state.add_error("Max retries reached, completed with current quality score")
            return "finish"
        
        # Needs revision and retries available
        logger.info(f"⟳ Revision needed (retry {state.retry_count + 1}/2)")
        return "revise"
    
    async def _increment_retry_node(self, state: SOPState) -> SOPState:
        """
        Increment retry counter
        
        Args:
            state: Current SOPState
            
        Returns:
            Updated SOPState
        """
        state.retry_count += 1
        state.current_node = "retry"
        logger.info(f"Retry attempt: {state.retry_count}")
        return state
    
    async def generate_sop(
        self,
        topic: str,
        industry: str,
        target_audience: str,
        requirements: list = None
    ) -> SOPState:
        """
        Generate SOP using complete workflow
        
        Args:
            topic: SOP topic
            industry: Industry domain
            target_audience: Target users
            requirements: Additional requirements
            
        Returns:
            Final SOPState with generated document
        """
        
        # Create initial state
        initial_state = SOPState(
            topic=topic,
            industry=industry,
            target_audience=target_audience,
            requirements=requirements or [],
            workflow_id=f"sop-{hash(topic)}"
        )
        
        logger.info(f"Starting SOP generation workflow for: {topic}")
        
        try:
            # Run workflow (Strand handles execution)
            final_state = await self.workflow.ainvoke(initial_state)
            
            logger.info(f"Workflow completed. Status: {final_state.status}")
            logger.info(f"Total tokens used: {final_state.tokens_used}")
            logger.info(f"QA Score: {final_state.qa_result.score if final_state.qa_result else 'N/A'}")
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            initial_state.status = WorkflowStatus.FAILED
            initial_state.add_error(f"Workflow error: {str(e)}")
            return initial_state


# Convenience function for standalone use
async def generate_sop(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: list = None
) -> SOPState:
    """
    Convenience function to generate SOP
    
    Args:
        topic: SOP topic
        industry: Industry
        target_audience: Target users
        requirements: Additional requirements
        
    Returns:
        Completed SOPState
    """
    supervisor = SupervisorAgent()
    return await supervisor.generate_sop(
        topic=topic,
        industry=industry,
        target_audience=target_audience,
        requirements=requirements
    )
