"""
SOP Workflow

FIX: Import names in the original workflow did not match what the agent files export.
The graph was silently skipping planning, research, content, and formatter nodes
because the imported names either didn't exist or were None.

Mismatch table (old → fixed):
  planning_tool   → run_planning_node   (planning_agent__3_.py exports run_planning_node)
  research_tool   → run_research_node   (research_agent__2_.py exports run_research_node)
  content_agent   → run_content_node    (content_agent__2_.py exports run_content_node)
  formatter_agent → run_formatter_node  (formatter_agent__2_.py exports run_formatter_node)
  qa_agent        → qa_agent            (qa_agent__1_.py exports qa_agent = Agent(...)) ✅

The graph also needs workflow_id injected into the initial message so every
run_* tool can find its state in STATE_STORE. Added _make_initial_prompt() for this.
"""

import logging
import uuid

from strands.multiagent.graph import GraphBuilder

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE

# ── Import what each file ACTUALLY exports ────────────────────────────────────
from src.agents.planning_agent  import run_planning_node   # was: planning_tool
from src.agents.research_agent  import run_research_node   # was: research_tool
from src.agents.content_agent   import run_content_node    # was: content_agent
from src.agents.formatter_agent import run_formatter_node  # was: formatter_agent
from src.agents.qa_agent        import qa_agent            # ✅ unchanged
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)


def should_revise(state: SOPState) -> bool:
    """Route back to content if QA failed and retries remain."""
    if state.qa_result and not state.qa_result.approved:
        if state.retry_count < 2:
            state.retry_count += 1
            logger.info("QA failed — retry %d/2", state.retry_count)
            return True
    return False


def create_sop_workflow():
    gb = GraphBuilder()

    gb.add_node(run_planning_node,  "planning")
    gb.add_node(run_research_node,  "research")
    gb.add_node(run_content_node,   "content")
    gb.add_node(run_formatter_node, "formatter")
    gb.add_node(qa_agent,           "qa")

    gb.add_edge("planning",  "research")
    gb.add_edge("research",  "content")
    gb.add_edge("content",   "formatter")
    gb.add_edge("formatter", "qa")
    gb.add_edge("qa",        "content", condition=should_revise)

    gb.set_entry_point("planning")

    return gb.build()


sop_workflow = create_sop_workflow()


def _make_initial_prompt(workflow_id: str, topic: str) -> str:
    """
    The graph passes a single string message to the first node.
    Every run_* tool extracts workflow_id from this string to look up STATE_STORE.
    Without workflow_id in the message, all tools fail with 'no state found'.
    """
    return f"workflow_id::{workflow_id} | Generate SOP for: {topic}"


async def generate_sop(
    topic: str,
    industry: str,
    target_audience: str = "IT Qualification Engineers and System Administrators",
    requirements: list = None,
) -> SOPState:
    """
    Entry point. Creates state, registers it in STATE_STORE, then runs the graph.
    """
    workflow_id = f"sop-{uuid.uuid4().hex[:8]}"

    state = SOPState(
        topic=topic,
        industry=industry,
        target_audience=target_audience,
        requirements=requirements or [],
        workflow_id=workflow_id,
    )

    # Register state BEFORE invoking the graph so run_* tools can find it
    STATE_STORE[workflow_id] = state
    logger.info("Registered workflow_id=%s | topic='%s'", workflow_id, topic)

    initial_prompt = _make_initial_prompt(workflow_id, topic)

    try:
        final_state = await sop_workflow.invoke_async(initial_prompt)
        return final_state
    except Exception as e:
        logger.exception("Workflow FAILED wf=%s", workflow_id)
        state.status = WorkflowStatus.FAILED
        state.add_error(str(e))
        return state
