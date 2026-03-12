# src/utils/crl_pdf_writer.py
"""
Generates a CRL-style PDF SOP with exact header and footer on every page,
matching the Word output from crl_docx_writer.py.

HEADER (every page):
┌─────────────┬──────────────────────┬──────────────────────────────┐
│ charles     │  STANDARD OPERATING  │  Doc #: GLBL-SOP-00060       │
│  river      │     PROCEDURE        │  Rev #: 6                    │
│  (italic)   │  (bold, centred)     │  Effective Date: 30/Nov/2024 │
├─────────────┴──────────────────────┴──────────────────────────────┤
│  Title: <SOP title here>                                          │
└───────────────────────────────────────────────────────────────────┘
        Status CURRENT, Confidential & Proprietary  (grey, centred)

FOOTER (every page):
══════════════════════════════════════   ← double rule
                            Page X of Y   ← right-aligned, live count

USAGE:
    from src.utils.crl_pdf_writer import write_crl_pdf
    write_crl_pdf(
        pdf_path="output.pdf",
        title="Global Technology Infrastructure Qualification SOP",
        document_id="GLBL-SOP-00060",
        version="6",
        effective_date="30/Nov/2024",
        markdown_body=state.formatted_markdown,
    )
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import black, HexColor
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle,
    ListFlowable, ListItem, Preformatted,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

# ─────────────────────────────────────────────────────────────
# PAGE LAYOUT  (points: 1 inch = 72 pt)
# ─────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = LETTER           # 612 × 792 pt

MARGIN_L   = 1.0  * inch          # 72 pt
MARGIN_R   = 1.0  * inch          # 72 pt
MARGIN_T   = 1.55 * inch          # space reserved above Frame for header
MARGIN_B   = 0.85 * inch          # space reserved below Frame for footer
CONTENT_W  = PAGE_W - MARGIN_L - MARGIN_R   # 468 pt

# Header draw positions
HDR_TOP    = PAGE_H - 0.20 * inch  # top of header bounding box
ROW1_H     = 0.52 * inch           # height of 3-column row
ROW2_H     = 0.28 * inch           # height of Title row
STATUS_H   = 0.22 * inch           # height of status line

# Footer draw positions
FTR_LINE_Y = 0.50 * inch           # y of the top rule line
FTR_TEXT_Y = 0.32 * inch           # y of "Page X of Y" text

# Header column widths (must sum to CONTENT_W = 468 pt)
COL_LOGO   = 1.30 * inch   # ~93.6 pt — "charles river"
COL_SOP    = 2.20 * inch   # 158.4 pt — "STANDARD OPERATING PROCEDURE"
COL_META   = CONTENT_W - COL_LOGO - COL_SOP   # 216.0 pt

GREY  = HexColor("#808080")
BLACK = black


# ─────────────────────────────────────────────────────────────
# FONT REGISTRATION
# ─────────────────────────────────────────────────────────────

def _register_fonts():
    """Register Arial from Windows Fonts if available; fall back to Helvetica."""
    candidates = {
        "Arial":        "C:\\Windows\\Fonts\\arial.ttf",
        "Arial-Bold":   "C:\\Windows\\Fonts\\arialbd.ttf",
        "Arial-Italic": "C:\\Windows\\Fonts\\ariali.ttf",
    }
    registered = {}
    for name, path in candidates.items():
        if Path(path).is_file():
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered[name] = True
            except Exception:
                pass
    return registered


_reg = _register_fonts()
FONT_N  = "Arial"        if "Arial"        in _reg else "Helvetica"
FONT_B  = "Arial-Bold"   if "Arial-Bold"   in _reg else "Helvetica-Bold"
FONT_I  = "Arial-Italic" if "Arial-Italic" in _reg else "Helvetica-Oblique"


# ─────────────────────────────────────────────────────────────
# "Page X of Y" CANVAS  — intercepts showPage to count pages
# ─────────────────────────────────────────────────────────────

class NumberedCanvas(Canvas):
    """
    Custom canvas that buffers all page operations so we can go back and
    stamp the correct total page count ("Page X of Y") on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            # Stamp "Page N of total" in the footer of this page
            self.setFont(FONT_N, 8)
            self.setFillColor(BLACK)
            page_num = state["_pageNumber"]
            self.drawRightString(
                MARGIN_L + CONTENT_W,
                FTR_TEXT_Y,
                f"Page {page_num} of {total}",
            )
            super().showPage()
        super().save()


# ─────────────────────────────────────────────────────────────
# HEADER / FOOTER DRAW FUNCTIONS (called on every page)
# ─────────────────────────────────────────────────────────────

def _draw_header(canvas, doc, title: str, document_id: str,
                 version: str, effective_date: str):
    canvas.saveState()

    x   = MARGIN_L
    y1  = HDR_TOP          # top of row 1

    # ── Row 1: three-column box ──────────────────────────────
    canvas.setStrokeColor(BLACK)
    canvas.setLineWidth(0.5)
    # Outer rect
    canvas.rect(x, y1 - ROW1_H, CONTENT_W, ROW1_H)
    # Column dividers
    canvas.line(x + COL_LOGO,            y1 - ROW1_H, x + COL_LOGO,            y1)
    canvas.line(x + COL_LOGO + COL_SOP,  y1 - ROW1_H, x + COL_LOGO + COL_SOP,  y1)

    # Cell 0 — "charles river" italic, vertically centred
    canvas.setFont(FONT_I, 9)
    canvas.setFillColor(BLACK)
    mid0 = x + COL_LOGO / 2
    canvas.drawCentredString(mid0, y1 - ROW1_H / 2 - 4, "charles river")

    # Cell 1 — "STANDARD OPERATING PROCEDURE" bold, two lines
    canvas.setFont(FONT_B, 9)
    mid1 = x + COL_LOGO + COL_SOP / 2
    canvas.drawCentredString(mid1, y1 - ROW1_H * 0.42, "STANDARD OPERATING")
    canvas.drawCentredString(mid1, y1 - ROW1_H * 0.68, "PROCEDURE")

    # Cell 2 — three metadata lines
    canvas.setFont(FONT_N, 7.5)
    mx = x + COL_LOGO + COL_SOP + 5   # left indent inside cell
    canvas.drawString(mx, y1 - 11, f"Doc #: {document_id}")
    canvas.drawString(mx, y1 - 22, f"Rev #: {version}")
    canvas.drawString(mx, y1 - 34, f"Effective Date: {effective_date}")

    # ── Row 2: full-width Title ──────────────────────────────
    y2 = y1 - ROW1_H
    canvas.rect(x, y2 - ROW2_H, CONTENT_W, ROW2_H)
    canvas.setFont(FONT_N, 8.5)
    canvas.setFillColor(BLACK)
    canvas.drawString(x + 5, y2 - ROW2_H / 2 - 4, f"Title: {title}"[:120])

    # ── Row 3: status line (grey, italic, centred) ───────────
    y3 = y2 - ROW2_H
    canvas.setFont(FONT_I, 8)
    canvas.setFillColor(GREY)
    canvas.drawCentredString(
        x + CONTENT_W / 2,
        y3 - STATUS_H / 2 - 2,
        "Status CURRENT, Confidential & Proprietary",
    )

    canvas.restoreState()


def _draw_footer_rules(canvas, doc):
    """Draw just the double-rule lines (page number is stamped by NumberedCanvas)."""
    canvas.saveState()
    canvas.setStrokeColor(BLACK)
    canvas.setLineWidth(0.75)
    canvas.line(MARGIN_L, FTR_LINE_Y + 4, MARGIN_L + CONTENT_W, FTR_LINE_Y + 4)
    canvas.setLineWidth(0.3)
    canvas.line(MARGIN_L, FTR_LINE_Y + 1, MARGIN_L + CONTENT_W, FTR_LINE_Y + 1)
    canvas.restoreState()


# ─────────────────────────────────────────────────────────────
# DOC TEMPLATE
# ─────────────────────────────────────────────────────────────

class CRLDocTemplate(BaseDocTemplate):

    def __init__(self, filename, title, document_id, version, effective_date, **kw):
        self._crl_title    = title
        self._crl_doc_id   = document_id
        self._crl_version  = version
        self._crl_eff_date = effective_date

        frame = Frame(
            MARGIN_L, MARGIN_B,
            CONTENT_W,
            PAGE_H - MARGIN_T - MARGIN_B,
            leftPadding=0, bottomPadding=0,
            rightPadding=0, topPadding=4,
        )

        super().__init__(
            filename,
            pagesize=LETTER,
            leftMargin=MARGIN_L, rightMargin=MARGIN_R,
            topMargin=MARGIN_T,  bottomMargin=MARGIN_B,
            **kw,
        )

        self.addPageTemplates([
            PageTemplate(
                id="crl",
                frames=[frame],
                onPage=self._on_page,
            )
        ])

    def _on_page(self, canvas, doc):
        _draw_header(canvas, doc,
                     self._crl_title, self._crl_doc_id,
                     self._crl_version, self._crl_eff_date)
        _draw_footer_rules(canvas, doc)


# ─────────────────────────────────────────────────────────────
# PARAGRAPH STYLES
# ─────────────────────────────────────────────────────────────

def _styles():
    return {
        "h1":   ParagraphStyle("SOP_H1",   fontName=FONT_B, fontSize=13, leading=16,
                                spaceBefore=14, spaceAfter=5),
        "h2":   ParagraphStyle("SOP_H2",   fontName=FONT_B, fontSize=11, leading=14,
                                spaceBefore=10, spaceAfter=4),
        "h3":   ParagraphStyle("SOP_H3",   fontName=FONT_B, fontSize=9.5, leading=12,
                                spaceBefore=8,  spaceAfter=3),
        "h4":   ParagraphStyle("SOP_H4",   fontName=FONT_B, fontSize=9,  leading=11,
                                spaceBefore=6,  spaceAfter=2),
        "body": ParagraphStyle("SOP_BODY", fontName=FONT_N, fontSize=9,  leading=12,
                                spaceBefore=2,  spaceAfter=3),
        "code": ParagraphStyle("SOP_CODE", fontName="Courier", fontSize=8, leading=10,
                                spaceBefore=2,  spaceAfter=2, leftIndent=12),
    }


# ─────────────────────────────────────────────────────────────
# TABLE RENDERER
# ─────────────────────────────────────────────────────────────

def _md_table(rows: List[List[str]]) -> Table:
    ncols  = max(len(r) for r in rows)
    col_w  = CONTENT_W / ncols
    widths = [col_w] * ncols

    def _clean(t):
        return re.sub(r"\*\*(.+?)\*\*", r"\1", t).strip()

    data = []
    for ri, row in enumerate(rows):
        cells = []
        for ci in range(ncols):
            val = _clean(row[ci]) if ci < len(row) else ""
            fn  = FONT_B if ri == 0 else FONT_N
            st  = ParagraphStyle(f"_tc", fontName=fn, fontSize=8, leading=10,
                                  spaceBefore=2, spaceAfter=2)
            # Escape for ReportLab XML
            safe = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            cells.append(Paragraph(safe, st))
        data.append(cells)

    tbl = Table(data, colWidths=widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("GRID",         (0, 0), (-1, -1), 0.5, black),
        ("BACKGROUND",   (0, 0), (-1,  0), HexColor("#EBEBEB")),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
    ]))
    return tbl


# ─────────────────────────────────────────────────────────────
# MARKDOWN PARSER
# ─────────────────────────────────────────────────────────────

def _xml_safe(t: str) -> str:
    return (t.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def _clean(t: str) -> str:
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"\*(.+?)\*",     r"\1", t)
    t = re.sub(r"^>\s*",         "",    t)
    return _xml_safe(t.strip())


def _md_to_flowables(md: str) -> list:
    S = _styles()
    lines  = md.splitlines()
    result = []
    i      = 0
    pending_bullets: list = []
    pending_numbers: list = []
    in_code = False

    number_re = re.compile(r"^\s*\d+\.\s+")

    def flush():
        nonlocal pending_bullets, pending_numbers
        if pending_bullets:
            items = [ListItem(Paragraph(t, S["body"]), leftIndent=12,
                              bulletColor=BLACK) for t in pending_bullets]
            result.append(ListFlowable(items, bulletType="bullet",
                                        bulletFontName=FONT_N, bulletFontSize=9,
                                        leftIndent=12, spaceBefore=2, spaceAfter=2))
            pending_bullets = []
        if pending_numbers:
            items = [ListItem(Paragraph(t, S["body"]), leftIndent=12)
                     for t in pending_numbers]
            result.append(ListFlowable(items, bulletType="1",
                                        bulletFontName=FONT_N, bulletFontSize=9,
                                        leftIndent=12, spaceBefore=2, spaceAfter=2))
            pending_numbers = []

    while i < len(lines):
        raw  = lines[i]
        line = raw.rstrip()

        # Skip pipeline-injected header metadata
        if re.match(r"^\*.*Doc #:.*\*$", line) or re.match(r"^\*.*CURRENT.*\*$", line):
            i += 1
            continue

        # Code fence
        if re.match(r"^```", line.strip()):
            flush()
            in_code = not in_code
            if not in_code:
                result.append(Spacer(1, 4))
            i += 1
            continue

        if in_code:
            result.append(Preformatted(raw, S["code"]))
            i += 1
            continue

        # Heading
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            flush()
            level = len(m.group(1))
            text  = _clean(m.group(2))
            st    = S.get(f"h{min(level, 4)}", S["h4"])
            result.append(Paragraph(text, st))
            i += 1
            continue

        # Table
        if line.strip().startswith("|"):
            flush()
            rows: List[List[str]] = []
            while i < len(lines):
                l = lines[i].rstrip()
                if not l.strip():
                    break
                if l.strip().startswith("|"):
                    if re.match(r"^\|[\s\-:|]+\|", l.strip()):
                        i += 1
                        continue
                    cols = [c.strip() for c in l.strip().strip("|").split("|")]
                    rows.append(cols)
                else:
                    break
                i += 1
            if rows:
                result.append(_md_table(rows))
                result.append(Spacer(1, 6))
            continue

        # Bullet
        if line.lstrip().startswith(("- ", "* ")):
            pending_bullets.append(_clean(line.lstrip()[2:]))
            i += 1
            continue

        # Numbered
        if number_re.match(line):
            pending_numbers.append(_clean(number_re.sub("", line)))
            i += 1
            continue

        # Blank
        if not line.strip():
            flush()
            result.append(Spacer(1, 4))
            i += 1
            continue

        # Normal paragraph
        flush()
        text = _clean(line)
        if text:
            result.append(Paragraph(text, S["body"]))
        i += 1

    flush()
    return result


# ─────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────

def write_crl_pdf(
    pdf_path,
    title: str,
    document_id: str,
    version: str,
    effective_date: str,
    markdown_body: str,
) -> None:
    """
    Write a PDF with exact CRL header/footer on every page.

    Parameters
    ----------
    pdf_path       : str or Path — output file path
    title          : SOP title
    document_id    : e.g. "GLBL-SOP-00060"
    version        : e.g. "6" or "1.0"
    effective_date : e.g. "30/Nov/2024"
    markdown_body  : formatted Markdown text from formatter_agent
    """
    flowables = _md_to_flowables(markdown_body)

    doc = CRLDocTemplate(
        str(pdf_path),
        title=title,
        document_id=document_id,
        version=version,
        effective_date=effective_date,
    )
    doc.build(flowables, canvasmaker=NumberedCanvas)