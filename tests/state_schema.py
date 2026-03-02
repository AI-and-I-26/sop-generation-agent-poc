"""
state_schema.py — Pydantic models for the SOP generation workflow.

PURPOSE:
    Defines the single source of truth for all data that flows through
    the multi-agent SOP pipeline.  Every agent reads from and writes to
    an SOPState instance; the workflow orchestrator seeds and harvests it.

DESIGN PRINCIPLE — NO HARDCODED FORMAT RULES:
    SOPState carries a `kb_format_context` field populated by the research
    agent.  This field holds the formatting conventions extracted from
    whatever documents are in YOUR Knowledge Base — section titles, table
    structures, numbering patterns, writing style, etc.  All downstream
    agents (content, formatter, QA) read from this field rather than
    from any hardcoded template, so the output automatically mirrors your KB.

DEPENDENCY CHAIN:
    state_schema.py
        └─ used by state_store.py (keyed storage)
        └─ used by every agent (planning, research, content, formatter, qa)
        └─ used by sop_workflow.py (orchestration)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# WORKFLOW STATUS ENUM
# ============================================================
class WorkflowStatus(str, Enum):
    INIT        = "init"
    PLANNING    = "planning"
    PLANNED     = "planned"
    RESEARCHING = "researching"
    RESEARCHED  = "researched"
    WRITING     = "writing"
    WRITTEN     = "written"
    FORMATTING  = "formatting"
    FORMATTED   = "formatted"
    QA_REVIEW   = "qa_review"
    QA_COMPLETE = "qa_complete"
    COMPLETED   = "completed"
    FAILED      = "failed"


# ============================================================
# OUTLINE MODELS
# ============================================================

class OutlineSubsection(BaseModel):
    """
    Recursive nested subsection.
    Supports any depth: 2.1 → 2.1.1 → 2.1.1.1, etc.
    Section numbers and titles come from the KB's actual structure —
    not from any hardcoded template.
    """
    number: str = Field(..., description="Section number e.g. '2.1', '6.3.1'")
    title: str  = Field(..., description="Section title text")
    subsections: List["OutlineSubsection"] = Field(default_factory=list)

OutlineSubsection.model_rebuild()


class OutlineSection(BaseModel):
    """
    A top-level section with optional nested subsections.
    Numbers and titles are derived from the KB at runtime.
    """
    number: str = Field(..., description="Top-level number e.g. '1.0'")
    title: str  = Field(..., description="Exact section title")
    subsections: List[OutlineSubsection] = Field(default_factory=list)


class SOPOutline(BaseModel):
    """
    Full SOP outline produced by the planning agent.
    The section structure mirrors whatever the KB documents use.
    """
    title: str      = Field(..., description="SOP document title")
    industry: str   = Field(..., description="Industry domain")
    audience: Optional[str] = Field(default=None)
    sections: List[OutlineSection] = Field(..., min_length=1)
    estimated_pages: int = Field(default=10, ge=1, le=200)


# ============================================================
# RESEARCH FINDINGS MODEL
# ============================================================

class ResearchFindings(BaseModel):
    """
    Output from the research agent.

    KEY FIELD: kb_format_context
        Extracted from the actual KB documents retrieved during research.
        Contains the formatting conventions (section names, table columns,
        numbering style, writing tone, etc.) that all downstream agents
        use to match the KB's style.  This is what makes the pipeline
        KB-format-agnostic — the format is discovered at runtime, not hardcoded.
    """
    # KB-retrieved content
    similar_sops: List[Dict]      = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)
    best_practices: List[str]     = Field(default_factory=list)
    sources: List[str]            = Field(default_factory=list)

    # Per-section KB facts (keyed by section number, e.g. "1.0", "3.0")
    section_insights: Dict[str, Any] = Field(
        default_factory=dict,
        description="KB facts mapped to each SOP section number"
    )

    # Dynamic format conventions extracted from KB documents.
    # This replaces all hardcoded format rules.
    kb_format_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Formatting conventions discovered from KB documents: "
            "section_titles, table_sections, subsection_sections, "
            "writing_style, banned_elements, etc."
        )
    )


# ============================================================
# QA RESULT MODEL
# ============================================================

class QAResult(BaseModel):
    """Quality assurance evaluation scores and approval decision."""
    score:    float = Field(..., ge=0, le=10)
    feedback: str   = Field(...)
    issues:   List[str] = Field(default_factory=list)
    approved: bool  = Field(...)

    completeness_score: float = Field(default=0.0, ge=0, le=10)
    clarity_score:      float = Field(default=0.0, ge=0, le=10)
    safety_score:       float = Field(default=0.0, ge=0, le=10)
    compliance_score:   float = Field(default=0.0, ge=0, le=10)
    consistency_score:  float = Field(default=0.0, ge=0, le=10)


# ============================================================
# MAIN WORKFLOW STATE
# ============================================================

class SOPState(BaseModel):
    """
    Complete, mutable state for a single SOP generation run.

    LIFECYCLE:
        sop_workflow.py creates → stored in STATE_STORE →
        each agent reads/writes its fields →
        sop_workflow.py reads final state after graph completion.

    KB FORMAT PROPAGATION:
        The research agent writes kb_format_context (discovered from KB).
        The content, formatter, and QA agents read kb_format_context
        and use it to match the KB's style — without any hardcoded rules.
    """

    # ── INPUT PARAMETERS ──────────────────────────────────────────────────
    topic:            str       = Field(...)
    industry:         str       = Field(...)
    target_audience:  str       = Field(...)
    requirements:     List[str] = Field(default_factory=list)

    # ── AGENT OUTPUTS ─────────────────────────────────────────────────────
    outline:             Optional[SOPOutline]       = Field(default=None)
    research:            Optional[ResearchFindings] = Field(default=None)
    content_sections:    Dict[str, Any]             = Field(default_factory=dict)
    formatted_document:  str = Field(default="")   # legacy alias
    formatted_markdown:  str = Field(default="")   # primary output
    qa_result:           Optional[QAResult]        = Field(default=None)

    # ── KB FORMAT CONTEXT (shortcut) ──────────────────────────────────────
    # Copied from research.kb_format_context after research completes,
    # so agents can access it directly without going through research.
    kb_format_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dynamic KB formatting conventions — discovered at runtime"
    )

    # ── WORKFLOW CONTROL ──────────────────────────────────────────────────
    status:       WorkflowStatus   = Field(default=WorkflowStatus.INIT)
    current_node: Optional[str]    = Field(default=None)
    retry_count:  int              = Field(default=0, ge=0, le=5)
    errors:       List[str]        = Field(default_factory=list)

    planning_complete: bool  = Field(default=False)
    research_complete: bool  = Field(default=False)

    # ── METADATA ──────────────────────────────────────────────────────────
    workflow_id:  str              = Field(default="")
    started_at:   Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    tokens_used:  int              = Field(default=0, ge=0)

    # ── AUX ───────────────────────────────────────────────────────────────
    kb_hits:             int                    = Field(default=0, ge=0)
    qa_policy_feedback:  Optional[List[str]]    = Field(default=None)

    class Config:
        use_enum_values    = True
        validate_assignment = True
        extra = "allow"
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    def add_error(self, error: str) -> None:
        self.errors.append(f"[{datetime.utcnow().isoformat()}] {error}")

    def increment_tokens(self, tokens: int) -> None:
        try:
            self.tokens_used += int(tokens)
        except Exception:
            self.tokens_used = int(self.tokens_used or 0) + int(tokens or 0)

    def update_status(self, new_status: WorkflowStatus) -> None:
        self.status = new_status

    def is_completed(self) -> bool:
        return self.status == WorkflowStatus.COMPLETED

    def needs_retry(self) -> bool:
        return self.status == WorkflowStatus.FAILED and self.retry_count < 3
