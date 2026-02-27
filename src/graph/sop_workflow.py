"""
SOP Workflow - Fixed for Strands Graph API (Option B: client-side tool execution)

KEY POINTS:
  - GraphBuilder.add_node() accepts Agent or MultiAgentBase.
  - We provide a lightweight LocalNodeAgent that calls local node runner functions
    (e.g., run_planning_node) which perform the *actual* work client-side and
    mutate STATE_STORE.
  - The graph passes a message containing 'workflow_id::<id> ...' between nodes.
  - STATE_STORE is the side channel holding the live SOPState throughout the graph.

This avoids relying on server-side tool use and fixes the 'event loop is already running'
and '0-byte file' issues by ensuring node handlers are awaited inside an async graph.
It also fixes empty-prompt extraction when the graph passes a list of messages.
"""

import logging
import asyncio
import time
from typing import Any, Optional, Dict, List

from strands.multiagent.graph import GraphBuilder
# If this import path differs in your environment, change it:
from strands.multiagent.base import MultiAgentBase  # adjust if needed

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE

# ---- Import the node runner entry points (client-side executors) ----
# IMPORTANT: These are async wrappers that `await` the underlying coroutine work.
from src.agents.planning_agent import run_planning_node
from src.agents.research_agent import run_research_node
from src.agents.content_agent import run_content_node
from src.agents.formatter_agent import run_formatter_node
from src.agents.qa_agent import run_qa_node

logger = logging.getLogger(__name__)

REVISION_MAX = 2  # max content<->qa revision cycles


# -----------------------------------------------------------------------------
# Local compatibility result object (DO NOT import the framework's class)
# -----------------------------------------------------------------------------
class MultiAgentResult:
    """
    Compatibility shim to satisfy strands.multiagent.graph expectations.

    Observed attributes the graph reads:
      - output (str)               : node output string propagated to next node
      - execution_time (float)     : seconds
      - messages (list)            : message list (optional)
      - tokens (dict)              : per-node token/usage (optional)
      - accumulated_usage (dict)   : cumulative usage across the graph
      - accumulated_metrics (dict) : cumulative metrics across the graph
      - execution_count (int)      : number of executions for this node
      - results (dict)             : nested node results (for fan-out scenarios)
    """
    def __init__(
        self,
        output: str,
        execution_time: float = 0.0,
        messages: Optional[List[dict]] = None,
        tokens: Optional[Dict[str, Any]] = None,
        accumulated_usage: Optional[Dict[str, Any]] = None,
        accumulated_metrics: Optional[Dict[str, Any]] = None,
        execution_count: int = 1,
        results: Optional[Dict[str, "MultiAgentResult"]] = None,
    ):
        self.output = output
        self.execution_time = execution_time
        self.messages = messages or []
        self.tokens = tokens or {}
        self.accumulated_usage = accumulated_usage or {}
        self.accumulated_metrics = accumulated_metrics or {}
        self.execution_count = execution_count
        self.results = results or {}


# -----------------------------------------------------------------------------
# Minimal MultiAgentBase wrapper for client-side node execution
# -----------------------------------------------------------------------------
class LocalNodeAgent(MultiAgentBase):
    """
    A thin wrapper to make a plain Python function/coroutine look like a Strands Agent
    for GraphBuilder. It executes client-side logic and returns a result object.

    The wrapped callable should accept a single 'prompt: str' and return a string
    (sync) or 'awaitable[str]' (async). In Option B, these call run_*_node which
    mutate STATE_STORE and return a summary string for the next node.
    """
    def __init__(self, name: str, handler):
        # DO NOT call super().__init__(...) — base may not accept args
        self._name = name
        self._handler = handler

    @property
    def name(self) -> str:
        return self._name

    # Must match what MultiAgentBase.stream_async() calls:
    # await agent.invoke_async(task, invocation_state, **kwargs)
    async def invoke_async(self, task, invocation_state=None, **kwargs) -> MultiAgentResult:
        import asyncio as _asyncio  # avoid shadowing top-level

        logger.debug(
            "LocalNodeAgent[%s].invoke_async called | task_type=%s | kwargs=%s",
            self._name, type(task).__name__, list(kwargs.keys())
        )

        def _extract_prompt(task_obj, inv_state, kw) -> str:
            """
            Extract a textual prompt from:
              - str
              - dict-like messages with 'content'
              - objects with .content
              - lists of such items
              - Bedrock/Converse style: {'content': [{'text': '...'}]}
              - OpenAI-style: {'content': [{'type': 'text', 'text': '...'}]}
            Strategy: scan newest-to-oldest; return first non-empty text.
            """
            def _extract_text_from_message(msg) -> str:
                # 1) Plain string
                if isinstance(msg, str):
                    return msg

                # 2) dict with 'content'
                if isinstance(msg, dict) and "content" in msg:
                    c = msg.get("content")
                    # 2a) content is string
                    if isinstance(c, str):
                        return c
                    # 2b) content is list of parts (Bedrock/Converse or OpenAI style)
                    if isinstance(c, list):
                        for part in c:
                            # Bedrock/Converse: {'text': '...'}
                            if isinstance(part, dict) and "text" in part and isinstance(part["text"], str):
                                if part["text"].strip():
                                    return part["text"]
                            # OpenAI style: {'type':'text','text':'...'}
                            if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                                if part["text"].strip():
                                    return part["text"]
                    # 2c) content object with .text
                    if hasattr(c, "text"):
                        try:
                            t = str(getattr(c, "text"))
                            if t.strip():
                                return t
                        except Exception:
                            pass
                    # 2d) last-resort stringification
                    try:
                        t = str(c)
                        if t.strip():
                            return t
                    except Exception:
                        pass

                # 3) object with .content
                if hasattr(msg, "content"):
                    try:
                        c = getattr(msg, "content")
                        if isinstance(c, str) and c.strip():
                            return c
                        if isinstance(c, list):
                            for part in c:
                                if isinstance(part, dict) and "text" in part and isinstance(part["text"], str):
                                    if part["text"].strip():
                                        return part["text"]
                                if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                                    if part["text"].strip():
                                        return part["text"]
                        # Fallback to str(c)
                        try:
                            t = str(c)
                            if t.strip():
                                return t
                        except Exception:
                            pass
                    except Exception:
                        pass

                return ""

            # A) If task is a list, scan newest-to-oldest
            if isinstance(task_obj, list) and task_obj:
                for msg in reversed(task_obj):
                    t = _extract_text_from_message(msg)
                    if t.strip():
                        return t

            # B) Single message-like object
            t = _extract_text_from_message(task_obj)
            if t.strip():
                return t

            # C) Check invocation_state for common shapes
            if inv_state is not None:
                for attr in ("last_message", "message", "messages"):
                    if hasattr(inv_state, attr):
                        val = getattr(inv_state, attr)
                        if isinstance(val, list) and val:
                            for msg in reversed(val):
                                t = _extract_text_from_message(msg)
                                if t.strip():
                                    return t
                        t = _extract_text_from_message(val)
                        if t.strip():
                            return t

            # D) Last resort: explicit kwarg
            if "prompt" in kw and str(kw["prompt"]).strip():
                return str(kw["prompt"])

            return ""

        try:
            prompt = _extract_prompt(task, invocation_state, kwargs)
            logger.debug("LocalNodeAgent[%s] extracted prompt: %s", self._name, (prompt or "")[:200])

            # Fail fast to avoid "successful" no-ops with empty workflow_id
            if not (prompt or "").strip():
                raise ValueError(
                    f"LocalNodeAgent[{self._name}] received empty prompt/task. "
                    "Ensure the graph passes a message whose content includes 'workflow_id::<id>'."
                )

            start = time.perf_counter()
            result = self._handler(prompt)

            # If handler is async, await it. If it's sync, just use the result.
            if _asyncio.iscoroutine(result):
                result = await result
            elapsed = time.perf_counter() - start

            output_str = "" if result is None else str(result)

            # Optional: populate from STATE_STORE if you track usage/metrics per workflow
            tokens: Dict[str, Any] = {}
            accumulated_usage: Dict[str, Any] = {}
            accumulated_metrics: Dict[str, Any] = {}
            execution_count: int = 1
            results_map: Dict[str, MultiAgentResult] = {}

            agent_result = MultiAgentResult(
                output=output_str,
                execution_time=elapsed,
                messages=[{"role": "assistant", "content": output_str}],
                tokens=tokens,
                accumulated_usage=accumulated_usage,
                accumulated_metrics=accumulated_metrics,
                execution_count=execution_count,
                results=results_map,
            )

            logger.debug(
                "LocalNodeAgent[%s] completed in %.3fs. Output(len)=%d",
                self._name, elapsed, len(output_str)
            )
            return agent_result

        except Exception as e:
            logger.exception("LocalNodeAgent[%s] failed: %s", self._name, e)
            err_text = f"[{self._name}] FAILED: {e}"
            return MultiAgentResult(
                output=err_text,
                execution_time=0.0,
                messages=[{"role": "assistant", "content": err_text}],
                tokens={},
                accumulated_usage={},
                accumulated_metrics={},
                execution_count=1,
                results={},
            )


# -----------------------------------------------------------------------------
# Graph creation using LocalNodeAgent wrappers
# -----------------------------------------------------------------------------
def create_sop_workflow():
    gb = GraphBuilder()

    # Optional: set execution limits to avoid cycles running indefinitely.
    # Duck-type to avoid breaking if your GraphBuilder doesn't expose this.
    try:
        if hasattr(gb, "set_limits"):
            gb.set_limits(
                max_node_executions=8,   # global guardrail
                execution_timeout=300,   # total seconds for the graph
                node_timeout=90          # per-node timeout
            )
        elif hasattr(gb, "configure"):
            gb.configure(
                max_node_executions=8,
                execution_timeout=300,
                node_timeout=90,
            )
    except Exception as e:
        logger.debug("GraphBuilder limits not set (non-fatal): %s", e)

    # Wrap each node runner with a LocalNodeAgent (async handlers supported)
    planning_node   = LocalNodeAgent("planning",  lambda p: run_planning_node(p, use_llama_dispatch=False))
    research_node   = LocalNodeAgent("research",  lambda p: run_research_node(p, use_llama_dispatch=False))
    content_node    = LocalNodeAgent("content",   lambda p: run_content_node(p, use_llama_dispatch=False))
    formatter_node  = LocalNodeAgent("formatter", lambda p: run_formatter_node(p, use_llama_dispatch=False))
    qa_node         = LocalNodeAgent("qa",        lambda p: run_qa_node(p, use_llama_dispatch=False))

    # Register nodes with the graph
    gb.add_node(planning_node,  "planning")
    gb.add_node(research_node,  "research")
    gb.add_node(content_node,   "content")
    gb.add_node(formatter_node, "formatter")
    gb.add_node(qa_node,        "qa")

    # Linear flow
    gb.add_edge("planning",  "research")
    gb.add_edge("research",  "content")
    gb.add_edge("content",   "formatter")
    gb.add_edge("formatter", "qa")

    # Conditional revision loop (client-side state check)
    def should_revise(graph_state) -> bool:
        """
        Conditional edge predicate. `graph_state` is the Strands GraphState.
        We look up our SOPState from STATE_STORE using the workflow_id threaded
        through the graph as a string message.
        """
        workflow_id = _extract_workflow_id_from_graph_state(graph_state)
        if not workflow_id:
            return False

        sop_state: Optional[SOPState] = STATE_STORE.get(workflow_id)
        if not sop_state:
            return False

        qa_result = getattr(sop_state, "qa_result", None)
        if qa_result and not getattr(qa_result, "approved", True):
            retry_count = getattr(sop_state, "retry_count", 0)
            if retry_count < REVISION_MAX:
                sop_state.retry_count = retry_count + 1
                logger.info("QA revision requested — retry %d/%d", sop_state.retry_count, REVISION_MAX)
                return True
        return False

    gb.add_edge("qa", "content", condition=should_revise)

    gb.set_entry_point("planning")
    return gb.build()


def _extract_workflow_id_from_graph_state(graph_state) -> str:
    """Extract our workflow_id token from the Strands GraphState messages."""
    try:
        messages = getattr(graph_state, "messages", []) or []
        for msg in reversed(messages):
            # Handle dict or object with .content; also handle list parts with 'text'
            content = ""
            if isinstance(msg, dict):
                c = msg.get("content", "")
                if isinstance(c, str):
                    content = c
                elif isinstance(c, list):
                    for part in c:
                        if isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"]:
                            content = part["text"]
                            break
            elif hasattr(msg, "content"):
                c = getattr(msg, "content")
                if isinstance(c, str):
                    content = c
                elif isinstance(c, list):
                    for part in c:
                        if isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"]:
                            content = part["text"]
                            break

            if "workflow_id::" in (content or ""):
                return content.split("workflow_id::")[1].split()[0].strip()
    except Exception:
        pass
    return ""


# Build the workflow once and reuse
sop_workflow = create_sop_workflow()


# -----------------------------------------------------------------------------
# Orchestration API
# -----------------------------------------------------------------------------
async def generate_sop(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: Optional[List[str]] = None,
) -> SOPState:
    """
    Orchestrates the SOP workflow via the Strands Graph using local client-side nodes.
    The graph receives a message list; all real work uses STATE_STORE side channel.
    """
    initial_state = SOPState(
        topic=topic,
        industry=industry,
        target_audience=target_audience,
        requirements=requirements or [],
        workflow_id=f"sop-{abs(hash((topic, industry, target_audience, tuple(requirements or []))))}",
        status=WorkflowStatus.INIT,
    )

    # Register state so node handlers can find it
    workflow_id = initial_state.workflow_id
    STATE_STORE[workflow_id] = initial_state

    # Graph receives a message with content — embed workflow_id so nodes can locate SOPState
    graph_prompt = (
        f"workflow_id::{workflow_id} | "
        f"Generate a Standard Operating Procedure for: {topic} | "
        f"Industry: {industry} | Audience: {target_audience}"
    )

    logger.info("=" * 60)
    logger.info("Starting SOP Generation | Topic: %s | Industry: %s | Audience: %s",
                topic, industry, target_audience)
    logger.info("=" * 60)

    try:
        # Drive the graph asynchronously. Each node will mutate STATE_STORE.
        # Pass as an explicit message list to align with frameworks expecting messages.
        await sop_workflow.invoke_async([{"role": "user", "content": graph_prompt}])

        final_state: SOPState = STATE_STORE.get(workflow_id, initial_state)
        logger.info(
            "Workflow complete | Status: %s | Tokens: %s",
            final_state.status, getattr(final_state, "tokens_used", "N/A")
        )
        return final_state

    except Exception as e:
        logger.error("Workflow failed: %s", e)
        initial_state.status = WorkflowStatus.FAILED
        if hasattr(initial_state, "add_error"):
            initial_state.add_error(str(e))
        return initial_state

    finally:
        # Optional: Remove from store if you don't need post-mortem inspection
        STATE_STORE.pop(workflow_id, None)


def generate_sop_sync(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: Optional[List[str]] = None,
) -> SOPState:
    """
    Synchronous wrapper — use only when NOT inside an existing event loop.

    If you are already inside an async runtime (e.g., notebooks, async web servers,
    or the strands graph runner), call `await generate_sop(...)` instead.
    """
    try:
        # If an event loop is already running in this thread, avoid re-entering it.
        asyncio.get_running_loop()
        # Loop is running — raise clear error telling caller to use the async API.
        raise RuntimeError(
            "generate_sop_sync() called inside an active event loop. "
            "Use: `await generate_sop(...)` in async contexts."
        )
    except RuntimeError:
        # No running loop — safe to use asyncio.run
        return asyncio.run(generate_sop(topic, industry, target_audience, requirements))