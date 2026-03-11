"""
sop_workflow.py — SOP Generation Workflow Orchestrator.

ARCHITECTURE OVERVIEW:
    This file builds and runs the Strands multi-agent graph that produces a
    complete Standard Operating Procedure from a topic, industry, and audience.

    Five Agent nodes are wired into a directed graph:

        [planning] → [research] → [content] → [formatter] → [qa]
                                     ↑                         │
                                     └─────── (revision loop) ─┘

    The graph passes a simple "workflow_id::<id>" string between nodes.
    Actual SOPState data is held in a module-level STATE_STORE dict and
    accessed by each agent's @tool function.

KEY DESIGN DECISIONS:
    1. GraphBuilder.add_node() only accepts Agent instances.
       Plain functions and @tool decorators are not supported as nodes.
       Each agent wraps its @tool in an outer Agent that immediately delegates.

    2. The revision loop: if QA does not approve and retry_count < 2,
       the should_revise() conditional edge routes back to the content node.
       The content agent picks up qa_policy_feedback to rewrite failing sections.

    3. State cleanup: STATE_STORE entries are removed in a finally block to
       prevent memory leaks on long-running servers.

ENVIRONMENT VARIABLES:
    MODEL_PLANNING   — Bedrock model ARN for planning agent
    MODEL_RESEARCH   — Bedrock model ARN for research agent
    MODEL_CONTENT    — Bedrock model ARN for content agent
    MODEL_FORMATTER  — Bedrock model ARN for formatter agent
    MODEL_QA         — Bedrock model ARN for QA agent
    AWS_REGION       — AWS region (default: us-east-2)
    KNOWLEDGE_BASE_ID — Bedrock KB ID for research agent

USAGE:
    # Async (inside an event loop):
    from src.graph.sop_workflow import generate_sop
    state = await generate_sop(topic="...", industry="...", target_audience="...")

    # Synchronous (standalone script):
    from src.graph.sop_workflow import generate_sop_sync
    state = generate_sop_sync(topic="...", industry="...", target_audience="...")
"""

import asyncio
import logging

from strands.multiagent.graph import GraphBuilder

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE

# Import all five agent nodes — each is a Strands Agent instance
import boto3
from botocore.config import Config as _BotoCfg

from src.agents.planning_agent  import planning_agent
from src.agents.research_agent  import research_agent
from src.agents.content_agent   import content_agent
from src.agents.formatter_agent import formatter_agent
from src.agents.qa_agent        import qa_agent
from src.utils.crl_docx_writer  import build_crl_docx


# ---------------------------------------------------------------------------
# STRANDS TIMEOUT PATCH
# ---------------------------------------------------------------------------
# BedrockModel silently ignores client_config (see strands-agents issue #815).
# The Strands agent loop makes a second .converse() call after each tool call
# to check if it should continue — this uses the default 120s boto3 timeout
# and fails for any long-running node.
# Fix: replace .client on every BedrockModel with a boto3 client that has
# STRANDS_READ_TIMEOUT (default 600s) applied.
def _patch_agent_timeout(agent, read_timeout: int = None) -> None:
    """Replace the BedrockModel's internal boto3 client with a high-timeout one."""
    import os
    _to = read_timeout or int(os.getenv("STRANDS_READ_TIMEOUT", "600"))
    _region = os.getenv("AWS_REGION", "us-east-2")
    high_timeout_client = boto3.client(
        "bedrock-runtime",
        region_name=_region,
        config=_BotoCfg(
            read_timeout=_to,
            connect_timeout=10,
            retries={"max_attempts": 1, "mode": "standard"},
        ),
    )
    try:
        model = agent.model  # BedrockModel instance
        model.client = high_timeout_client
        logger.info(
            "Patched BedrockModel.client timeout=%ds on agent '%s'",
            _to, getattr(agent, 'name', str(agent)),
        )
    except Exception as e:
        logger.warning("Could not patch agent timeout: %s", e)


# Patch all 5 node agents at import time
_STRANDS_READ_TIMEOUT = int(__import__('os').getenv('STRANDS_READ_TIMEOUT', '600'))
for _agent in [planning_agent, research_agent, content_agent, formatter_agent, qa_agent]:
    _patch_agent_timeout(_agent, _STRANDS_READ_TIMEOUT)

logger = logging.getLogger(__name__)


# ── CONDITIONAL EDGE ───────────────────────────────────────────────────────────

def should_revise(graph_state) -> bool:
    """
    Conditional edge predicate: should the pipeline loop back to content?

    Called by Strands after the QA node completes.  Reads SOPState from
    STATE_STORE using the workflow_id embedded in the accumulated graph messages.

    Returns True  → route back to content node (revision)
    Returns False → exit graph (done)

    Revision is allowed at most twice (retry_count < 2).
    """
    workflow_id = _extract_workflow_id(graph_state)
    if not workflow_id:
        logger.debug("should_revise: no workflow_id found in graph state")
        return False

    sop_state: SOPState = STATE_STORE.get(workflow_id)
    if not sop_state:
        logger.debug("should_revise: no SOPState found for workflow_id=%s", workflow_id)
        return False

    qa_result = getattr(sop_state, "qa_result", None)
    if qa_result and not getattr(qa_result, "approved", True):
        retry_count = getattr(sop_state, "retry_count", 0)
        if retry_count < 2:
            sop_state.retry_count = retry_count + 1
            logger.info(
                "QA revision requested — retry %d/2 | score=%.1f | workflow_id=%s",
                sop_state.retry_count, qa_result.score, workflow_id
            )
            return True
        else:
            logger.info(
                "Revision budget exhausted after %d retries | workflow_id=%s",
                retry_count, workflow_id
            )

    return False


def _extract_workflow_id(graph_state) -> str:
    """
    Extract the workflow_id token from Strands GraphState accumulated messages.

    The token is embedded as "workflow_id::<id>" in every message string that
    flows through the graph, so we can find it in any message.
    """
    try:
        messages = getattr(graph_state, "messages", []) or []
        for msg in reversed(messages):     # most recent messages first
            content = ""
            if isinstance(msg, dict):
                content = str(msg.get("content", ""))
            elif hasattr(msg, "content"):
                content = str(msg.content)
            if "workflow_id::" in content:
                return content.split("workflow_id::")[1].split()[0].strip()
    except Exception as e:
        logger.debug("_extract_workflow_id error: %s", e)
    return ""


# ── GRAPH CONSTRUCTION ─────────────────────────────────────────────────────────

def create_sop_workflow():
    """
    Build and return the compiled Strands Graph.

    Node order:
        planning → research → content → formatter → qa
                                  ↑                   │
                                  └─ (if not approved) ┘

    Edges:
        Linear flow through all five nodes.
        Conditional edge from qa back to content (via should_revise).
    """
    gb = GraphBuilder()

    # Register all five agent nodes.
    # The string name is used in log messages and edge definitions.
    gb.add_node(planning_agent,   "planning")
    gb.add_node(research_agent,   "research")
    gb.add_node(content_agent,    "content")
    gb.add_node(formatter_agent,  "formatter")
    gb.add_node(qa_agent,         "qa")

    # Linear forward edges
    gb.add_edge("planning",  "research")
    gb.add_edge("research",  "content")
    gb.add_edge("content",   "formatter")
    gb.add_edge("formatter", "qa")

    # Conditional revision edge: qa → content only when should_revise() is True
    gb.add_edge("qa", "content", condition=should_revise)

    # Entry point: the first node to receive the initial graph message
    gb.set_entry_point("planning")

    return gb.build()


# Build the workflow at import time so it can be reused across calls.
sop_workflow = create_sop_workflow()


# ── MAIN ENTRY POINTS ─────────────────────────────────────────────────────────

async def generate_sop(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: list = None,
) -> SOPState:
    """
    Generate a complete SOP document asynchronously.

    Steps:
      1. Create an SOPState and register it in STATE_STORE.
      2. Build the initial graph message string (embeds workflow_id).
      3. Invoke the Strands graph asynchronously.
      4. Read the final SOPState from STATE_STORE.
      5. Clean up STATE_STORE.

    Args:
        topic           : The SOP subject (e.g. "IT Infrastructure Qualification").
        industry        : Industry domain (e.g. "Information Technology (IT)").
        target_audience : Primary readership (e.g. "IT Qualification Engineers").
        requirements    : Optional list of additional requirements.

    Returns:
        Final SOPState containing the formatted document and QA result.
    """
    # ── Initialise state ────────────────────────────────────────────────
    initial_state = SOPState(
        topic=topic,
        industry=industry,
        target_audience=target_audience,
        requirements=requirements or [],
        workflow_id=f"sop-{abs(hash(topic + industry))}",
    )
    workflow_id = initial_state.workflow_id

    # Register state so agent @tool functions can find it by workflow_id
    STATE_STORE[workflow_id] = initial_state

    # ── Build graph prompt ───────────────────────────────────────────────
    # The workflow_id is embedded in the string so every downstream node
    # can call STATE_STORE.get(workflow_id) to access the shared state.
    graph_prompt = (
        f"workflow_id::{workflow_id} | "
        f"Generate a Standard Operating Procedure for: {topic} | "
        f"Industry: {industry} | Audience: {target_audience}"
    )

    logger.info("=" * 60)
    logger.info("SOP Generation START | topic='%s' | industry='%s'", topic, industry)
    logger.info("workflow_id: %s", workflow_id)
    logger.info("=" * 60)

    try:
        # ── Run the graph ─────────────────────────────────────────────────
        await sop_workflow.invoke_async(graph_prompt)

        # ── Read final state ──────────────────────────────────────────────
        final_state: SOPState = STATE_STORE.get(workflow_id, initial_state)

        logger.info(
            "SOP Generation COMPLETE | status=%s | tokens=%s | kb_hits=%s",
            final_state.status,
            getattr(final_state, "tokens_used", "N/A"),
            getattr(final_state, "kb_hits",     "N/A"),
        )

        if getattr(final_state, "qa_result", None):
            logger.info(
                "QA Result | score=%.1f | approved=%s",
                final_state.qa_result.score,
                final_state.qa_result.approved,
            )

        # ── Generate CRL-style .docx with per-page header/footer ─────────
        _formatted_md = (
            getattr(final_state, "formatted_markdown", None) or
            getattr(final_state, "formatted_document", None) or ""
        )
        if _formatted_md:
            try:
                import os as _os, datetime as _dt
                _title = (
                    (final_state.outline.title if getattr(final_state, "outline", None) else None)
                    or final_state.topic
                )
                _doc_id   = getattr(final_state, "document_id",    None) or f"SOP-{_dt.datetime.now().strftime('%Y%m%d-%H%M')}"
                _version  = getattr(final_state, "sop_version",    "1.0")
                _eff_date = getattr(final_state, "effective_date",  _dt.datetime.now().strftime("%d/%b/%Y"))
                _docx_bytes = build_crl_docx(
                    title=_title,
                    document_id=_doc_id,
                    version=_version,
                    effective_date=_eff_date,
                    markdown_body=_formatted_md,
                )
                _safe_name = "".join(
                    c if c.isalnum() or c in (" ", "-", "_") else "_"
                    for c in final_state.topic
                ).strip().replace(" ", "_")[:60]
                _out_dir  = _os.getenv("SOP_OUTPUT_DIR", "outputs")
                _os.makedirs(_out_dir, exist_ok=True)
                _out_path = _os.path.join(_out_dir, f"{_safe_name}_{workflow_id[-8:]}.docx")
                with open(_out_path, "wb") as _f:
                    _f.write(_docx_bytes)
                final_state.docx_path = _out_path
                logger.info("CRL .docx written — %d bytes | path=%s", len(_docx_bytes), _out_path)
            except Exception as _docx_err:
                logger.warning("CRL .docx generation failed (non-fatal): %s", _docx_err, exc_info=True)
        else:
            logger.warning("No formatted content — skipping .docx generation | workflow_id=%s", workflow_id)

        return final_state

    except Exception as e:
        logger.error("Workflow failed with unhandled exception: %s", e, exc_info=True)
        initial_state.status = WorkflowStatus.FAILED
        initial_state.add_error(str(e))
        return initial_state

    finally:
        # Always clean up — prevents state leaks on long-running servers
        STATE_STORE.pop(workflow_id, None)
        logger.debug("STATE_STORE entry removed for workflow_id=%s", workflow_id)


def generate_sop_sync(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: list = None,
) -> SOPState:
    """
    Synchronous wrapper around generate_sop().

    Use this when calling from a script or REPL that does not already
    have a running event loop.  Do NOT call from within an async context
    (use await generate_sop(...) instead to avoid loop nesting errors).
    """
    return asyncio.run(generate_sop(topic, industry, target_audience, requirements))
