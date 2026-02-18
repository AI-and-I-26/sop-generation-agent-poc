"""
Simple SOP Generation Example

This is the EASIEST way to generate an SOP.
Just run: python examples/simple_example.py
"""

import asyncio
import sys
sys.path.insert(0, '.')  # Add project root to path

from src.graph.sop_workflow import generate_sop


async def main():
    """Generate a simple SOP"""
    
    print("\n" + "="*70)
    print("SOP GENERATION - Simple Example")
    print("="*70 + "\n")
    
    # ========================================================================
    # THIS IS THE MAIN ENTRY POINT - EVERYTHING STARTS HERE
    # ========================================================================
    result = await generate_sop(
        topic="Fire Evacuation Procedures",
        industry="Office Buildings",
        target_audience="All employees"
    )
    
    # ========================================================================
    # DISPLAY RESULTS
    # ========================================================================
    print("\n" + "="*70)
    print("✅ GENERATION COMPLETE")
    print("="*70)
    
    print(f"\nStatus: {result.status}")
    print(f"Workflow ID: {result.workflow_id}")
    print(f"Tokens Used: {result.tokens_used:,}")
    
    if result.qa_result:
        print(f"\n📊 Quality Assurance:")
        print(f"  Overall Score: {result.qa_result.score}/10")
        print(f"  Approved: {'YES ✓' if result.qa_result.approved else 'NO ✗'}")
        print(f"  Feedback: {result.qa_result.feedback[:150]}...")
    
    # ========================================================================
    # SAVE DOCUMENT
    # ========================================================================
    if result.formatted_document:
        filename = "fire_evacuation_sop.md"
        with open(filename, "w") as f:
            f.write(result.formatted_document)
        
        print(f"\n📄 Document saved: {filename}")
        print(f"   Length: {len(result.formatted_document):,} characters")
        
        # Show preview
        print(f"\n📄 Document Preview (first 500 characters):")
        print("-" * 70)
        print(result.formatted_document[:500])
        print("...")
        print("-" * 70)
    
    # ========================================================================
    # SHOW ERRORS (if any)
    # ========================================================================
    if result.errors:
        print(f"\n⚠️  Errors encountered ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error}")
    
    print("\n" + "="*70)
    print("✅ Done! Check fire_evacuation_sop.md")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
