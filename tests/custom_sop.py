"""
Custom SOP Generator Template

INSTRUCTIONS:
1. Change the topic, industry, and audience below (lines 20-22)
2. Run: python examples/custom_sop.py
3. Your SOP will be saved to a file

That's it!
"""

import asyncio
from pathlib import Path
import sys
# sys.path.insert(0, '.')

import logging
import os

logging.basicConfig(level=logging.DEBUG)

# Resolve the project root: <repo_root>/ (two levels up from app/test/custom_sop.py)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Add it to sys.path
sys.path.insert(0, str(PROJECT_ROOT))

from src.graph.sop_workflow import generate_sop


async def main():
    # (Optional) ensure stdout can print UTF-8 glyphs in some Windows terminals
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # ========================================================================
    # 🔧 CUSTOMIZE THESE VALUES:
    # ========================================================================
    TOPIC = "Chemical Spill Response"           # ← Change this
    INDUSTRY = "Manufacturing"                  # ← Change this
    AUDIENCE = "Floor supervisors"              # ← Change this
    # ========================================================================

    print(f"\nGenerating SOP...")
    print(f"  Topic: {TOPIC}")
    print(f"  Industry: {INDUSTRY}")
    print(f"  Audience: {AUDIENCE}\n")

    # Generate
    result = await generate_sop(
        topic=TOPIC,
        industry=INDUSTRY,
        target_audience=AUDIENCE
    )

    # Save — write as UTF-8 to support symbols like ⚡/⚠️/✓
    filename = f"sop_{TOPIC.lower().replace(' ', '_')}.md"
    with open(filename, "w", encoding="utf-8", newline="") as f:
        f.write(result.formatted_document)

    # Results
    print(f"✅ Generation complete!")
    print(f"   Status: {result.status}")
    if getattr(result, "qa_result", None):
        print(f"   QA Score: {result.qa_result.score}/10")
        print(f"   Approved: {result.qa_result.approved}")
    print(f"   File: {filename}")
    print(f"   Size: {len(result.formatted_document):,} characters\n")


if __name__ == "__main__":
    asyncio.run(main())