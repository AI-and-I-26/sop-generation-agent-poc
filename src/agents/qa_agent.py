"""
QA Agent - Module 5, Section 5.1

Quality assurance agent that reviews SOP documents.
Uses Strand Agent with JSON schema for structured scoring.
"""

import os
import json
import re
import logging
from strands import Agent
from strands.types import ModelConfig

from src.graph.state_schema import SOPState, QAResult, WorkflowStatus

logger = logging.getLogger(__name__)


class QAAgent:
    """
    Quality Assurance Agent using Strand SDK
    
    Reviews SOP documents for quality, completeness, safety, and compliance.
    Returns structured feedback with scores.
    """
    
    def __init__(self):
        """Initialize QA Agent with Strand"""
        
        model_id = os.getenv('MODEL_QA', 'meta.llama3-1-70b-instruct-v1:0')
        
        self.agent = Agent(
            name="QAAgent",
            model=f"bedrock/{model_id}",
            system_prompt=self._get_system_prompt(),
            temperature=0.5,  # Moderate for consistent evaluation
            max_tokens=2048,
            response_format={"type": "json_object"},
            model_config=ModelConfig(
                region=os.getenv('AWS_REGION', 'us-east-1')
            )
        )
        
        logger.info("Initialized QAAgent")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for QA agent"""
        return """You are a quality assurance specialist for Standard Operating Procedures.

EVALUATION CRITERIA:

1. **Completeness** (0-10):
   - All mandatory sections present
   - Adequate detail in procedures
   - No obvious gaps

2. **Clarity** (0-10):
   - Instructions clear and unambiguous
   - Appropriate technical level
   - Logical step ordering

3. **Safety** (0-10):
   - All hazards identified
   - Appropriate warnings
   - PPE specified
   - Emergency procedures included

4. **Compliance** (0-10):
   - Regulations referenced
   - Industry standards followed
   - Requirements met

5. **Consistency** (0-10):
   - Formatting uniform
   - Terminology consistent
   - Numbering correct

SCORING:
- Calculate overall score (average of all criteria)
- Score ≥ 8.0 = APPROVED
- Score < 8.0 = NEEDS REVISION

OUTPUT FORMAT:
Return valid JSON:
{
  "score": 8.5,
  "feedback": "Detailed feedback here",
  "approved": true,
  "issues": ["Issue 1", "Issue 2"],
  "completeness_score": 9.0,
  "clarity_score": 8.5,
  "safety_score": 8.0,
  "compliance_score": 8.5,
  "consistency_score": 9.0
}

Be thorough, objective, and provide specific, actionable feedback.
"""
    
    async def review_document(
        self,
        document: str,
        topic: str,
        industry: str
    ) -> QAResult:
        """
        Review SOP document
        
        Args:
            document: Formatted document text
            topic: SOP topic
            industry: Industry domain
            
        Returns:
            QAResult with scores and feedback
        """
        
        # Truncate document for review (first 3000 chars)
        doc_sample = document[:3000] + "..." if len(document) > 3000 else document
        
        prompt = f"""Review this SOP document:

Topic: {topic}
Industry: {industry}

Document Sample:
{doc_sample}

Provide comprehensive quality assessment with:
1. Overall score (0-10)
2. Individual criterion scores
3. Specific feedback on strengths and weaknesses
4. List of issues to address
5. Approval decision (true if score ≥ 8.0)

Return complete JSON with all required fields."""
        
        try:
            response = await self.agent.ainvoke(prompt)
            qa_data = json.loads(response.content)
            
            # Validate with Pydantic
            qa_result = QAResult(**qa_data)
            
            logger.info(f"QA Review complete. Score: {qa_result.score}, Approved: {qa_result.approved}")
            
            return qa_result
            
        except Exception as e:
            logger.error(f"QA review failed: {e}")
            # Return default low score
            return QAResult(
                score=5.0,
                feedback=f"QA review error: {str(e)}",
                approved=False,
                issues=["QA review failed"],
                completeness_score=5.0,
                clarity_score=5.0,
                compliance_score=5.0
            )
    
    async def execute(self, state: SOPState) -> SOPState:
        """Execute QA agent"""
        try:
            if not state.formatted_document:
                raise ValueError("No formatted document available for QA")
            
            qa_result = await self.review_document(
                document=state.formatted_document,
                topic=state.topic,
                industry=state.industry
            )
            
            state.qa_result = qa_result
            state.status = WorkflowStatus.QA_COMPLETE
            state.current_node = "qa"
            state.increment_tokens(1500)
            
            # Check if approved
            if qa_result.approved:
                logger.info(f"✓ SOP APPROVED with score: {qa_result.score}")
            else:
                logger.warning(f"⚠ SOP NEEDS REVISION. Score: {qa_result.score}")
            
        except Exception as e:
            state.add_error(f"QA review failed: {str(e)}")
            state.status = WorkflowStatus.FAILED
        
        return state


# Standalone node function for Strand StateGraph
async def qa_node(state: SOPState) -> SOPState:
    """QA review node for Strand StateGraph"""
    agent = QAAgent()
    return await agent.execute(state)
