"""
Custom SOP Generator Template

INSTRUCTIONS:
1. Change the topic, industry, and audience below (lines 20-22)
2. Run: python examples/custom_sop.py
3. Your SOP will be saved to a file

That's it!
"""

import asyncio
import sys
sys.path.insert(0, '.')

from src.graph.sop_workflow import generate_sop


async def main():
    
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
    
    # Save
    filename = f"sop_{TOPIC.lower().replace(' ', '_')}.md"
    with open(filename, "w") as f:
        f.write(result.formatted_document)
    
    # Results
    print(f"✅ Generation complete!")
    print(f"   Status: {result.status}")
    if result.qa_result:
        print(f"   QA Score: {result.qa_result.score}/10")
        print(f"   Approved: {result.qa_result.approved}")
    print(f"   File: {filename}")
    print(f"   Size: {len(result.formatted_document):,} characters\n")


if __name__ == "__main__":
    asyncio.run(main())
