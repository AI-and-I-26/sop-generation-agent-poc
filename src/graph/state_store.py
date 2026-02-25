"""
State Store - shared in-process state for the SOP workflow.

Because the Strands Graph only passes plain string messages between Agent nodes,
SOPState objects are kept here (keyed by workflow_id) so every agent's @tool
functions can read and write state without it passing through the graph wire.

Usage:
    from src.agents.state_store import STATE_STORE

    # Write
    STATE_STORE["sop-12345"] = my_sop_state

    # Read inside a tool
    state = STATE_STORE.get(workflow_id)
"""

from typing import Dict

# Module-level dict — lives for the lifetime of the process.
# For concurrent requests each workflow_id is unique, so there are no collisions.
STATE_STORE: Dict[str, object] = {}
