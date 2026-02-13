"""
Formatter Agent - Module 5, Section 5.1

Formats final SOP document using Strand Agent.
Uses smaller/cheaper model (Llama 8B) for cost optimization.
"""

import os
import logging
from datetime import datetime
from strands import Agent
from strands.types import ModelConfig

from src.graph.state_schema import SOPState, WorkflowStatus

logger = logging.getLogger(__name__)


class FormatterAgent:
    """
    Formatter Agent using Strand SDK
    
    Combines all sections into a cohesive, professionally formatted document.
    Uses Llama 8B model for cost efficiency.
    """
    
    def __init__(self):
        """Initialize Formatter Agent with Strand"""
        
        # Use smaller model for cost optimization
        model_id = os.getenv('MODEL_FORMATTER', 'meta.llama3-1-8b-instruct-v1:0')
        
        self.agent = Agent(
            name="FormatterAgent",
            model=f"bedrock/{model_id}",
            system_prompt=self._get_system_prompt(),
            temperature=0.3,  # Lower for consistency
            max_tokens=2048,
            model_config=ModelConfig(
                region=os.getenv('AWS_REGION', 'us-east-1')
            )
        )
        
        logger.info(f"Initialized FormatterAgent with model: {model_id}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for formatter"""
        return """You are a document formatting specialist for Standard Operating Procedures.

Your job is to format SOP content into a professional, cohesive document.

DOCUMENT STRUCTURE:
# [SOP Title]

**Document Control**
- Document ID: SOP-XXX
- Version: 1.0
- Effective Date: [Date]
- Industry: [Industry]
- Target Audience: [Audience]

---

## Table of Contents
[Auto-generated from sections]

---

[All sections with consistent formatting]

---

**Approval Signatures**
[Signature block]

FORMATTING RULES:
- Use # for main title
- Use ## for section headings
- Use ### for subsection headings
- Preserve all numbered steps
- Keep all safety warnings and checkpoints
- Maintain consistent spacing
- Number all sections hierarchically

CRITICAL:
- Preserve ALL content exactly as provided
- Do not modify technical details
- Keep all safety warnings intact
- Maintain professional tone
"""
    
    async def format_document(
        self,
        title: str,
        industry: str,
        target_audience: str,
        content_sections: dict
    ) -> str:
        """
        Format complete SOP document
        
        Args:
            title: SOP title
            industry: Industry
            target_audience: Target users
            content_sections: Dict of section_title: content
            
        Returns:
            Formatted markdown document
        """
        
        # Build document structure
        doc_parts = []
        
        # Title and metadata
        doc_parts.append(f"# {title}")
        doc_parts.append("")
        doc_parts.append("**Document Control**")
        doc_parts.append(f"- Document ID: SOP-{datetime.now().strftime('%Y%m%d-%H%M')}")
        doc_parts.append("- Version: 1.0")
        doc_parts.append(f"- Effective Date: {datetime.now().strftime('%Y-%m-%d')}")
        doc_parts.append(f"- Industry: {industry}")
        doc_parts.append(f"- Target Audience: {target_audience}")
        doc_parts.append("")
        doc_parts.append("---")
        doc_parts.append("")
        
        # Table of contents
        doc_parts.append("## Table of Contents")
        doc_parts.append("")
        for i, section_title in enumerate(content_sections.keys(), 1):
            doc_parts.append(f"{i}. {section_title}")
        doc_parts.append("")
        doc_parts.append("---")
        doc_parts.append("")
        
        # All sections
        for section_title, content in content_sections.items():
            doc_parts.append(f"## {section_title}")
            doc_parts.append("")
            doc_parts.append(content)
            doc_parts.append("")
            doc_parts.append("---")
            doc_parts.append("")
        
        # Signature block
        doc_parts.append("**Approval Signatures**")
        doc_parts.append("")
        doc_parts.append("Prepared by: _________________ Date: _______")
        doc_parts.append("")
        doc_parts.append("Reviewed by: _________________ Date: _______")
        doc_parts.append("")
        doc_parts.append("Approved by: _________________ Date: _______")
        
        formatted_doc = "\n".join(doc_parts)
        
        logger.info(f"Formatted document with {len(content_sections)} sections")
        
        return formatted_doc
    
    async def execute(self, state: SOPState) -> SOPState:
        """Execute formatter agent"""
        try:
            if not state.content_sections:
                raise ValueError("No content sections available for formatting")
            
            formatted_doc = await self.format_document(
                title=state.outline.title if state.outline else state.topic,
                industry=state.industry,
                target_audience=state.target_audience,
                content_sections=state.content_sections
            )
            
            state.formatted_document = formatted_doc
            state.status = WorkflowStatus.FORMATTED
            state.current_node = "formatter"
            state.increment_tokens(800)  # Smaller model uses fewer tokens
            
        except Exception as e:
            state.add_error(f"Formatting failed: {str(e)}")
            state.status = WorkflowStatus.FAILED
        
        return state


# Standalone node function for Strand StateGraph
async def formatter_node(state: SOPState) -> SOPState:
    """Formatter node for Strand StateGraph"""
    agent = FormatterAgent()
    return await agent.execute(state)
