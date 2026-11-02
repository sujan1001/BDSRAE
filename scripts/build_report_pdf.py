"""Build a compact, printable PDF version of report/technical_report.md."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "report" / "technical_report.md"
output = ROOT / "report" / "technical_report.pdf"


def ascii_safe(value: str) -> str:
    replacements = {
        "\u2013": "-", "\u2014": "-", "\u2011": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2022": "-", "\u00a0": " ",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def inline_markup(value: str) -> str:
    value = ascii_safe(value.strip())
    value = html.escape(value, quote=False)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"\*(.+?)\*", r"<i>\1</i>", value)
    value = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", value)
    return value


styles = getSampleStyleSheet()
title = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=24, alignment=TA_CENTER, spaceAfter=8)
subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=9, leading=12, alignment=TA_CENTER, textColor="#566270", spaceAfter=12)
h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=13, leading=16, spaceBefore=8, spaceAfter=5, textColor="#1D2A3A")
h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, spaceBefore=6, spaceAfter=3, textColor="#1F8A8C")
body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.6, leading=12.4, spaceAfter=6, textColor="#1D2A3A")
bullet = ParagraphStyle("Bullet", parent=body, leftIndent=12, firstLineIndent=-7, bulletIndent=0, spaceAfter=3)
small = ParagraphStyle("Small", parent=body, fontSize=7.6, leading=9.2, textColor="#566270")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor("#D5DCE3")
    canvas.line(18 * mm, 13 * mm, 192 * mm, 13 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor("#566270")
    canvas.drawString(18 * mm, 8 * mm, "Multilingual Retrieval Fairness | BDSRAE")
    canvas.drawRightString(192 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


story = []
lines = source.read_text(encoding="utf-8").splitlines()
for index, raw in enumerate(lines):
    line = raw.strip()
    if not line:
        story.append(Spacer(1, 2))
        continue
    if line.startswith("# "):
        story.append(Paragraph(inline_markup(line[2:]), title))
        story.append(HRFlowable(width="100%", thickness=1.2, color="#F47C20", spaceAfter=8))
    elif line.startswith("## "):
        story.append(Paragraph(inline_markup(line[3:]), h1))
    elif line.startswith("### "):
        story.append(Paragraph(inline_markup(line[4:]), h2))
    elif line.startswith("---"):
        story.append(PageBreak())
    elif line.startswith("-") or line.startswith("*"):
        story.append(Paragraph("- " + inline_markup(line[1:].strip()), bullet))
    elif line.startswith("[") and "] " in line:
        story.append(Paragraph(inline_markup(line), small))
    elif line.startswith("**"):
        story.append(Paragraph(inline_markup(line), subtitle))
    elif line.startswith(">"):
        story.append(Paragraph(inline_markup(line[1:]), small))
    elif line.startswith("|"):
        # Keep Markdown tables readable in the report without depending on a table parser.
        if set(line.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            continue
        story.append(Paragraph(inline_markup(line.replace("|", "  |  ")), small))
    else:
        story.append(Paragraph(inline_markup(line), body))

doc = SimpleDocTemplate(
    str(output), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
    topMargin=16 * mm, bottomMargin=18 * mm, title="Multilingual Retrieval Fairness Technical Report",
    author="Sujan S M and Swasthik Pamadi",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(output)

