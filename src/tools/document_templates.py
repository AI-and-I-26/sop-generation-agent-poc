# src/prompts/document_templates.py
"""
document_templates.py — Static SOP document header and footer templates.

LOCATION
--------
Place this file in the SAME folder as system_prompts.py:
    src/prompts/document_templates.py

The research_agent imports it as:
    from src.prompts.document_templates import KB_HEADER_TEMPLATE, KB_FOOTER_TEMPLATE

WHY THIS FILE EXISTS
--------------------
The old research_agent tried to extract header/footer templates from KB chunks
using regex heuristics (_looks_like_header, _looks_like_footer).  This approach
always silently returned empty strings because Bedrock Knowledge Base retrieval
returns semantic content slices from the MIDDLE of documents — they never
contain the page-1 metadata table or the last-page footer text that the
patterns were looking for.

Result: every generated SOP was produced with no document header or footer.

This file provides reliable static templates so every output document has a
proper document control header and footer regardless of KB content.

CUSTOMISATION
-------------
Edit KB_HEADER_TEMPLATE and KB_FOOTER_TEMPLATE below to match your
organisation's exact document control format.

Supported {{placeholders}} (substituted at format time by formatter_agent):
    {{title}}            SOP title  (from planning agent output)
    {{document_id}}      Auto-generated: SOP-YYYYMMDD-HHMM
    {{version}}          "1.0" for initial pipeline generation
    {{effective_date}}   Today's date formatted as DD-Mon-YYYY
    {{industry}}         From SOPState.industry
    {{target_audience}}  From SOPState.target_audience
"""

KB_HEADER_TEMPLATE = """\
---
| Field | Value |
|---|---|
| **Title** | {{title}} |
| **Document ID** | {{document_id}} |
| **Version** | {{version}} |
| **Effective Date** | {{effective_date}} |
| **Industry** | {{industry}} |
| **Target Audience** | {{target_audience}} |

---
"""

KB_FOOTER_TEMPLATE = (
    "\n---\n"
    "*This document is controlled. Unauthorised reproduction is prohibited.*\n"
    "*Always verify you are reading the current approved version before use.*"
)