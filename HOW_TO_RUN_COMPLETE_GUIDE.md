# COMPLETE EXECUTION GUIDE
How to Run the SOP Generation System & Generate Your First SOP

## 📋 Table of Contents
1. [Setup (One-Time)](#setup)
2. [Execution Flow Explained](#flow)
3. [Method 1: Simple Script](#method1)
4. [Method 2: Interactive Python](#method2)
5. [Method 3: Full Application](#method3)
6. [Understanding State Flow](#state)
7. [Troubleshooting](#troubleshooting)

---

## 🔧 SETUP (One-Time) {#setup}

### Step 1: Install Dependencies
```bash
# Install Strands SDK (REQUIRED)
pip install strands-agents strands-agents-tools

# Install other dependencies
pip install boto3 pydantic python-dotenv
```

### Step 2: Create .env File
```bash
# Create .env in project root
cat > .env << 'EOF'
AWS_REGION=us-east-1

# Bedrock Models
MODEL_PLANNING=meta.llama3-1-70b-instruct-v1:0
MODEL_RESEARCH=meta.llama3-1-70b-instruct-v1:0
MODEL_CONTENT=meta.llama3-1-70b-instruct-v1:0
MODEL_FORMATTER=meta.llama3-1-8b-instruct-v1:0
MODEL_QA=meta.llama3-1-70b-instruct-v1:0

# AWS Resources (Optional - works in mock mode without these)
KNOWLEDGE_BASE_ID=your-kb-id-here
SOP_BUCKET=your-bucket-name
EOF
```

### Step 3: Configure AWS
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Enter region: us-east-1
```

---

## 🔄 EXECUTION FLOW EXPLAINED {#flow}

```
YOU (run script)
    ↓
generate_sop() in sop_workflow.py
    ↓
Creates initial SOPState
    ↓
Strands StateGraph executes nodes:
    ↓
[1] planning_node → Creates outline
    ↓
[2] research_node → Finds similar SOPs, compliance
    ↓
[3] content_node → Generates detailed content
    ↓
[4] formatter_node → Formats final document
    ↓
[5] qa_node → Reviews quality
    ↓
Decision: Approved? → END
         Needs work? → Back to content (max 2 retries)
    ↓
Returns final SOPState with complete SOP
```

### File Participation:
- **sop_workflow.py**: Entry point, orchestrates everything
- **state_schema.py**: Defines data structure passed between nodes
- **planning_agent.py**: Node 1 - Creates outline
- **research_agent.py**: Node 2 - Uses knowledge_base.py, s3_search.py, compliance_api.py
- **content_agent.py**: Node 3 - Uses few_shot_examples.py
- **formatter_agent.py**: Node 4 - Formats document
- **qa_agent.py**: Node 5 - Quality review
- **system_prompts.py**: Used by all agents
- **logger.py**: Logging throughout

---

## 🚀 METHOD 1: Simple Script (Recommended) {#method1}

### Create: `examples/simple_example.py`
```python
import asyncio
import sys
sys.path.insert(0, '.')  # Important: adds current dir to path

from src.graph.sop_workflow import generate_sop


async def main():
    print("Generating SOP...")
    
    # THIS IS THE MAIN ENTRY POINT
    result = await generate_sop(
        topic="Fire Evacuation Procedures",
        industry="Office Buildings",
        target_audience="All employees"
    )
    
    # Check results
    print(f"\n✅ Status: {result.status}")
    print(f"📊 QA Score: {result.qa_result.score}/10")
    print(f"✓ Approved: {result.qa_result.approved}")
    
    # Save document
    with open("fire_evacuation_sop.md", "w") as f:
        f.write(result.formatted_document)
    
    print("\n✓ Saved to: fire_evacuation_sop.md")
    print(f"\nDocument preview:")
    print(result.formatted_document[:500])
    print("...\n")


if __name__ == "__main__":
    asyncio.run(main())
```

### Run It:
```bash
python examples/simple_example.py
```

### Expected Output:
```
======================================================================
Starting SOP Generation Workflow
Topic: Fire Evacuation Procedures
Industry: Office Buildings
======================================================================
✓ Planning complete. Created outline with 11 sections
✓ Research found 3 similar SOPs, 5 compliance requirements
✓ Generated content for 5 sections
✓ Document formatted (8 pages estimated)
✓ QA Review complete. Score: 8.5/10, Approved: True
======================================================================
Workflow Completed!
Status: completed
Tokens Used: 12,450
QA Score: 8.5/10
======================================================================

✅ Status: completed
📊 QA Score: 8.5/10
✓ Approved: True

✓ Saved to: fire_evacuation_sop.md

Document preview:
# Fire Evacuation Procedures

**Document Control**
- Document ID: SOP-20240218-1430
- Version: 1.0
- Effective Date: 2024-02-18
...
```

---

## 💻 METHOD 2: Interactive Python {#method2}

```bash
# Start Python
python

# Then in Python prompt:
```

```python
import asyncio
import sys
sys.path.insert(0, '.')

from src.graph.sop_workflow import generate_sop

# Generate SOP
result = asyncio.run(generate_sop(
    topic="Chemical Spill Response",
    industry="Manufacturing",
    target_audience="Floor supervisors"
))

# Check status
print(f"Status: {result.status}")
print(f"Score: {result.qa_result.score}")

# View first 1000 chars
print(result.formatted_document[:1000])

# Save to file
with open("chemical_spill_sop.md", "w") as f:
    f.write(result.formatted_document)

print("✓ Saved!")
```

---

## 🎯 METHOD 3: Full Application {#method3}

### Create: `examples/full_application.py`
```python
import asyncio
import sys
from datetime import datetime
sys.path.insert(0, '.')

from src.graph.sop_workflow import generate_sop


async def generate_with_details(topic, industry, audience):
    """Generate SOP with detailed output"""
    
    print(f"\n{'='*70}")
    print(f"GENERATING SOP")
    print(f"Topic: {topic}")
    print(f"Industry: {industry}")
    print(f"Audience: {audience}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    # MAIN EXECUTION HAPPENS HERE
    result = await generate_sop(
        topic=topic,
        industry=industry,
        target_audience=audience
    )
    
    # Display comprehensive results
    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    
    print(f"\n📊 Status: {result.status}")
    print(f"🆔 Workflow ID: {result.workflow_id}")
    print(f"🔢 Tokens Used: {result.tokens_used:,}")
    print(f"🔄 Retries: {result.retry_count}")
    
    if result.outline:
        print(f"\n📋 Outline:")
        print(f"  Title: {result.outline.title}")
        print(f"  Sections: {len(result.outline.sections)}")
        print(f"  Sections:")
        for section in result.outline.sections[:5]:
            print(f"    {section.number}. {section.title}")
    
    if result.research:
        print(f"\n🔍 Research:")
        print(f"  Similar SOPs: {len(result.research.similar_sops)}")
        print(f"  Compliance: {len(result.research.compliance_requirements)}")
        if result.research.compliance_requirements:
            for req in result.research.compliance_requirements[:3]:
                print(f"    - {req}")
    
    if result.content_sections:
        print(f"\n✍️  Content:")
        print(f"  Sections Generated: {len(result.content_sections)}")
    
    if result.qa_result:
        print(f"\n✅ Quality Assurance:")
        print(f"  Overall Score: {result.qa_result.score}/10")
        print(f"  Approved: {'YES ✓' if result.qa_result.approved else 'NO ✗'}")
        print(f"  Completeness: {result.qa_result.completeness_score}/10")
        print(f"  Clarity: {result.qa_result.clarity_score}/10")
        print(f"  Compliance: {result.qa_result.compliance_score}/10")
    
    if result.formatted_document:
        filename = f"sop_{topic.lower().replace(' ', '_')}.md"
        with open(filename, "w") as f:
            f.write(result.formatted_document)
        print(f"\n📄 Document saved: {filename}")
        print(f"   Length: {len(result.formatted_document):,} characters")
    
    if result.errors:
        print(f"\n⚠️  Errors:")
        for error in result.errors:
            print(f"  - {error}")
    
    print(f"\n{'='*70}\n")
    return result


async def main():
    # Generate multiple SOPs
    
    # Example 1
    await generate_with_details(
        topic="Fire Evacuation Procedures",
        industry="Office Buildings",
        audience="All employees"
    )
    
    # Example 2
    await generate_with_details(
        topic="Lab Safety Procedures",
        industry="Laboratory",
        audience="Lab technicians"
    )


if __name__ == "__main__":
    asyncio.run(main())
```

### Run:
```bash
python examples/full_application.py
```

---

## 📊 UNDERSTANDING STATE FLOW {#state}

The `SOPState` object flows through all nodes:

```python
# 1. INITIAL (you create this)
state = SOPState(
    topic="Fire Safety",
    industry="Office",
    target_audience="Employees",
    status="init"  # Starting status
)

# 2. AFTER PLANNING
state.status = "planned"
state.outline = SOPOutline(
    title="Fire Safety Procedures",
    sections=[...11 sections...],
    estimated_pages=8
)

# 3. AFTER RESEARCH
state.status = "researched"
state.research = ResearchFindings(
    similar_sops=[...],
    compliance_requirements=["NFPA 101", "OSHA", ...],
    best_practices=[...]
)

# 4. AFTER CONTENT
state.status = "written"
state.content_sections = {
    "Purpose and Scope": "## Purpose...",
    "Safety Requirements": "## Safety...",
    ... # All sections
}

# 5. AFTER FORMATTING
state.status = "formatted"
state.formatted_document = """
# Fire Safety Procedures

**Document Control**
...
[Complete formatted document]
"""

# 6. AFTER QA
state.status = "qa_complete" or "completed"
state.qa_result = QAResult(
    score=8.5,
    approved=True,
    feedback="Excellent coverage..."
)

# 7. FINAL - returned to you
return state  # All fields populated
```

---

## 🔧 TROUBLESHOOTING {#troubleshooting}

### Error: "No module named 'strands'"
```bash
pip install strands-agents strands-agents-tools
```

### Error: "No module named 'src'"
Add to top of your script:
```python
import sys
sys.path.insert(0, '.')
```

### Error: "Unable to locate credentials"
```bash
aws configure
# Or set: export AWS_PROFILE=your-profile
```

### Error: "Model not found" or "Access denied"
1. Go to AWS Console → Bedrock
2. Enable models: Llama 3.1 8B, 70B
3. Wait 5 minutes for activation

### Workflow hangs or takes too long
- Check AWS credentials
- Verify Bedrock model access
- Check CloudWatch logs for errors

### Empty or invalid output
- Check logs in terminal
- Verify MODEL_* variables in .env
- Test individual agents first

---

## ⚡ QUICK START (Copy-Paste)

```bash
# 1. One-time setup
pip install strands-agents strands-agents-tools boto3 pydantic python-dotenv
aws configure

# 2. Create script
cat > my_sop.py << 'SCRIPT'
import asyncio
import sys
sys.path.insert(0, '.')
from src.graph.sop_workflow import generate_sop

async def main():
    result = await generate_sop(
        topic="YOUR TOPIC HERE",
        industry="YOUR INDUSTRY",
        target_audience="YOUR AUDIENCE"
    )
    
    print(f"✅ Status: {result.status}")
    print(f"📊 Score: {result.qa_result.score if result.qa_result else 'N/A'}/10")
    
    with open("my_sop.md", "w") as f:
        f.write(result.formatted_document)
    
    print("✓ Saved to my_sop.md")

asyncio.run(main())
SCRIPT

# 3. Run
python my_sop.py

# 4. Your SOP is in my_sop.md!
```

---

## 🎯 SUMMARY

**Starting Point:** `src/graph/sop_workflow.py` → `generate_sop()` function

**Main Function:**
```python
from src.graph.sop_workflow import generate_sop

result = await generate_sop(topic, industry, audience)
```

**Output:** `result.formatted_document` contains your complete SOP

**That's it!** The Strands StateGraph handles all the orchestration automatically.
