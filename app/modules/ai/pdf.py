from __future__ import annotations

from io import BytesIO
from typing import Iterable

from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from app.modules.ai.schemas import ExecutiveSummaryResponse
from app.core.settings import settings


def render_executive_summary_pdf(summary: ExecutiveSummaryResponse) -> bytes:
    buffer = BytesIO()
    page_width, page_height = LETTER
    margin = 0.75 * inch
    max_width = page_width - (margin * 2)
    header_height = 0.65 * inch
    footer_height = 0.45 * inch

    pdf = canvas.Canvas(buffer, pagesize=LETTER)
    page_num = 1
    y = page_height - margin - header_height

    def draw_header() -> None:
        pdf.setFillColor(colors.HexColor("#E8B373"))
        pdf.setFont("Helvetica-Bold", 16)
        logo_drawn = False
        if settings.AI_REPORT_LOGO_PATH:
            try:
                logo = ImageReader(settings.AI_REPORT_LOGO_PATH)
                logo_height = 28
                logo_width = 90
                pdf.drawImage(
                    logo,
                    margin,
                    page_height - margin + 2,
                    width=logo_width,
                    height=logo_height,
                    mask="auto",
                )
                pdf.drawString(margin + logo_width + 12, page_height - margin + 10, "IRMMF Command Center")
                logo_drawn = True
            except Exception:
                logo_drawn = False
        if not logo_drawn:
            pdf.drawString(margin, page_height - margin + 8, "IRMMF Command Center")
        pdf.setFillColor(colors.HexColor("#3B4654"))
        pdf.setFont("Helvetica", 9)
        pdf.drawString(margin, page_height - margin - 8, "Executive Summary Report")
        pdf.setStrokeColor(colors.HexColor("#D6DEE6"))
        pdf.setLineWidth(1)
        pdf.line(margin, page_height - margin - 14, page_width - margin, page_height - margin - 14)
        pdf.setFillColor(colors.black)

    def draw_footer() -> None:
        pdf.setStrokeColor(colors.HexColor("#D6DEE6"))
        pdf.setLineWidth(1)
        pdf.line(margin, margin - 8, page_width - margin, margin - 8)
        pdf.setFont("Helvetica", 9)
        pdf.setFillColor(colors.HexColor("#6B7280"))
        pdf.drawString(margin, margin - 22, f"Generated: {summary.generated_at or 'Unknown'}")
        pdf.drawRightString(page_width - margin, margin - 22, f"Page {page_num}")
        pdf.setFillColor(colors.black)

    def new_page() -> float:
        nonlocal page_num
        draw_footer()
        pdf.showPage()
        page_num += 1
        draw_header()
        return page_height - margin - header_height

    def draw_lines(lines: Iterable[str], font: str, size: int, leading: int, x: float = margin) -> None:
        nonlocal y
        pdf.setFont(font, size)
        for line in lines:
            if y - leading < margin + footer_height:
                y = new_page()
                pdf.setFont(font, size)
            pdf.drawString(x, y, line)
            y -= leading

    def wrap_text(text: str, font: str, size: int) -> list[str]:
        words = text.split()
        if not words:
            return [""]
        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if stringWidth(candidate, font, size) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def draw_heading(text: str) -> None:
        draw_lines([text], "Helvetica-Bold", 14, 18)

    def draw_subheading(text: str) -> None:
        draw_lines([text], "Helvetica-Bold", 12, 16)

    def draw_paragraph(text: str) -> None:
        draw_lines(wrap_text(text, "Helvetica", 11), "Helvetica", 11, 14)

    def draw_list(items: Iterable[str]) -> None:
        for item in items:
            lines = wrap_text(f"- {item}", "Helvetica", 11)
            draw_lines(lines, "Helvetica", 11, 14, x=margin + 6)

    draw_header()
    draw_heading("Executive Summary")
    draw_paragraph(summary.summary_text or "Summary unavailable.")

    if summary.maturity_band or summary.average_score is not None or summary.maturity_level is not None:
        meta_parts = []
        if summary.maturity_band:
            meta_parts.append(f"Maturity: {summary.maturity_band}")
        if summary.average_score is not None:
            meta_parts.append(f"Avg Score: {summary.average_score}/100")
        if summary.maturity_level is not None:
            label = summary.maturity_label or ""
            meta_parts.append(f"Level {summary.maturity_level}{f' ({label})' if label else ''}")
        draw_paragraph(" · ".join(meta_parts))

    draw_subheading("Key Findings")
    findings = summary.key_findings or []
    if findings:
        draw_list(findings)
    else:
        draw_paragraph("No findings generated yet.")

    draw_subheading("High-Level Recommendations")
    recommendations = summary.high_level_recommendations or []
    if recommendations:
        draw_list(recommendations)
    else:
        draw_paragraph("No recommendations generated yet.")

    draw_footer()
    pdf.save()
    return buffer.getvalue()
