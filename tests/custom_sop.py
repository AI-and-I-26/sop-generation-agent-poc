"""
Custom SOP Generator Template

INSTRUCTIONS:
1. Change the topic, industry, and audience below (lines ~170-172)
2. Run: python test/custom_sop.py
3. Your SOP will be saved to Markdown (.md), Word (.docx), and PDF (.pdf)

That's it!
"""

# -----------------------------
# Standard library imports
# -----------------------------
import asyncio                  # Provides the event loop for running async functions (async/await)
from pathlib import Path        # Convenient, cross-platform filesystem path handling
import sys                      # Access to interpreter internals (sys.path, stdout, etc.)
# sys.path.insert(0, '.')       # (Disabled) Would add current directory to module search path

import logging                  # Built-in logging framework for debug/info/warn/error logs
import os                       # (Currently unused) Often used for env vars / file ops

# -----------------------------
# Configure logging for the script
# -----------------------------
logging.basicConfig(level=logging.DEBUG)

# -----------------------------
# Resolve the project root path
# -----------------------------
# __file__ is the path to the current file (test/custom_sop.py).
# .resolve() gives an absolute path, following symlinks.
# .parents[1] means "go two levels up":
#   test/custom_sop.py -> test/ (parents[0])
#   test/ -> <repo_root>/      (parents[1])
# This establishes the project root dynamically, regardless of where the script is called from.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# -----------------------------
# Add the project root to sys.path
# -----------------------------
sys.path.insert(0, str(PROJECT_ROOT))

# -----------------------------
# Project import (your business logic)
# -----------------------------
from src.graph.sop_workflow import generate_sop

# =============================================================================
# Word (.docx) support (light Markdown-to-Word mapping)
# =============================================================================
_DOCX_AVAILABLE = True
try:
    from docx import Document
    from docx.shared import Pt
    from docx.oxml.shared import OxmlElement, qn
except Exception:
    _DOCX_AVAILABLE = False
    logging.warning(
        "python-docx is not installed or failed to import. "
        "Skipping .docx generation. Install with: pip install python-docx"
    )

def _docx_add_list_paragraph(doc, text, numbered=False):
    """Add a bullet or numbered list paragraph using Word's built-in list styles."""
    p = doc.add_paragraph(text)
    p.style = 'List Number' if numbered else 'List Bullet'
    return p

def _docx_add_code_paragraph(doc, text):
    """Add a monospace-looking 'code' paragraph (Word has no native code style)."""
    p = doc.add_paragraph()
    run = p.add_run(text)
    # Set a monospace font/size
    run.font.name = 'Consolas'
    run.font.size = Pt(10)
    # Ensure font sticks in some Word versions
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = OxmlElement('w:rFonts')
    rFonts.set(qn('w:ascii'), 'Consolas')
    rFonts.set(qn('w:hAnsi'), 'Consolas')
    rPr.append(rFonts)
    return p

def write_markdown_to_docx(doc: "Document", md_text: str, title: str, industry: str, audience: str):
    """
    Lightweight Markdown-to-Word mapper that supports:
      - Headings (#, ##, ###)
      - Bulleted lists (-, *)
      - Numbered lists (1., 2., ...)
      - Fenced code blocks (``` ... ```)
      - Normal paragraphs
    """
    # Title + metadata
    doc.add_heading(title, level=1)
    if industry:
        doc.add_paragraph(f"Industry: {industry}")
    if audience:
        doc.add_paragraph(f"Audience: {audience}")
    doc.add_paragraph("")  # spacing

    in_code_block = False
    code_fence = "```"

    for raw_line in md_text.splitlines():
        line = raw_line.rstrip()

        # Toggle code block state on ``` fences
        if line.strip().startswith(code_fence):
            in_code_block = not in_code_block
            if not in_code_block:
                # add spacing after closing fence
                doc.add_paragraph("")
            continue

        if in_code_block:
            _docx_add_code_paragraph(doc, raw_line)
            continue

        # Headings
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
            continue
        if line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
            continue
        if line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
            continue

        # Bulleted list (- or *)
        stripped_left = line.lstrip()
        if stripped_left.startswith("- ") or stripped_left.startswith("* "):
            text = stripped_left[2:].strip()
            _docx_add_list_paragraph(doc, text, numbered=False)
            continue

        # Numbered list (e.g., "1. something")
        if len(stripped_left) > 3 and stripped_left[0].isdigit() and stripped_left[1] == "." and stripped_left[2] == " ":
            text = stripped_left[3:].strip()
            _docx_add_list_paragraph(doc, text, numbered=True)
            continue

        # Blank line → spacing
        if line.strip() == "":
            doc.add_paragraph("")
            continue

        # Default: normal paragraph
        doc.add_paragraph(raw_line)


# =============================================================================
# PDF support via ReportLab (light Markdown-to-PDF mapping)
# =============================================================================
_PDF_AVAILABLE = True
try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Preformatted
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except Exception:
    _PDF_AVAILABLE = False
    logging.warning(
        "reportlab is not installed or failed to import. "
        "Skipping PDF generation. Install with: pip install reportlab"
    )

def _pdf_register_unicode_font(preferred_paths=None, font_name="DejaVuSans"):
    """
    Attempt to register a Unicode TrueType font for wider character support (e.g., ✓ ⚠️).
    If not found, PDF falls back to default fonts (may not render all glyphs).
    """
    if not _PDF_AVAILABLE:
        return None

    if preferred_paths is None:
        preferred_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",               # Linux (common)
            "/Library/Fonts/DejaVuSans.ttf",                                 # macOS (if installed)
            "C:\\Windows\\Fonts\\DejaVuSans.ttf",                             # Windows (if installed)
        ]
    for p in preferred_paths:
        try:
            if Path(p).is_file():
                pdfmetrics.registerFont(TTFont(font_name, p))
                return font_name
        except Exception:
            continue
    return None  # could not register; caller should use default fonts

def write_markdown_to_pdf(pdf_path: Path, md_text: str, title: str, industry: str, audience: str):
    """
    Lightweight Markdown-to-PDF using ReportLab Platypus.
    Supports:
      - Headings (#, ##, ###)
      - Bulleted lists (-, *)
      - Numbered lists (1., 2., ...)
      - Fenced code blocks (``` ... ```)
      - Normal paragraphs
    """
    if not _PDF_AVAILABLE:
        raise RuntimeError("ReportLab not available")

    # Try to enable broader Unicode coverage (optional). If not found, fallback.
    unicode_font = _pdf_register_unicode_font()
    base_font = unicode_font if unicode_font else "Helvetica"
    mono_font = unicode_font if unicode_font else "Courier"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=LETTER,
        leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54,  # ~0.75" margins
    )

    styles = getSampleStyleSheet()
    # Override / define styles we need
    styles.add(ParagraphStyle(name="SOP_H1", parent=styles["Heading1"], fontName=base_font, leading=20, spaceAfter=10))
    styles.add(ParagraphStyle(name="SOP_H2", parent=styles["Heading2"], fontName=base_font, leading=18, spaceAfter=8))
    styles.add(ParagraphStyle(name="SOP_H3", parent=styles["Heading3"], fontName=base_font, leading=16, spaceAfter=6))
    styles.add(ParagraphStyle(name="SOP_BODY", parent=styles["BodyText"], fontName=base_font, leading=14, spaceAfter=6))
    styles.add(ParagraphStyle(name="SOP_META", parent=styles["BodyText"], fontName=base_font, leading=12, spaceAfter=4))
    styles.add(ParagraphStyle(name="SOP_CODE", fontName=mono_font, fontSize=9, leading=11, spaceAfter=4))

    flow = []

    # Header
    if title:
        flow.append(Paragraph(title, styles["SOP_H1"]))
    if industry:
        flow.append(Paragraph(f"Industry: {industry}", styles["SOP_META"]))
    if audience:
        flow.append(Paragraph(f"Audience: {audience}", styles["SOP_META"]))
    flow.append(Spacer(1, 8))

    # Parse Markdown lines
    in_code_block = False
    code_fence = "```"

    # To group consecutive list items, accumulate then flush as ListFlowable
    pending_bullets = []
    pending_numbers = []

    def flush_lists():
        nonlocal pending_bullets, pending_numbers, flow
        if pending_bullets:
            items = [ListItem(Paragraph(text, styles["SOP_BODY"])) for text in pending_bullets]
            flow.append(ListFlowable(items, bulletType='bullet', start='circle', leftIndent=18))
            pending_bullets = []
            flow.append(Spacer(1, 4))
        if pending_numbers:
            items = [ListItem(Paragraph(text, styles["SOP_BODY"])) for text in pending_numbers]
            flow.append(ListFlowable(items, bulletType='1', leftIndent=18))
            pending_numbers = []
            flow.append(Spacer(1, 4))

    for raw_line in md_text.splitlines():
        line = raw_line.rstrip()

        # Toggle code block
        if line.strip().startswith(code_fence):
            # Flush any pending lists before entering/exiting code blocks
            flush_lists()
            in_code_block = not in_code_block
            if not in_code_block:
                flow.append(Spacer(1, 6))
            continue

        if in_code_block:
            flow.append(Preformatted(raw_line, styles["SOP_CODE"]))
            continue

        # Headings
        if line.startswith("### "):
            flush_lists()
            flow.append(Paragraph(line[4:].strip(), styles["SOP_H3"]))
            continue
        if line.startswith("## "):
            flush_lists()
            flow.append(Paragraph(line[3:].strip(), styles["SOP_H2"]))
            continue
        if line.startswith("# "):
            flush_lists()
            flow.append(Paragraph(line[2:].strip(), styles["SOP_H1"]))
            continue

        stripped_left = line.lstrip()

        # Bulleted list
        if stripped_left.startswith("- ") or stripped_left.startswith("* "):
            pending_bullets.append(stripped_left[2:].strip())
            continue

        # Numbered list (e.g., "1. something")
        if len(stripped_left) > 3 and stripped_left[0].isdigit() and stripped_left[1] == "." and stripped_left[2] == " ":
            pending_numbers.append(stripped_left[3:].strip())
            continue

        # Blank line
        if line.strip() == "":
            flush_lists()
            flow.append(Spacer(1, 6))
            continue

        # Default paragraph
        flush_lists()
        flow.append(Paragraph(raw_line, styles["SOP_BODY"]))

    # Flush any remaining list items
    flush_lists()

    # Build the PDF
    doc.build(flow)


# -----------------------------
# Define the asynchronous entry point
# -----------------------------
async def main():
    """
    Orchestrates the SOP generation workflow:
      - Ensures UTF-8 output works on some Windows terminals
      - Reads customization inputs (topic/industry/audience)
      - Calls the async SOP generator
      - Writes the generated SOP to:
          * Markdown (.md)
          * Word (.docx) with light Markdown mapping
          * PDF (.pdf) with light Markdown mapping
      - Prints a concise summary (status, optional QA score, file paths, size)
    """

    # (Optional) Ensure stdout prints UTF-8 glyphs (e.g., ⚡/⚠️/✓) in some Windows terminals.
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # ========================================================================
    # 🔧 CUSTOMIZE THESE VALUES:
    # ========================================================================
    TOPIC = "Global Technology Infrastructure Qualification SOP"   # ← The specific SOP subject
    INDUSTRY = "Information Technology (IT)"                       # ← The industry context
    AUDIENCE = "Information Technology (IT)"                       # ← The primary readership
    # ========================================================================

    # Pre-run summary
    print(f"\nGenerating SOP...")
    print(f"  Topic: {TOPIC}")
    print(f"  Industry: {INDUSTRY}")
    print(f"  Audience: {AUDIENCE}\n")

    # -----------------------------
    # Invoke the SOP generator
    # -----------------------------
    result = await generate_sop(
        topic=TOPIC,
        industry=INDUSTRY,
        target_audience=AUDIENCE
    )

    # -----------------------------
    # Persist the SOP to disk (Markdown)
    # -----------------------------
    safe_name = TOPIC.lower().replace(' ', '_')
    md_filename = f"sop_{safe_name}.md"
    with open(md_filename, "w", encoding="utf-8", newline="") as f:
        f.write(result.formatted_document)

    # -----------------------------
    # Persist the SOP to disk (Word .docx)
    # -----------------------------
    docx_filename = None
    if _DOCX_AVAILABLE:
        try:
            docx_filename = f"sop_{safe_name}.docx"
            doc = Document()
            write_markdown_to_docx(
                doc,
                md_text=result.formatted_document,
                title=TOPIC,
                industry=INDUSTRY,
                audience=AUDIENCE
            )
            doc.save(docx_filename)
        except Exception as e:
            logging.exception("Failed to create .docx file: %s", e)
            docx_filename = None
    else:
        logging.info("Skipping .docx generation (python-docx not available).")

    # -----------------------------
    # Persist the SOP to disk (PDF)
    # -----------------------------
    pdf_filename = None
    if _PDF_AVAILABLE:
        try:
            pdf_filename = f"sop_{safe_name}.pdf"
            write_markdown_to_pdf(
                pdf_path=Path(pdf_filename),
                md_text=result.formatted_document,
                title=TOPIC,
                industry=INDUSTRY,
                audience=AUDIENCE
            )
        except Exception as e:
            logging.exception("Failed to create PDF file: %s", e)
            pdf_filename = None
    else:
        logging.info("Skipping PDF generation (reportlab not available).")

    # -----------------------------
    # Print a post-run summary
    # -----------------------------
    print(f"✅ Generation complete!")
    print(f"   Status: {result.status}")

    if getattr(result, "qa_result", None):
        print(f"   QA Score: {result.qa_result.score}/10")
        print(f"   Approved: {result.qa_result.approved}")

    print(f"   Markdown File: {md_filename}")
    print(f"   Word File: {docx_filename if docx_filename else '(not created)'}")
    print(f"   PDF File: {pdf_filename if pdf_filename else '(not created)'}")
    print(f"   Size: {len(result.formatted_document):,} characters\n")


# -----------------------------
# Standard Python script guard
# -----------------------------
if __name__ == "__main__":
    asyncio.run(main())