# COURSE DOCUMENT UPDATE GUIDE

## Changes Required for AWS_Bedrock_Strand_Complete_Course.docx

This document shows exactly what needs to be updated in the course document.

---

## MODULE 5: Multi-Agent Orchestration

### **CURRENT STRUCTURE (WRONG):**
```
Module 5, Section 5.1: Multi-Agent System Implementation
- All 5 agents together in one code block (confusing!)
```

### **NEW STRUCTURE (CORRECT):**
```
Module 5: Multi-Agent Orchestration

5.1 Planning Agent Implementation
5.2 Research Agent with RAG Tools  
5.3 Content Generation Agent
5.4 Formatter Agent (Cost Optimized)
5.5 QA Agent with Scoring
5.6 Supervisor Agent and Workflow Orchestration
5.7 Understanding __init__.py Files
```

---

## DETAILED CHANGES:

### **5.1 Planning Agent Implementation** (NEW)

**Replace the combined code with:**

```
In this section, we implement the Planning Agent that creates structured SOP outlines.

**File:** src/agents/planning_agent.py

This agent:
- Uses Strand Agent class with Llama 3.1 70B
- Enforces JSON schema for consistent outputs
- Creates comprehensive outlines with mandatory sections

**Complete Code:**
[Insert planning_agent.py code here - 124 lines]

**Key Features:**
1. JSON schema enforcement via response_format
2. System prompt with mandatory sections
3. Pydantic validation of outputs
4. Async execution for Strand StateGraph

**Usage:**
```python
from src.agents.planning_agent import PlanningAgent

agent = PlanningAgent()
outline = await agent.create_outline(
    topic="Fire Safety",
    industry="Office",
    target_audience="Employees"
)
```
```

---

### **5.2 Research Agent with RAG Tools** (NEW)

**Add new section:**

```
The Research Agent performs information retrieval using Bedrock Knowledge Base and other tools.

**File:** src/agents/research_agent.py

This agent demonstrates:
- Strand Tools integration
- RAG implementation with Bedrock KB
- Tool calling automation
- Multi-source information gathering

**Complete Code:**
[Insert research_agent.py code here - 177 lines]

**Key Features:**
1. Strand Tool class for knowledge base search
2. Automatic tool calling by Strand
3. JSON output with research findings
4. Integration with compliance APIs

**Tool Definition Example:**
```python
def _create_kb_search_tool(self) -> Tool:
    def search_kb(query: str, max_results: int = 5) -> str:
        # Bedrock KB search implementation
        ...
    
    return Tool(
        name="search_knowledge_base",
        description="Search Bedrock Knowledge Base",
        function=search_kb,
        parameters={...}
    )
```

**Note:** The Research Agent is the ONLY agent that uses tools. Other agents use prompts only.
```

---

### **5.3 Content Generation Agent** (NEW)

**Add new section:**

```
The Content Agent generates detailed, professional SOP content.

**File:** src/agents/content_agent.py

Features:
- Few-shot prompting with examples
- Safety warnings and checkpoints
- Time estimates
- Markdown formatting

**Complete Code:**
[Insert content_agent.py code here - 157 lines]

**Few-Shot Prompting:**
The system prompt includes complete examples showing:
- Emergency Shutdown Procedure (detailed)
- Sample Collection Procedure (sterile handling)
- Proper formatting with ⚠️ WARNING, ✓ CHECKPOINT, ⚡ CRITICAL markers

**Output Schema:**
```json
{
  "section_title": "string",
  "content": "string (markdown)",
  "safety_warnings": ["array"],
  "quality_checkpoints": ["array"],
  "time_estimate_minutes": "integer"
}
```
```

---

### **5.4 Formatter Agent (Cost Optimized)** (NEW)

**Add new section:**

```
The Formatter Agent combines all sections into a cohesive document.

**File:** src/agents/formatter_agent.py

**Cost Optimization:**
This agent uses Llama 3.1 8B (cheaper model) instead of 70B because:
- Formatting doesn't require complex reasoning
- 60-70% cost savings
- Still maintains quality

**Complete Code:**
[Insert formatter_agent.py code here - 149 lines]

**Document Structure:**
1. Title and metadata
2. Document control information
3. Table of contents
4. All sections with consistent formatting
5. Approval signature block

**Key Point:** Uses `MODEL_FORMATTER=meta.llama3-1-8b-instruct-v1:0` for cost savings.
```

---

### **5.5 QA Agent with Scoring** (NEW)

**Add new section:**

```
The QA Agent reviews documents for quality, completeness, and compliance.

**File:** src/agents/qa_agent.py

**Evaluation Criteria:**
1. Completeness (0-10)
2. Clarity (0-10)
3. Safety (0-10)
4. Compliance (0-10)
5. Consistency (0-10)

**Complete Code:**
[Insert qa_agent.py code here - 179 lines]

**Decision Logic:**
- Score ≥ 8.0 → APPROVED
- Score < 8.0 → NEEDS REVISION
- Max 2 retries allowed

**Output Schema:**
```json
{
  "score": 8.5,
  "feedback": "Detailed feedback",
  "approved": true,
  "issues": [],
  "completeness_score": 9.0,
  "clarity_score": 8.5,
  "safety_score": 8.0,
  "compliance_score": 8.5,
  "consistency_score": 9.0
}
```
```

---

### **5.6 Supervisor Agent and Workflow Orchestration** (NEW SECTION!)

**Add completely new section:**

```
The Supervisor Agent orchestrates the entire workflow using Strand StateGraph.

**File:** src/agents/supervisor_agent.py

**Why We Need This:**
While individual agents handle specific tasks, we need an orchestrator to:
1. Define the workflow sequence
2. Handle conditional routing (QA approval/revision)
3. Manage retry logic
4. Coordinate state between agents

**Complete Code:**
[Insert supervisor_agent.py code here - 158 lines]

**Workflow Graph:**
```
Planning → Research → Content → Format → QA
                                           ↓
                                    Approved? Yes → END
                                           ↓ No
                                    Retry < 2? Yes → Content (revision)
                                           ↓ No
                                          END (max retries)
```

**Key Features:**

1. **StateGraph Definition:**
```python
from strands import StateGraph, END

graph = StateGraph(state_schema=SOPState)
graph.add_node("planning", planning_node)
graph.add_node("research", research_node)
# ... add all nodes
```

2. **Conditional Routing:**
```python
def _should_revise(self, state: SOPState) -> Literal["revise", "finish"]:
    if state.qa_result.approved:
        return "finish"
    if state.retry_count >= 2:
        return "finish"
    return "revise"

graph.add_conditional_edges("qa", _should_revise, {
    "revise": "increment_retry",
    "finish": END
})
```

3. **Usage:**
```python
from src.agents.supervisor_agent import generate_sop

result = await generate_sop(
    topic="Fire Safety",
    industry="Office",
    target_audience="Employees"
)
```

**Important:** This is the MAIN entry point for the entire system!
```

---

### **5.7 Understanding __init__.py Files** (NEW SECTION!)

**Add completely new section:**

```
Python requires __init__.py files to make directories importable as packages.

**What is __init__.py?**

A special Python file that:
1. Makes a directory a Python package
2. Controls what gets exported
3. Enables clean import syntax
4. Can be empty or contain initialization code

**File:** src/agents/__init__.py

**Complete Code:**
[Insert __init__.py code here - 52 lines]

**Why It's Required:**

**WITHOUT __init__.py:**
```python
from src.agents import PlanningAgent  
# ❌ ImportError: No module named 'src.agents'
```

**WITH __init__.py:**
```python
from src.agents import PlanningAgent  
# ✅ Works!
```

**What Goes in __init__.py:**

1. **Imports from submodules:**
```python
from src.agents.planning_agent import PlanningAgent
from src.agents.content_agent import ContentAgent
```

2. **Define __all__ (optional but recommended):**
```python
__all__ = [
    'PlanningAgent',
    'ContentAgent',
    'QAAgent',
    # ... etc
]
```

3. **Package metadata (optional):**
```python
__version__ = '1.0.0'
__author__ = 'Your Team'
```

**Required __init__.py Files in This Project:**
- src/__init__.py
- src/agents/__init__.py
- src/graph/__init__.py
- src/tools/__init__.py
- src/utils/__init__.py
- src/prompts/__init__.py
- tests/__init__.py

**Note:** These files can be empty (just create empty files), but filling them with imports makes your code cleaner.

**Example: Empty vs. Full __init__.py**

**Empty (minimal, but works):**
```python
# File: src/agents/__init__.py
# (empty file)
```

**Full (recommended, cleaner imports):**
```python
# File: src/agents/__init__.py
from src.agents.planning_agent import PlanningAgent
from src.agents.content_agent import ContentAgent
# ... etc

__all__ = ['PlanningAgent', 'ContentAgent', ...]
```

**Best Practice:** Create all __init__.py files, even if empty initially. You can always add exports later.
```

---

## SUMMARY OF CHANGES:

### Module 5 - OLD Structure:
- 5.1 Multi-Agent System (all code together) ❌

### Module 5 - NEW Structure:
- 5.1 Planning Agent ✅
- 5.2 Research Agent ✅
- 5.3 Content Agent ✅
- 5.4 Formatter Agent ✅
- 5.5 QA Agent ✅
- 5.6 Supervisor Agent ✅ (NEW!)
- 5.7 __init__.py Files ✅ (NEW!)

### Code Blocks to Add:
1. planning_agent.py (124 lines)
2. research_agent.py (177 lines)
3. content_agent.py (157 lines)
4. formatter_agent.py (149 lines)
5. qa_agent.py (179 lines)
6. supervisor_agent.py (158 lines) - NEW!
7. __init__.py (52 lines) - NEW!

**Total: 996 lines of separated, working code**

---

## ADDITIONAL UPDATES NEEDED:

### Module 3 - Add Note:
```
**Note:** The state_schema.py file defines the Pydantic models used 
throughout the workflow. This includes SOPState, SOPOutline, 
ResearchFindings, and QAResult classes.
```

### Module 4 - Update Reference:
```
**Note:** Module 4 covers the Planning Agent in detail. 
See Module 5.1 for the complete implementation.
```

### Module 6 - Add Cross-References:
```
**Note:** The prompts defined here are used in:
- Planning Agent (Module 5.1)
- Content Agent (Module 5.3)
- QA Agent (Module 5.5)
```

---

## VALIDATION CHECKLIST:

After updates, verify:
- [ ] All 7 code files are separated into individual sections
- [ ] Supervisor agent is included
- [ ] __init__.py explanation is added
- [ ] Cross-references between modules are updated
- [ ] Code block formatting is consistent
- [ ] Line numbers/lengths are accurate
- [ ] All code uses Strand SDK (not custom implementations)

---

**This update makes the course document match the actual working code!**
