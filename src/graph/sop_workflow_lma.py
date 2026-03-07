"""
SOP Workflow — Strands Graph (Option B: client-side tool execution)
Updated to enforce Planning/Research gating and add QA-policy revision loop,
with robust workflow_id extraction and router diagnostics.
"""

import logging
import asyncio
import time
import re
from typing import Any, Optional, Dict, List, Tuple

from strands.multiagent.graph import GraphBuilder
from strands.multiagent.base import MultiAgentBase  # adjust if needed

from src.graph.state_schema import SOPState, WorkflowStatus
from src.graph.state_store import STATE_STORE

# ---- Client-side node runner entry points (async-capable) ----
from app.src.agents.planning_agent_lma import run_planning_node
from src.agents.research_agent import run_research_node
from app.src.agents.content_agent_lma import run_content_node
from app.src.agents.formatter_agent_lma import run_formatter_node
from app.src.agents.qa_agent_lma import run_qa_node

logger = logging.getLogger(__name__)

REVISION_MAX = 2          # maximum content<->qa revision cycles
POLICY_GUARDS = True      # enable extra structural/policy checks for revision gating


# -----------------------------------------------------------------------------
# Compatibility result for Strands Graph (do not import framework class)
# -----------------------------------------------------------------------------
class MultiAgentResult:
    """
    Minimal result container that the graph inspects.
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
# Local agent wrapper (client-side executors)
# -----------------------------------------------------------------------------
class LocalNodeAgent(MultiAgentBase):
    """
    Wraps a Python callable/coroutine as a Strands Agent. The handler must accept
    a single 'prompt: str' and return a str (or awaitable[str]).
    """
    def __init__(self, name: str, handler):
        self._name = name
        self._handler = handler

    @property
    def name(self) -> str:
        return self._name

    async def invoke_async(self, task, invocation_state=None, **kwargs) -> MultiAgentResult:
        import asyncio as _asyncio

        logger.debug(
            "LocalNodeAgent[%s].invoke_async called | task_type=%s | kwargs=%s",
            self._name, type(task).__name__, list(kwargs.keys())
        )

        def _extract_prompt(task_obj, inv_state, kw) -> str:
            """
            Extract prompt from various message shapes:
            - str
            - dict with 'content' (string or list of parts)
            - object with .content
            - Bedrock/Converse: {'content': [{'text': '...'}]}
            - OpenAI: {'content': [{'type': 'text', 'text': '...'}]}
            - lists of any of the above (scan newest-first)
            """
            def _extract_text_from_message(msg) -> str:
                # A) plain str
                if isinstance(msg, str):
                    return msg

                # B) dict with 'content'
                if isinstance(msg, dict) and "content" in msg:
                    c = msg.get("content")
                    if isinstance(c, str):
                        return c
                    if isinstance(c, list):
                        for part in c:
                            # Bedrock
                            if isinstance(part, dict) and isinstance(part.get("text"), str):
                                t = part["text"]
                                if t and t.strip():
                                    return t
                            # OpenAI
                            if isinstance(part, dict) and part.get("type") == "text":
                                t = part.get("text")
                                if isinstance(t, str) and t.strip():
                                    return t
                    if hasattr(c, "text"):
                        try:
                            t = str(getattr(c, "text"))
                            if t.strip():
                                return t
                        except Exception:
                            pass
                    try:
                        t = str(c)
                        if t.strip():
                            return t
                    except Exception:
                        pass

                # C) object with .content
                if hasattr(msg, "content"):
                    try:
                        c = getattr(msg, "content")
                        if isinstance(c, str) and c.strip():
                            return c
                        if isinstance(c, list):
                            for part in c:
                                if isinstance(part, dict) and isinstance(part.get("text"), str):
                                    t = part["text"]
                                    if t and t.strip():
                                        return t
                                if isinstance(part, dict) and part.get("type") == "text":
                                    t = part.get("text")
                                    if isinstance(t, str) and t.strip():
                                        return t
                        t = str(c)
                        if t.strip():
                            return t
                    except Exception:
                        pass

                return ""

            # 1) lists — scan newest-first
            if isinstance(task_obj, list) and task_obj:
                for msg in reversed(task_obj):
                    t = _extract_text_from_message(msg)
                    if t.strip():
                        return t

            # 2) single object
            t = _extract_text_from_message(task_obj)
            if t.strip():
                return t

            # 3) invocation_state
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

            # 4) kw fallback
            if "prompt" in kw and str(kw["prompt"]).strip():
                return str(kw["prompt"])

            return ""

        try:
            prompt = _extract_prompt(task, invocation_state, kwargs)
            logger.debug("LocalNodeAgent[%s] extracted prompt: %s", self._name, (prompt or "")[:200])

            # Fail fast to avoid silent no-ops
            if not (prompt or "").strip():
                raise ValueError(
                    f"LocalNodeAgent[{self._name}] received empty prompt/task. "
                    "Ensure the graph passes a message with 'workflow_id::<id>'."
                )

            start = time.perf_counter()
            result = self._handler(prompt)
            if _asyncio.iscoroutine(result):
                result = await result
            elapsed = time.perf_counter() - start

            output_str = "" if result is None else str(result)

            agent_result = MultiAgentResult(
                output=output_str,
                execution_time=elapsed,
                messages=[{"role": "assistant", "content": output_str}],
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
            )


# -----------------------------------------------------------------------------
# Helpers to read SOPState from STATE_STORE via workflow_id in messages
# -----------------------------------------------------------------------------
_WID_RE = re.compile(r"workflow_id::([^\s\|]+)")

def _extract_workflow_id_from_graph_state(graph_state) -> str:
    """
    Pull workflow_id from graph_state.messages by scanning newest->oldest and
    both user and assistant 'content' strings and structured 'content' parts.
    Fallback: if exactly one key in STATE_STORE matches '^sop-', use that.
    """
    try:
        messages = getattr(graph_state, "messages", []) or []
        for msg in reversed(messages):
            content = ""
            # Dict message
            if isinstance(msg, dict):
                c = msg.get("content", "")
                if isinstance(c, str):
                    content = c
                elif isinstance(c, list):
                    for part in c:
                        if isinstance(part, dict):
                            t = part.get("text")
                            if isinstance(t, str) and t.strip():
                                content = t
                                break
            # Object with .content
            elif hasattr(msg, "content"):
                c = getattr(msg, "content")
                if isinstance(c, str):
                    content = c
                elif isinstance(c, list):
                    for part in c:
                        if isinstance(part, dict):
                            t = part.get("text")
                            if isinstance(t, str) and t.strip():
                                content = t
                                break

            if content:
                m = _WID_RE.search(content)
                if m:
                    return m.group(1).strip()
    except Exception:
        pass

    # Fallback for dev: single active workflow in STATE_STORE
    try:
        sop_keys = [k for k in STATE_STORE.keys() if isinstance(k, str) and k.startswith("sop-")]
        if len(sop_keys) == 1:
            return sop_keys[0]
    except Exception:
        pass

    return ""


def _get_state(graph_state) -> Optional[SOPState]:
    wid = _extract_workflow_id_from_graph_state(graph_state)
    st = STATE_STORE.get(wid)
    return st


# -----------------------------------------------------------------------------
# Edge condition predicates (gating) with diagnostics
# -----------------------------------------------------------------------------
def planning_complete(graph_state) -> bool:
    wid = _extract_workflow_id_from_graph_state(graph_state)
    st = STATE_STORE.get(wid)
    flag = bool(getattr(st, "planning_complete", False)) if st else False
    logger.warning(
        "Router[planning_complete]: wid=%s | state_present=%s | flag=%s | state_id=%s | keys=%s",
        wid, st is not None, flag, id(st) if st else None, list(STATE_STORE.keys())
    )
    return flag


def research_complete(graph_state) -> bool:
    wid = _extract_workflow_id_from_graph_state(graph_state)
    st = STATE_STORE.get(wid)
    flag = bool(getattr(st, "research_complete", False)) if st else False
    logger.warning(
        "Router[research_complete]: wid=%s | state_present=%s | flag=%s | state_id=%s | keys=%s",
        wid, st is not None, flag, id(st) if st else None, list(STATE_STORE.keys())
    )
    return flag


def content_ready(graph_state) -> bool:
    wid = _extract_workflow_id_from_graph_state(graph_state)
    st = STATE_STORE.get(wid)
    has_sections = bool(getattr(st, "content_sections", None)) if st else False
    has_markdown = bool(getattr(st, "formatted_markdown", "").strip()) if st else False
    flag = bool(st and (has_sections or has_markdown))
    logger.warning(
        "Router[content_ready]: wid=%s | state_present=%s | sections=%s | markdown=%s | flag=%s",
        wid, st is not None, has_sections, has_markdown, flag
    )
    return flag


def _purpose_ok(text: str) -> bool:
    t = (text or "").strip()
    return t.lower().startswith("to ")


def _extract_purpose_and_scope_text(st: SOPState) -> Tuple[str, str]:
    """
    Best-effort pull of 1.0 and 2.0 text from either structured sections
    or the formatted_markdown. Handlers can vary; we keep it defensive.
    """
    purpose = ""
    scope = ""

    sec = getattr(st, "content_sections", {}) or {}
    if isinstance(sec, dict):
        # Try structured section objects
        p = sec.get("PURPOSE") or sec.get("1.0") or sec.get("Purpose")
        s = sec.get("SCOPE") or sec.get("2.0") or sec.get("Scope")
        if isinstance(p, dict):
            purpose = str(p.get("content", "")).strip()
        elif isinstance(p, str):
            purpose = p.strip()
        if isinstance(s, dict):
            scope = str(s.get("content", "")).strip()
        elif isinstance(s, str):
            scope = s.strip()

    if not (purpose and scope):
        # Fallback: parse minimal lines from formatted markdown
        md = getattr(st, "formatted_markdown", "") or ""
        lines = [ln.strip() for ln in md.splitlines()]
        cur = None
        buff: List[str] = []
        col: Dict[str, str] = {}
        for ln in lines:
            if ln.startswith("## 1.0"):
                if cur and buff:
                    col[cur] = "\n".join(buff).strip()
                    buff = []
                cur = "1.0"
                continue
            if ln.startswith("## 2.0"):
                if cur and buff:
                    col[cur] = "\n".join(buff).strip()
                    buff = []
                cur = "2.0"
                continue
            if ln.startswith("## ") and cur:
                col[cur] = "\n".join(buff).strip()
                buff = []
                cur = None
                continue
            if cur:
                buff.append(ln)
        if cur and buff:
            col[cur] = "\n".join(buff).strip()
        purpose = purpose or col.get("1.0", "")
        scope = scope or col.get("2.0", "")

    return purpose or "", scope or ""


def policy_violation_requires_revision(graph_state) -> bool:
    """
    Optional extra guard to catch structural issues that QA may miss or approve:
    - PURPOSE must begin with "To <verb> ..."
    - PURPOSE should not duplicate SCOPE
    """
    if not POLICY_GUARDS:
        return False

    st = _get_state(graph_state)
    if not st:
        return False

    # If QA already rejected, let the QA loop handle it
    qa_result = getattr(st, "qa_result", None)
    if qa_result and not getattr(qa_result, "approved", True):
        return False

    purpose, scope = _extract_purpose_and_scope_text(st)
    reasons: List[str] = []

    if not _purpose_ok(purpose):
        reasons.append("PURPOSE must start with 'To ' (infinitive verb).")

    # naive duplication check
    if purpose and scope:
        p_norm = " ".join(purpose.lower().split())[:160]
        s_norm = " ".join(scope.lower().split())[:160]
        if p_norm and s_norm and p_norm == s_norm:
            reasons.append("PURPOSE duplicates SCOPE; rephrase PURPOSE to intent, not coverage.")

    if reasons:
        setattr(st, "qa_policy_feedback", reasons)
        if not hasattr(st, "retry_count"):
            st.retry_count = 0
        return True

    return False


def should_revise(graph_state) -> bool:
    """
    QA-driven (and policy-driven) revision loop.
    - If QA not approved and retries < REVISION_MAX => revise
    - Else if policy guard flags issues and retries < REVISION_MAX => revise
    """
    st = _get_state(graph_state)
    if not st:
        return False

    retry = int(getattr(st, "retry_count", 0))

    qa_result = getattr(st, "qa_result", None)
    needs_qa_revision = bool(qa_result and not getattr(qa_result, "approved", True))

    policy_needs_revision = policy_violation_requires_revision(graph_state)

    if (needs_qa_revision or policy_needs_revision) and retry < REVISION_MAX:
        st.retry_count = retry + 1
        reason = "QA" if needs_qa_revision else "Policy"
        logger.info("Revision requested by %s — retry %d/%d", reason, st.retry_count, REVISION_MAX)
        return True

    return False


# -----------------------------------------------------------------------------
# Graph construction
# -----------------------------------------------------------------------------
def create_sop_workflow():
    gb = GraphBuilder()

    # Optional global limits
    try:
        if hasattr(gb, "set_limits"):
            gb.set_limits(
                max_node_executions=12,
                execution_timeout=300,
                node_timeout=120,
            )
        elif hasattr(gb, "configure"):
            gb.configure(
                max_node_executions=12,
                execution_timeout=300,
                node_timeout=120,
            )
    except Exception as e:
        logger.debug("GraphBuilder limits not set (non-fatal): %s", e)

    # Local node wrappers (ensure handlers are awaited in async)
    planning   = LocalNodeAgent("planning",  lambda p: run_planning_node(p,  use_llama_dispatch=False))
    research   = LocalNodeAgent("research",  lambda p: run_research_node(p,  use_llama_dispatch=False))
    content    = LocalNodeAgent("content",   lambda p: run_content_node(p,   use_llama_dispatch=False))
    formatter  = LocalNodeAgent("formatter", lambda p: run_formatter_node(p, use_llama_dispatch=False))
    qa         = LocalNodeAgent("qa",        lambda p: run_qa_node(p,        use_llama_dispatch=False))

    # Register nodes
    gb.add_node(planning,  "planning")
    gb.add_node(research,  "research")
    gb.add_node(content,   "content")
    gb.add_node(formatter, "formatter")
    gb.add_node(qa,        "qa")

    # Enforce Planning → Research → Content
    gb.add_edge("planning", "research", condition=planning_complete)  # requires st.planning_complete = True
    gb.add_edge("research", "content",  condition=research_complete)  # requires st.research_complete = True

    # Gate Content → Formatter on research and content readiness
    gb.add_edge("content", "formatter", condition=lambda gs: research_complete(gs) and content_ready(gs))

    # Formatter → QA is linear
    gb.add_edge("formatter", "qa")

    # QA → Content revision loop (QA rejection or policy guard)
    gb.add_edge("qa", "content", condition=should_revise)

    # Entry point
    gb.set_entry_point("planning")

    logger.warning("GRAPH ENTRY: planning")
    logger.warning("GRAPH EDGES (gated): planning -[planning_complete]-> research -[research_complete]-> content -[content_ready]-> formatter -> qa -[revision?]-> content")

    return gb.build()


# Build once (module-level)
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
    Drives the SOP workflow using the Strands Graph and client-side node handlers.
    STATE_STORE carries SOPState across nodes; the graph only passes a message
    containing 'workflow_id::<id>' plus basic context.

    Handlers should set:
      - st.planning_complete = True  (planning node)
      - st.research_complete = True  (research node)
      - st.content_sections / st.formatted_markdown (content/formatter)
      - st.qa_result.approved (qa node)
    """
    initial_state = SOPState(
        topic=topic,
        industry=industry,
        target_audience=target_audience,
        requirements=requirements or [],
        workflow_id=f"sop-{abs(hash((topic, industry, target_audience, tuple(requirements or []))))}",
        status=WorkflowStatus.INIT,
    )

    workflow_id = initial_state.workflow_id
    STATE_STORE[workflow_id] = initial_state

    graph_prompt = (
        f"workflow_id::{workflow_id} | "
        f"Generate a Standard Operating Procedure for: {topic} | "
        f"Industry: {industry} | Audience: {target_audience}"
    )

    logger.info("=" * 60)
    logger.info("Starting SOP Generation | Topic=%s | Industry=%s | Audience=%s",
                topic, industry, target_audience)
    logger.info("=" * 60)

    try:
        # Execute graph asynchronously; each node mutates STATE_STORE[workflow_id]
        logger.warning("Invoke sop_workflow.invoke_async(...) with message: %s", graph_prompt)
        await sop_workflow.invoke_async([{"role": "user", "content": graph_prompt}])

        final_state: SOPState = STATE_STORE.get(workflow_id, initial_state)
        logger.info(
            "Workflow complete | Status: %s | Tokens: %s",
            getattr(final_state, "status", "N/A"), getattr(final_state, "tokens_used", "N/A")
        )
        return final_state

    except Exception as e:
        logger.error("Workflow failed: %s", e)
        initial_state.status = WorkflowStatus.FAILED
        if hasattr(initial_state, "add_error"):
            try:
                initial_state.add_error(str(e))
            except Exception:
                pass
        return initial_state

    finally:
        # Optional: retain state for post-mortem; otherwise clean up.
        STATE_STORE.pop(workflow_id, None)


def generate_sop_sync(
    topic: str,
    industry: str,
    target_audience: str = "General staff",
    requirements: Optional[List[str]] = None,
) -> SOPState:
    """
    Synchronous wrapper — use only outside an active event loop.
    """
    try:
        asyncio.get_running_loop()
        raise RuntimeError(
            "generate_sop_sync() called inside an active event loop. "
            "Use: `await generate_sop(...)` in async contexts."
        )
    except RuntimeError:
        return asyncio.run(generate_sop(topic, industry, target_audience, requirements))