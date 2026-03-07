import os
import sys
import asyncio
import logging
from pathlib import Path

# ---- Force logging to show DEBUG for this ad-hoc test ----
for h in logging.root.handlers[:]:
    logging.root.removeHandler(h)
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")

# ---- Ensure imports work: add .../app to sys.path ----
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # should be .../app
sys.path.insert(0, str(PROJECT_ROOT))
print("PROJECT_ROOT:", PROJECT_ROOT)

from src.agents import research_agent
from src.graph.state_store import STATE_STORE
from src.graph.state_schema import SOPState

def test_kb_retrieval_rounds():
    print(">>> test_kb_retrieval_rounds START")

    # --- Env configuration for KB retrieval ---
    os.environ["AWS_REGION"] = "us-east-2"
    os.environ["KNOWLEDGE_BASE_ID"] = "1NR6BI4TNO"   # <-- replace with your real KB ID (no spaces/quotes)
    os.environ["RESEARCH_REQUIRE_KB"] = "1"
    os.environ["KB_FORCE_HITS"] = "1"
    os.environ["KB_MAX_RESULTS"] = "20"
    os.environ["KB_MIN_HITS"] = "1"

    wid = "sop-test-123"
    STATE_STORE[wid] = SOPState(
        workflow_id=wid,
        topic="Global Technology Infrastructure Qualification SOP — Network Devices, Storage, and Cloud Platforms",
        industry="Information Technology (IT)",
        target_audience="IT Qualification Engineers and System Administrators at Charles River Laboratories",
        outline=None,
    )

    prompt = f"workflow_id::{wid} | test research"
    out = asyncio.run(research_agent.run_research_node(prompt))

    state = STATE_STORE[wid]
    print("Research returned:", out)
    print("kb_hits=", state.kb_hits, "| research_complete=", state.research_complete)

    assert state.research_complete is True, out
    assert state.kb_hits >= 1, f"expected kb_hits>=1, got {state.kb_hits}"

    print("<<< test_kb_retrieval_rounds END — PASS")

# ---- Run if executed as a script ----
if __name__ == "__main__":
    test_kb_retrieval_rounds()