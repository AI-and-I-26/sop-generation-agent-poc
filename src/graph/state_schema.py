"""
State Schema - File 1/14
Pydantic models for Strands workflow state

CRITICAL: This is used by ALL agents and the workflow.
Every field here must be compatible with agents.
"""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class WorkflowStatus(str, Enum):
    """Workflow status enumeration"""
    INIT = "init"
    PLANNING = "planning"
    PLANNED = "planned"
    RESEARCHING = "researching"
    RESEARCHED = "researched"
    WRITING = "writing"
    WRITTEN = "written"
    FORMATTING = "formatting"
    FORMATTED = "formatted"
    QA_REVIEW = "qa_review"
    QA_COMPLETE = "qa_complete"
    COMPLETED = "completed"
    FAILED = "failed"


class SectionOutline(BaseModel):
    """Individual section in SOP outline"""
    number: str = Field(..., description="Section number (e.g., '1.1')")
    title: str = Field(..., description="Section title")
    subsections: List[str] = Field(default_factory=list, description="Subsection titles")
    
    class Config:
        json_schema_extra = {
            "example": {
                "number": "1.1",
                "title": "Purpose and Scope",
                "subsections": ["1.1.1 Purpose", "1.1.2 Scope"]
            }
        }


class SOPOutline(BaseModel):
    """Complete SOP outline structure - matches agent output"""
    title: str = Field(..., description="SOP document title")
    industry: str = Field(..., description="Industry domain")
    sections: List[SectionOutline] = Field(..., min_length=5, description="All sections")
    estimated_pages: int = Field(default=5, ge=1, le=100, description="Estimated length")


class ResearchFindings(BaseModel):
    """Research results from RAG - matches research agent output"""
    similar_sops: List[Dict] = Field(default_factory=list, description="Similar SOPs found")
    compliance_requirements: List[str] = Field(default_factory=list, description="Regulations")
    best_practices: List[str] = Field(default_factory=list, description="Best practices")
    sources: List[str] = Field(default_factory=list, description="Source references")


class QAResult(BaseModel):
    """Quality assurance results - matches QA agent output"""
    score: float = Field(..., ge=0, le=10, description="Overall quality score 0-10")
    feedback: str = Field(..., description="Detailed feedback")
    issues: List[str] = Field(default_factory=list, description="Issues found")
    approved: bool = Field(..., description="Whether SOP is approved")
    completeness_score: float = Field(default=0.0, ge=0, le=10)
    clarity_score: float = Field(default=0.0, ge=0, le=10)
    compliance_score: float = Field(default=0.0, ge=0, le=10)


class SOPState(BaseModel):
    """
    Complete state for Strands workflow
    
    This is the SINGLE source of truth for workflow state.
    All agents read from and write to this state.
    """
    
    # ===== INPUT PARAMETERS =====
    topic: str = Field(..., description="SOP topic/title")
    industry: str = Field(..., description="Industry domain")
    target_audience: str = Field(..., description="Target users")
    requirements: List[str] = Field(default_factory=list, description="Additional requirements")
    
    # ===== AGENT OUTPUTS =====
    outline: Optional[SOPOutline] = Field(default=None, description="From planning agent")
    research: Optional[ResearchFindings] = Field(default=None, description="From research agent")
    content_sections: Dict[str, str] = Field(default_factory=dict, description="From content agent")
    formatted_document: str = Field(default="", description="From formatter agent")
    qa_result: Optional[QAResult] = Field(default=None, description="From QA agent")
    
    # ===== WORKFLOW CONTROL =====
    status: WorkflowStatus = Field(default=WorkflowStatus.INIT, description="Current status")
    current_node: Optional[str] = Field(default=None, description="Current node name")
    retry_count: int = Field(default=0, ge=0, le=5, description="Number of retries")
    errors: List[str] = Field(default_factory=list, description="Error log")
    
    # ===== METADATA =====
    workflow_id: str = Field(default="", description="Unique workflow identifier")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    tokens_used: int = Field(default=0, ge=0, description="Total tokens consumed")
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def add_error(self, error: str) -> None:
        """Add error to error log with timestamp"""
        timestamp = datetime.utcnow().isoformat()
        self.errors.append(f"[{timestamp}] {error}")
    
    def increment_tokens(self, tokens: int) -> None:
        """Increment token counter"""
        self.tokens_used += tokens
    
    def update_status(self, new_status: WorkflowStatus) -> None:
        """Update workflow status"""
        self.status = new_status
    
    def is_completed(self) -> bool:
        """Check if workflow is complete"""
        return self.status == WorkflowStatus.COMPLETED
    
    def needs_retry(self) -> bool:
        """Check if retry is needed"""
        return self.status == WorkflowStatus.FAILED and self.retry_count < 3
