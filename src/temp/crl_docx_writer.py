# src/utils/crl_docx_writer.py
"""
Generates a .docx with exact CRL per-page header and footer on EVERY page.

PAGE LAYOUT (US Letter, all units in twips — 1 inch = 1440 twips):
  Page:    12240 × 15840
  Margins: L=1440, R=1440, T=2160, B=1440
  Content width = 12240 - 1440 - 1440 = 9360 twips

HEADER TABLE column widths (must sum to 9360):
  Col 0 (charles river): 1800
  Col 1 (SOP title):     4500
  Col 2 (Doc#/Rev/Date): 3060
  Total:                 9360  ✓

FOOTER: double top-border paragraph, "Page X of Y" right-aligned
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime
from typing import List


# ──────────────────────────────────────────────────────────────
# PAGE LAYOUT (twips)
# ──────────────────────────────────────────────────────────────
PAGE_W    = 12240   # 8.5 in
PAGE_H    = 15840   # 11  in
MARGIN_L  = 1440    # 1.0 in
MARGIN_R  = 1440    # 1.0 in
MARGIN_T  = 2160    # 1.5 in  (header needs extra room)
MARGIN_B  = 1440    # 1.0 in
HDR_DIST  = 432     # 0.3 in
FTR_DIST  = 432     # 0.3 in

CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R   # 9360

# Header table columns — must sum EXACTLY to CONTENT_W
COL_LOGO   = 1800   # "charles river"
COL_TITLE  = 4500   # "STANDARD OPERATING PROCEDURE"
COL_META   = 3060   # Doc#, Rev#, Date
assert COL_LOGO + COL_TITLE + COL_META == CONTENT_W, "Column widths must sum to CONTENT_W"


# ──────────────────────────────────────────────────────────────
# XML NAMESPACES (used in every part file)
# ──────────────────────────────────────────────────────────────
_NS = (
    'xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
    'xmlns:mo="http://schemas.microsoft.com/office/mac/office/2008/main" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:mv="urn:schemas-microsoft-com:mac:vml" '
    'xmlns:o="urn:schemas-microsoft-com:office:office" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
    'xmlns:v="urn:schemas-microsoft-com:vml" '
    'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:w10="urn:schemas-microsoft-com:office:word" '
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
    'mc:Ignorable="w14 wp14"'
)


# ──────────────────────────────────────────────────────────────
# LOW-LEVEL XML HELPERS
# ──────────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def _rpr(font="Arial", sz=18, bold=False, italic=False, color="000000") -> str:
    b = "<w:b/>" if bold else '<w:b w:val="0"/>'
    i = "<w:i/>" if italic else '<w:i w:val="0"/>'
    return (
        f"<w:rPr>"
        f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}"/>'
        f"{b}{i}"
        f'<w:color w:val="{color}"/>'
        f'<w:sz w:val="{sz}"/>'
        f"</w:rPr>"
    )


def _run(text: str, **kw) -> str:
    space = ' xml:space="preserve"' if " " in text or text != text.strip() else ""
    return f"<w:r>{_rpr(**kw)}<w:t{space}>{_esc(text)}</w:t></w:r>"


def _para(inner: str, align: str = "left", before: int = 0, after: int = 0,
          top_border: str = "") -> str:
    jc  = f'<w:jc w:val="{align}"/>' if align != "left" else ""
    spc = f'<w:spacing w:before="{before}" w:after="{after}"/>'
    bdr = (
        f"<w:pBdr><w:top w:val=\"{top_border}\" w:sz=\"6\" "
        f'w:space="1" w:color="000000"/></w:pBdr>'
    ) if top_border else ""
    return f"<w:p><w:pPr>{jc}{spc}{bdr}</w:pPr>{inner}</w:p>"


def _all_borders() -> str:
    sides = ["top", "left", "bottom", "right", "insideH", "insideV"]
    return "<w:tblBorders>" + "".join(
        f'<w:{s} w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        for s in sides
    ) + "</w:tblBorders>"


def _cell(content: str, w: int, valign: str = "top") -> str:
    return (
        f"<w:tc>"
        f"<w:tcPr>"
        f'<w:tcW w:type="dxa" w:w="{w}"/>'
        f'<w:vAlign w:val="{valign}"/>'
        f"</w:tcPr>"
        f"{content}"
        f"</w:tc>"
    )


def _table(rows_xml: str, col_widths: List[int]) -> str:
    total = sum(col_widths)
    grid  = "".join(f'<w:gridCol w:w="{w}"/>' for w in col_widths)
    return (
        f"<w:tbl>"
        f"<w:tblPr>"
        f'<w:tblW w:type="dxa" w:w="{total}"/>'
        f'<w:jc w:val="left"/>'
        f"{_all_borders()}"
        f"</w:tblPr>"
        f"<w:tblGrid>{grid}</w:tblGrid>"
        f"{rows_xml}"
        f"</w:tbl>"
    )


# ──────────────────────────────────────────────────────────────
# HEADER XML
# ──────────────────────────────────────────────────────────────

def _header_xml(title: str, document_id: str,
                version: str, effective_date: str) -> str:
    """
    3-column top table + full-width title table + status paragraph.
    All widths are exact dxa (twips) values summing to CONTENT_W=9360.
    """
    # ── Cell 0: "charles river" italic, centred ───────────────────────
    c0 = _cell(
        _para(_run("charles river", sz=20, italic=True), align="center", before=60, after=60),
        COL_LOGO, valign="center"
    )

    # ── Cell 1: "STANDARD OPERATING" / "PROCEDURE" bold, centred ─────
    c1_inner = (
        _para(_run("STANDARD OPERATING", sz=22, bold=True), align="center", before=40, after=0) +
        _para(_run("PROCEDURE",          sz=22, bold=True), align="center", before=0,  after=40)
    )
    c1 = _cell(c1_inner, COL_TITLE, valign="center")

    # ── Cell 2: Doc#, Rev#, Effective Date ────────────────────────────
    c2_inner = (
        _para(_run(f"Doc #: {document_id}",       sz=17), before=40, after=40) +
        _para(_run(f"Rev #: {version}",            sz=17), before=0,  after=40) +
        _para(_run(f"Effective Date: {effective_date}", sz=17), before=0, after=40)
    )
    c2 = _cell(c2_inner, COL_META, valign="top")

    table1 = _table(f"<w:tr>{c0}{c1}{c2}</w:tr>", [COL_LOGO, COL_TITLE, COL_META])

    # ── Full-width Title row ──────────────────────────────────────────
    title_cell = _cell(
        _para(_run(f"Title: {title}", sz=19), before=60, after=60),
        CONTENT_W, valign="center"
    )
    table2 = _table(f"<w:tr>{title_cell}</w:tr>", [CONTENT_W])

    # ── Status line ───────────────────────────────────────────────────
    status = _para(
        _run("Status CURRENT, Confidential & Proprietary", sz=17, color="808080"),
        align="center", before=60, after=0
    )

    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:hdr {_NS}>"
        f"{table1}"
        f"{table2}"
        f"{status}"
        f"</w:hdr>"
    )


# ──────────────────────────────────────────────────────────────
# FOOTER XML
# ──────────────────────────────────────────────────────────────

def _footer_xml() -> str:
    """Double top-border paragraph with right-aligned PAGE / NUMPAGES fields."""

    def _field(instr: str) -> str:
        rpr = _rpr(sz=18)
        return (
            f"<w:r>{rpr}<w:fldChar w:fldCharType=\"begin\"/></w:r>"
            f"<w:r>{rpr}<w:instrText xml:space=\"preserve\"> {instr} </w:instrText></w:r>"
            f"<w:r>{rpr}<w:fldChar w:fldCharType=\"end\"/></w:r>"
        )

    rpr18 = _rpr(sz=18)
    inner = (
        f'<w:r>{rpr18}<w:t xml:space="preserve">Page </w:t></w:r>'
        f"{_field('PAGE')}"
        f'<w:r>{rpr18}<w:t xml:space="preserve"> of </w:t></w:r>'
        f"{_field('NUMPAGES')}"
    )

    para = (
        f"<w:p>"
        f"<w:pPr>"
        f'<w:jc w:val="right"/>'
        f'<w:spacing w:before="0" w:after="0"/>'
        f"<w:pBdr>"
        f'<w:top w:val="double" w:sz="6" w:space="1" w:color="000000"/>'
        f"</w:pBdr>"
        f"</w:pPr>"
        f"{inner}"
        f"</w:p>"
    )

    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:ftr {_NS}>{para}</w:ftr>"
    )


# ──────────────────────────────────────────────────────────────
# DOCUMENT BODY  (Markdown → Word XML)
# ──────────────────────────────────────────────────────────────

import re as _re

def _md_to_body(md: str) -> str:
    """Convert Markdown to Word body XML paragraphs/tables."""
    lines  = md.splitlines()
    result = []
    i = 0

    def body_para(text: str, bold: bool = False) -> str:
        clean = _re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        clean = _re.sub(r"\*(.+?)\*",     r"\1", clean)
        clean = _re.sub(r"^>\s*",         "",    clean).strip()
        if not clean:
            return ""
        sz = 20
        b  = "<w:b/>" if bold else ""
        rpr = f'<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>{b}<w:sz w:val="{sz}"/></w:rPr>'
        return (
            f"<w:p><w:pPr><w:spacing w:before=\"60\" w:after=\"60\"/></w:pPr>"
            f'<w:r>{rpr}<w:t xml:space="preserve">{_esc(clean)}</w:t></w:r></w:p>'
        )

    def heading(text: str, level: int) -> str:
        clean = _re.sub(r"\*\*(.+?)\*\*", r"\1", text).strip()
        sz_map = {1: 32, 2: 28, 3: 24, 4: 22}
        st_map = {1: "Heading1", 2: "Heading2", 3: "Heading3", 4: "Heading4"}
        sz  = sz_map.get(level, 22)
        st  = st_map.get(level, "Heading2")
        rpr = f'<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:sz w:val="{sz}"/></w:rPr>'
        return (
            f'<w:p><w:pPr><w:pStyle w:val="{st}"/>'
            f'<w:spacing w:before="120" w:after="60"/></w:pPr>'
            f'<w:r>{rpr}<w:t>{_esc(clean)}</w:t></w:r></w:p>'
        )

    def md_table(rows: List[List[str]]) -> str:
        if not rows:
            return ""
        ncols  = max(len(r) for r in rows)
        col_w  = CONTENT_W // ncols
        widths = [col_w] * ncols
        widths[-1] = CONTENT_W - col_w * (ncols - 1)
        grid   = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
        rows_xml = ""
        for ri, row in enumerate(rows):
            cells_xml = ""
            for ci in range(ncols):
                val  = row[ci] if ci < len(row) else ""
                val  = _re.sub(r"\*\*(.+?)\*\*", r"\1", val).strip()
                bold = "<w:b/>" if ri == 0 else ""
                rpr  = f'<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>{bold}<w:sz w:val="18"/></w:rPr>'
                cell_p = (
                    f"<w:p><w:pPr><w:spacing w:before=\"40\" w:after=\"40\"/></w:pPr>"
                    f'<w:r>{rpr}<w:t xml:space="preserve">{_esc(val)}</w:t></w:r></w:p>'
                )
                cells_xml += (
                    f"<w:tc>"
                    f'<w:tcPr><w:tcW w:type="dxa" w:w="{widths[ci]}"/></w:tcPr>'
                    f"{cell_p}</w:tc>"
                )
            rows_xml += f"<w:tr>{cells_xml}</w:tr>"
        total = sum(widths)
        return (
            f"<w:tbl>"
            f'<w:tblPr><w:tblW w:type="dxa" w:w="{total}"/>'
            f'<w:jc w:val="left"/>{_all_borders()}</w:tblPr>'
            f"<w:tblGrid>{grid}</w:tblGrid>"
            f"{rows_xml}</w:tbl>"
        )

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip pipeline-injected header metadata lines
        if _re.match(r"^\*.*Doc #:.*\*$", line) or _re.match(r"^\*.*CURRENT.*\*$", line):
            i += 1
            continue

        if not line.strip():
            i += 1
            continue

        # Heading
        m = _re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            result.append(heading(m.group(2), len(m.group(1))))
            i += 1
            continue

        # Table
        if line.strip().startswith("|"):
            table_rows: List[List[str]] = []
            while i < len(lines):
                l = lines[i].rstrip()
                if not l.strip():
                    break
                if l.strip().startswith("|"):
                    if _re.match(r"^\|[\s\-:|]+\|", l.strip()):
                        i += 1
                        continue
                    cols = [c.strip() for c in l.strip().strip("|").split("|")]
                    table_rows.append(cols)
                else:
                    break
                i += 1
            if table_rows:
                result.append(md_table(table_rows))
            continue

        # Code block
        if line.startswith("```"):
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                t = lines[i].rstrip()
                if t:
                    result.append(body_para(t))
                i += 1
            i += 1
            continue

        # Normal paragraph (strip list markers)
        text = _re.sub(r"^[-*]\s+", "", line)
        text = _re.sub(r"^\d+\.\s+", "", text)
        if text.strip():
            result.append(body_para(text))
        i += 1

    return "".join(result)


# ──────────────────────────────────────────────────────────────
# STATIC DOCX PART FILES
# ──────────────────────────────────────────────────────────────

_CONTENT_TYPES = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
            ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml"
            ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/header1.xml"
            ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
  <Override PartName="/word/footer1.xml"
            ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
  <Override PartName="/word/settings.xml"
            ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
</Types>
"""

_ROOT_RELS = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>
"""

_WORD_RELS = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
    Target="styles.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings"
    Target="settings.xml"/>
  <Relationship Id="rId3"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header"
    Target="header1.xml"/>
  <Relationship Id="rId4"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"
    Target="footer1.xml"/>
</Relationships>
"""

_SETTINGS = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:defaultTabStop w:val="720"/>
  <w:compat>
    <w:compatSetting w:name="compatibilityMode"
      w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>
  </w:compat>
</w:settings>
"""

_STYLES = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  mc:Ignorable="w14">
  <w:docDefaults><w:rPrDefault><w:rPr>
    <w:rFonts w:ascii="Arial" w:hAnsi="Arial"/>
    <w:sz w:val="20"/><w:szCs w:val="20"/>
  </w:rPr></w:rPrDefault></w:docDefaults>
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:pPr><w:spacing w:after="120"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="20"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:outlineLvl w:val="0"/><w:spacing w:before="240" w:after="120"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:sz w:val="32"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:outlineLvl w:val="1"/><w:spacing w:before="200" w:after="100"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:sz w:val="28"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:outlineLvl w:val="2"/><w:spacing w:before="160" w:after="80"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:sz w:val="24"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading4">
    <w:name w:val="heading 4"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:outlineLvl w:val="3"/><w:spacing w:before="120" w:after="60"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:b/><w:sz w:val="22"/></w:rPr>
  </w:style>
</w:styles>
"""


def _document_xml(body_xml: str) -> str:
    sect = (
        f"<w:sectPr>"
        f'<w:headerReference w:type="default" r:id="rId3"/>'
        f'<w:footerReference w:type="default" r:id="rId4"/>'
        f'<w:pgSz w:w="{PAGE_W}" w:h="{PAGE_H}"/>'
        f'<w:pgMar w:top="{MARGIN_T}" w:right="{MARGIN_R}" '
        f'w:bottom="{MARGIN_B}" w:left="{MARGIN_L}" '
        f'w:header="{HDR_DIST}" w:footer="{FTR_DIST}" w:gutter="0"/>'
        f'<w:cols w:space="720"/>'
        f'<w:docGrid w:linePitch="360"/>'
        f"</w:sectPr>"
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f"<w:document {_NS}>"
        f"<w:body>{body_xml}{sect}</w:body>"
        f"</w:document>"
    )


# ──────────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────────

def build_crl_docx(
    title: str,
    document_id: str,
    version: str,
    effective_date: str,
    markdown_body: str,
) -> bytes:
    """
    Build a complete .docx with CRL header/footer on every page.

    Parameters
    ----------
    title          : SOP title shown in header Title row
    document_id    : e.g. "GLBL-SOP-00060"
    version        : e.g. "6" or "1.0"
    effective_date : e.g. "30/Nov/2024"
    markdown_body  : formatted Markdown from formatter_agent

    Returns
    -------
    bytes — complete .docx file ready to write to disk
    """
    hdr  = _header_xml(title, document_id, version, effective_date)
    ftr  = _footer_xml()
    body = _md_to_body(markdown_body)
    doc  = _document_xml(body)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml",           _CONTENT_TYPES)
        zf.writestr("_rels/.rels",                   _ROOT_RELS)
        zf.writestr("word/_rels/document.xml.rels",  _WORD_RELS)
        zf.writestr("word/document.xml",             doc)
        zf.writestr("word/header1.xml",              hdr)
        zf.writestr("word/footer1.xml",              ftr)
        zf.writestr("word/styles.xml",               _STYLES)
        zf.writestr("word/settings.xml",             _SETTINGS)

    return buf.getvalue()


def write_crl_docx_from_state(state, output_path: str) -> str:
    """Convenience wrapper — pulls metadata from SOPState and writes .docx."""
    title          = getattr(state, "topic",          "Standard Operating Procedure")
    formatted_md   = (getattr(state, "formatted_markdown", "") or
                      getattr(state, "formatted_document",  "") or "")
    document_id    = (getattr(state, "document_id",    None) or
                      f"SOP-{datetime.now().strftime('%Y%m%d-%H%M')}")
    version        = getattr(state, "sop_version",    "1.0")
    effective_date = getattr(state, "effective_date",
                             datetime.now().strftime("%d/%b/%Y"))

    data = build_crl_docx(
        title=title,
        document_id=document_id,
        version=version,
        effective_date=effective_date,
        markdown_body=formatted_md,
    )
    with open(output_path, "wb") as fh:
        fh.write(data)
    return output_path
