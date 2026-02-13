"""
Agents Package

This __init__.py file makes the 'agents' directory a Python package
and provides convenient imports.

WHY WE NEED __init__.py:
1. Makes directory a Python package (can import from it)
2. Provides clean import syntax
3. Controls what gets exported from the package
4. Allows relative imports within the package

Without __init__.py, you CANNOT do:
    from src.agents import PlanningAgent
    
With __init__.py, you CAN do:
    from src.agents import PlanningAgent, ContentAgent, QAAgent
"""

# Import all agents for easy access
from src.agents.planning_agent import PlanningAgent, planning_node
from src.agents.research_agent import ResearchAgent, research_node
from src.agents.content_agent import ContentAgent, content_node
from src.agents.formatter_agent import FormatterAgent, formatter_node
from src.agents.qa_agent import QAAgent, qa_node
from src.agents.supervisor_agent import SupervisorAgent, generate_sop

# Define what gets exported when someone does: from src.agents import *
__all__ = [
    'PlanningAgent',
    'ResearchAgent',
    'ContentAgent',
    'FormatterAgent',
    'QAAgent',
    'SupervisorAgent',
    'planning_node',
    'research_node',
    'content_node',
    'formatter_node',
    'qa_node',
    'generate_sop',
]

# Package metadata
__version__ = '1.0.0'
__author__ = 'Your Team'


# EXAMPLE USAGE WITH __init__.py:
"""
# Clean imports (ONLY possible because of __init__.py)
from src.agents import PlanningAgent, ContentAgent

# Create instances
planner = PlanningAgent()
writer = ContentAgent()

# WITHOUT __init__.py, you'd have to do:
from src.agents.planning_agent import PlanningAgent
from src.agents.content_agent import ContentAgent
# (much more verbose!)
"""
