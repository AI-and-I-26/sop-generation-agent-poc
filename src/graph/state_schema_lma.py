"""
State Schema - File 1/14
Pydantic models for Strands workflow state

CRITICAL: This is used by ALL agents and the workflow.
Every field here must be compatible with agents.
"""

from typing import Any, Dict, List, Optional
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


# ============================================================
# NESTED OUTLINE MODELS (Fix for Planning JSON shape)
# ============================================================
class OutlineSubsection(BaseModel):
    """
    Nested subsection used in the SOP outline.
    Supports arbitrary depth via recursive 'subsections'.
    Example: 2.1, 2.1.1, 6.3.1.2, etc.
    """
    number: str = Field(..., description="Section number (e.g., '2.1', '6.3.1')")
    title: str = Field(..., description="Section/subsection title")
    subsections: List["OutlineSubsection"] = Field(
        default_factory=list,
        description="Nested subsections (recursive)"
    )

# Enable forward references for recursive type
OutlineSubsection.model_rebuild()


class OutlineSection(BaseModel):
    """
    Top-level section (1.0 .. 8.0) with nested subsections.
    """
    number: str = Field(..., description="Top-level section number (e.g., '1.0')")
    title: str = Field(..., description="Top-level section title")
    subsections: List[OutlineSubsection] = Field(
        default_factory=list,
        description="Nested subsections"
    )


class SOPOutline(BaseModel):
    """
    Complete SOP outline structure produced by the Planning agent.

    NOTE:
    - 'audience' is optional here; many pipelines still take it from SOPState.target_audience.
      Keeping it optional avoids breaking older runs and still allows newer prompts to pass it.
    """
    title: str = Field(..., description="SOP document title")
    industry: str = Field(..., description="Industry domain")
    audience: Optional[str] = Field(default=None, description="Target audience (optional)")
    sections: List[OutlineSection] = Field(..., min_length=5, description="All sections (1.0 .. 8.0)")
    estimated_pages: int = Field(default=5, ge=1, le=100, description="Estimated length (pages)")


# ============================================================
# OTHER AGENT MODELS (unchanged)
# ============================================================
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
    # If your QA later needs more subscores (e.g., safety, consistency), add here:
    # safety_score: float = Field(default=0.0, ge=0, le=10)
    # consistency_score: float = Field(default=0.0, ge=0, le=10)


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

    # IMPORTANT: allow structured sections (dicts), not just strings
    content_sections: Dict[str, Any] = Field(default_factory=dict, description="From content agent")

    # Keep both for compatibility: some formatters use 'formatted_document', newer ones use 'formatted_markdown'
    formatted_document: str = Field(default="", description="(Legacy) From formatter agent - full Markdown or rendered text")
    formatted_markdown: str = Field(default="", description="From formatter agent - KB-format Markdown")

    qa_result: Optional[QAResult] = Field(default=None, description="From QA agent")

    # ===== WORKFLOW CONTROL =====
    status: WorkflowStatus = Field(default=WorkflowStatus.INIT, description="Current status")
    current_node: Optional[str] = Field(default=None, description="Current node name")
    retry_count: int = Field(default=0, ge=0, le=5, description="Number of retries")
    errors: List[str] = Field(default_factory=list, description="Error log")

    # Gating flags (graph edge conditions)
    planning_complete: bool = Field(default=False, description="Planning node completed successfully")
    research_complete: bool = Field(default=False, description="Research node completed successfully")

    # ===== METADATA =====
    workflow_id: str = Field(default="", description="Unique workflow identifier")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    tokens_used: int = Field(default=0, ge=0, description="Total tokens consumed")

    # ===== AUX SIGNALS / POLICY GUARDS =====
    kb_hits: int = Field(default=0, ge=0, description="Number of KB retrieval hits")
    qa_policy_feedback: Optional[List[str]] = Field(default=None, description="Policy guard feedback for revisions")

    class Config:
        """Pydantic v2-compatible config (back-compat style)"""
        use_enum_values = True
        validate_assignment = True
        extra = "allow"  # tolerate minor agent drift while rolling out changes
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    # ---------------------------
    # Helper methods
    # ---------------------------
    def add_error(self, error: str) -> None:
        """Add error to error log with timestamp"""
        timestamp = datetime.utcnow().isoformat()
        self.errors.append(f"[{timestamp}] {error}")

    def increment_tokens(self, tokens: int) -> None:
        """Increment token counter"""
        try:
            self.tokens_used += int(tokens)
        except Exception:
            self.tokens_used = int(self.tokens_used or 0) + int(tokens or 0)

    def update_status(self, new_status: WorkflowStatus) -> None:
        """Update workflow status"""
        self.status = new_status

    def is_completed(self) -> bool:
        """Check if workflow is complete"""
        return self.status == WorkflowStatus.COMPLETED

    def needs_retry(self) -> bool:
        """Check if retry is needed"""
        return self.status == WorkflowStatus.FAILED and self.retry_count < 3