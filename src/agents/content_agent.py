"""
Content Agent - Module 5, Section 5.1

Generates detailed SOP content using Strand Agent with few-shot prompting.
"""

import os
import json
import logging
from typing import Dict
from strands import Agent
from strands.types import ModelConfig

from src.graph.state_schema import SOPState, WorkflowStatus

logger = logging.getLogger(__name__)


class ContentAgent:
    """
    Content Generation Agent using Strand SDK
    
    Creates detailed, professional SOP content with proper formatting,
    safety warnings, and quality checkpoints.
    """
    
    def __init__(self):
        """Initialize Content Agent with Strand"""
        
        model_id = os.getenv('MODEL_CONTENT', 'meta.llama3-1-70b-instruct-v1:0')
        
        self.agent = Agent(
            name="ContentAgent",
            model=f"bedrock/{model_id}",
            system_prompt=self._get_system_prompt(),
            temperature=0.8,  # Higher for creativity
            max_tokens=3072,
            response_format={"type": "json_object"},
            model_config=ModelConfig(
                region=os.getenv('AWS_REGION', 'us-east-1')
            )
        )
        
        logger.info("Initialized ContentAgent")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt with few-shot examples"""
        return """You are a technical writer specializing in Standard Operating Procedures.

WRITING STYLE:
- Active voice and imperative mood ("Perform X" not "X should be performed")
- Specific and quantitative (exact numbers, temperatures, times)
- Clear and concise language
- Appropriate technical level for target audience

FORMATTING REQUIREMENTS:
1. Number all procedure steps (1., 2., 3.)
2. Mark safety warnings: ⚠️ WARNING: [warning text]
3. Mark critical notes: ⚡ CRITICAL: [critical information]
4. Mark quality checkpoints: ✓ CHECKPOINT: [what to verify]
5. Include time estimates

EXAMPLE OUTPUT:
{
  "section_title": "Emergency Shutdown Procedure",
  "content": "## Emergency Shutdown Procedure\\n\\n1. **Alert Personnel**\\n   - Activate emergency alarm\\n   - Announce over PA system\\n   - Estimated time: 10 seconds\\n\\n2. **Isolate System**\\n   - Rotate valve 90° clockwise\\n   - ✓ CHECKPOINT: Flow indicator shows zero\\n   - ⚠️ WARNING: Do not force valve\\n   - Estimated time: 30 seconds",
  "safety_warnings": ["Do not force valve past stop point"],
  "quality_checkpoints": ["Flow indicator shows zero"],
  "time_estimate_minutes": 5
}

OUTPUT FORMAT:
Always return valid JSON with these fields:
- section_title (string)
- content (string with markdown formatting)
- safety_warnings (array of strings)
- quality_checkpoints (array of strings)
- time_estimate_minutes (integer)
"""
    
    async def generate_section_content(
        self,
        section_title: str,
        research_findings: Dict,
        target_audience: str
    ) -> Dict:
        """
        Generate content for a section
        
        Args:
            section_title: Title of section
            research_findings: Research data
            target_audience: Target users
            
        Returns:
            Dict with content and metadata
        """
        
        # Extract relevant research
        best_practices = research_findings.get('best_practices', [])
        compliance = research_findings.get('compliance_requirements', [])
        
        prompt = f"""Write detailed content for this SOP section:

Section: {section_title}
Target Audience: {target_audience}

Relevant Information:
- Best Practices: {', '.join(best_practices) if best_practices else 'None'}
- Compliance: {', '.join(compliance) if compliance else 'None'}

Requirements:
1. Write clear, numbered steps
2. Include safety warnings where applicable
3. Add quality checkpoints
4. Provide time estimates
5. Use specific measurements and quantities

Return complete JSON with all required fields."""
        
        try:
            response = await self.agent.ainvoke(prompt)
            content_data = json.loads(response.content)
            
            logger.info(f"Generated content for: {section_title}")
            
            return content_data
            
        except Exception as e:
            logger.error(f"Content generation failed for {section_title}: {e}")
            raise
    
    async def execute(self, state: SOPState) -> SOPState:
        """Execute content agent"""
        try:
            # Generate content for each section in outline
            if not state.outline:
                raise ValueError("No outline available for content generation")
            
            content_sections = {}
            research_data = state.research.dict() if state.research else {}
            
            # Generate content for first 5 sections (or all if fewer)
            sections_to_generate = state.outline.sections[:5]
            
            for section in sections_to_generate:
                section_content = await self.generate_section_content(
                    section_title=section.title,
                    research_findings=research_data,
                    target_audience=state.target_audience
                )
                
                # Store the content
                content_sections[section.title] = section_content['content']
                
                state.increment_tokens(2500)
            
            state.content_sections = content_sections
            state.status = WorkflowStatus.WRITTEN
            state.current_node = "content"
            
            logger.info(f"Generated content for {len(content_sections)} sections")
            
        except Exception as e:
            state.add_error(f"Content generation failed: {str(e)}")
            state.status = WorkflowStatus.FAILED
        
        return state


# Standalone node function for Strand StateGraph
async def content_node(state: SOPState) -> SOPState:
    """Content generation node for Strand StateGraph"""
    agent = ContentAgent()
    return await agent.execute(state)
