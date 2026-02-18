"""
Output Schemas - File 4/14
JSON schemas for structured agent outputs

These schemas match the Pydantic models in state_schema.py
"""

# SOP Outline Schema - Used by Planning Agent
SOP_OUTLINE_SCHEMA = {
    "type": "object",
    "required": ["title", "industry", "sections"],
    "properties": {
        "title": {
            "type": "string",
            "description": "Complete SOP title",
            "minLength": 5,
            "maxLength": 200
        },
        "industry": {
            "type": "string",
            "description": "Industry or domain"
        },
        "sections": {
            "type": "array",
            "description": "All SOP sections",
            "minItems": 5,
            "items": {
                "type": "object",
                "required": ["number", "title"],
                "properties": {
                    "number": {
                        "type": "string",
                        "description": "Section number (1, 1.1, etc.)"
                    },
                    "title": {
                        "type": "string",
                        "description": "Section title"
                    },
                    "subsections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Subsection titles"
                    }
                }
            }
        },
        "estimated_pages": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "description": "Estimated document length in pages"
        }
    }
}


# Content Section Schema - Used by Content Agent
CONTENT_SECTION_SCHEMA = {
    "type": "object",
    "required": ["section_title", "content", "safety_warnings", "quality_checkpoints"],
    "properties": {
        "section_title": {
            "type": "string",
            "description": "Section title"
        },
        "content": {
            "type": "string",
            "description": "Detailed content with markdown formatting",
            "minLength": 100
        },
        "safety_warnings": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of safety warnings"
        },
        "quality_checkpoints": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Quality control checkpoints"
        },
        "time_estimate_minutes": {
            "type": "integer",
            "minimum": 1,
            "description": "Estimated time to complete in minutes"
        }
    }
}


# QA Result Schema - Used by QA Agent
QA_RESULT_SCHEMA = {
    "type": "object",
    "required": ["score", "feedback", "approved", "issues"],
    "properties": {
        "score": {
            "type": "number",
            "minimum": 0,
            "maximum": 10,
            "description": "Overall quality score from 0-10"
        },
        "feedback": {
            "type": "string",
            "description": "Detailed feedback on quality",
            "minLength": 50
        },
        "approved": {
            "type": "boolean",
            "description": "Whether SOP meets quality standards"
        },
        "issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of issues found (empty if none)"
        },
        "completeness_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 10,
            "description": "Completeness rating"
        },
        "clarity_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 10,
            "description": "Clarity rating"
        },
        "compliance_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 10,
            "description": "Compliance rating"
        }
    }
}


# Research Findings Schema - Used by Research Agent
RESEARCH_FINDINGS_SCHEMA = {
    "type": "object",
    "required": ["similar_sops", "compliance_requirements", "best_practices", "sources"],
    "properties": {
        "similar_sops": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "relevance": {"type": "number", "minimum": 0, "maximum": 1},
                    "key_points": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            "description": "Similar existing SOPs found"
        },
        "compliance_requirements": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Relevant regulations and compliance requirements"
        },
        "best_practices": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Industry best practices"
        },
        "sources": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Source references"
        }
    }
}


def get_schema_for_agent(agent_name: str) -> dict:
    """
    Get JSON schema for specific agent
    
    Args:
        agent_name: Name of agent (planning, content, qa, research)
        
    Returns:
        JSON schema dict
    """
    schemas = {
        "planning": SOP_OUTLINE_SCHEMA,
        "content": CONTENT_SECTION_SCHEMA,
        "qa": QA_RESULT_SCHEMA,
        "research": RESEARCH_FINDINGS_SCHEMA
    }
    
    return schemas.get(agent_name.lower(), {})
