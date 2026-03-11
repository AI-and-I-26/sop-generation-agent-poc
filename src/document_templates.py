# src/prompts/document_templates.py
"""
document_templates.py — CRL-style SOP document header and footer templates.

These templates are injected by formatter_agent:
  - KB_HEADER_TEMPLATE  : rendered once at the top of the Markdown document
                          and repeated at the start of each major section
                          (so that when rendered to Word/PDF every page has it)
  - KB_FOOTER_TEMPLATE  : appended at the end of the whole document

For true per-page rendering in Word/PDF, the formatter_agent also
injects KB_PAGE_HEADER_LINE as a Word section header string into python-docx.

Supported {{placeholders}} (substituted at format time by formatter_agent):
    {{title}}            SOP title
    {{document_id}}      Auto-generated: SOP-YYYYMMDD-HHMM
    {{version}}          "1.0" for initial pipeline generation
    {{effective_date}}   Today's date formatted as DD-Mon-YYYY
    {{industry}}         From SOPState.industry
    {{target_audience}}  From SOPState.target_audience
    {{status}}           Always "CURRENT" for newly generated SOPs
    {{classification}}   Always "Confidential and Proprietary"
"""

# ---------------------------------------------------------------------------
# Full document-control header — rendered at the TOP of the SOP document
# (Markdown / Word cover block)
# ---------------------------------------------------------------------------
KB_HEADER_TEMPLATE = """\
---

| Field | Value |
|---|---|
| **Title** | {{title}} |
| **Document ID** | {{document_id}} |
| **Version** | {{version}} |
| **Status** | {{status}} |
| **Effective Date** | {{effective_date}} |
| **Classification** | {{classification}} |
| **Industry** | {{industry}} |
| **Target Audience** | {{target_audience}} |

> **{{status}} — {{classification}}**
> This document is subject to controlled document management.
> Approval signatures (wet or electronic per 21 CFR Part 11) are required
> before this SOP is placed into operational use.
> Always verify you are reading the current approved version before use.

---

"""

# ---------------------------------------------------------------------------
# Per-section page header line — prepended to EVERY section heading in the
# Markdown body so that when converted to Word/PDF each page carries the
# document identity line.
# Format:  {{document_id}} | {{title}} | Version {{version}} | {{status}} — {{classification}} | Page x of y
# ---------------------------------------------------------------------------
KB_PAGE_HEADER_LINE = (
    "*{{document_id}} | {{title}} | Version {{version}} | "
    "{{status}} — {{classification}}*"
)

# ---------------------------------------------------------------------------
# Document footer — appended once at the very end of the SOP
# ---------------------------------------------------------------------------
KB_FOOTER_TEMPLATE = (
    "\n\n---\n\n"
    "| Field | Value |\n"
    "|---|---|\n"
    "| **Document ID** | {{document_id}} |\n"
    "| **Version** | {{version}} |\n"
    "| **Status** | {{status}} |\n"
    "| **Effective Date** | {{effective_date}} |\n"
    "| **Classification** | {{classification}} |\n\n"
    "*This document is controlled. Unauthorised reproduction is prohibited.*  \n"
    "*{{status}} — {{classification}}*  \n"
    "*Always verify you are reading the current approved version before use.*"
)

# ---------------------------------------------------------------------------
# Default substitution values (formatter_agent overrides these at runtime)
# ---------------------------------------------------------------------------
KB_TEMPLATE_DEFAULTS = {
    "status": "CURRENT",
    "classification": "Confidential and Proprietary",
    "version": "1.0",
}
