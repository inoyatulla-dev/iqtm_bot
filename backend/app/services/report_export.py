"""Hisobotni PDF/DOCX formatida tayyorlash — faqat jadval va matn (ikonkasiz)."""
import io

from app.services.report_service import ReportData

_SUMMARY_LABELS = [
    ("Jami vazifalar (joriy)", "total"),
    ("Davrda yaratilgan", "created_in_period"),
    ("Davrda bajarilgan", "done_in_period"),
    ("Kechikkan", "overdue"),
]

# Rang palitrasi
_NAVY = "#1e3a5f"
_ACCENT = "#2563eb"
_ROW_ALT = "#eef2f7"
_GRID = "#cbd5e1"


def _summary_rows(data: ReportData) -> list[tuple[str, int]]:
    return [(label, getattr(data, attr)) for label, attr in _SUMMARY_LABELS]


def build_pdf(data: ReportData) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Image as RLImage,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "SectionTitle", parent=styles["Heading2"],
        textColor=colors.HexColor(_NAVY), spaceBefore=14, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "ProjectTitle", parent=styles["Heading3"],
        textColor=colors.HexColor(_ACCENT), spaceBefore=10, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        "Cell", parent=styles["Normal"], fontSize=8.5, leading=11,
    ))
    cell = lambda text: Paragraph(str(text), styles["Cell"])

    header_style = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(_GRID)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(_NAVY)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(_ROW_ALT)]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])
    info_style = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(_GRID)),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor(_ROW_ALT)),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])

    elements = []
    if data.logo_path.exists():
        elements.append(RLImage(str(data.logo_path), width=120, height=80))
        elements.append(Spacer(1, 8))

    elements.append(Paragraph(f"{data.period_label} hisobot", styles["Title"]))
    elements.append(Paragraph(f"Davr: {data.start} — {data.end}", styles["Normal"]))
    elements.append(Paragraph(
        f"Yaratildi: {data.generated_at.strftime('%Y-%m-%d %H:%M')}", styles["Normal"]
    ))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Umumiy ko'rsatkichlar", styles["SectionTitle"]))
    elements.append(Table(
        [["Ko'rsatkich", "Qiymat"]] + [[label, str(value)] for label, value in _summary_rows(data)],
        style=header_style, colWidths=[120 * mm, 54 * mm],
    ))

    if data.statuses:
        elements.append(Paragraph("Holatlar bo'yicha", styles["SectionTitle"]))
        rows = [["Holat", "Soni"]] + [[s.name, str(s.count)] for s in data.statuses]
        elements.append(Table(rows, style=header_style, colWidths=[120 * mm, 54 * mm]))

    if data.departments:
        elements.append(Paragraph("Bo'limlar bo'yicha", styles["SectionTitle"]))
        rows = [["Bo'lim", "Jami", "Bajarilgan", "Foiz"]] + [
            [d.name, str(d.total), str(d.done), f"{d.percent}%"] for d in data.departments
        ]
        elements.append(Table(rows, style=header_style, colWidths=[84 * mm, 30 * mm, 30 * mm, 30 * mm]))

    if data.projects:
        elements.append(Paragraph("Loyihalar", styles["SectionTitle"]))
        for proj in data.projects:
            elements.append(Paragraph(proj.name, styles["ProjectTitle"]))
            info_rows = [
                ["Holat", proj.status_label],
                ["Muddat", proj.deadline_label],
                ["Bajarilgan vazifalar", f"{proj.done}/{proj.total} ({proj.percent}%)"],
                ["Joriy jarayon", proj.schedule_label],
            ]
            elements.append(Table(info_rows, style=info_style, colWidths=[50 * mm, 124 * mm]))
            elements.append(Spacer(1, 4))

            if proj.tasks:
                rows = [["#", "Vazifa", "Mas'ul", "Muddat", "Holat"]] + [
                    [str(t.seq), cell(t.name), cell(t.assignee), t.deadline, t.status_label]
                    for t in proj.tasks
                ]
                elements.append(Table(
                    rows, style=header_style,
                    colWidths=[8 * mm, 70 * mm, 40 * mm, 28 * mm, 28 * mm],
                ))
            else:
                elements.append(Paragraph("Vazifalar mavjud emas", styles["Normal"]))
            elements.append(Spacer(1, 10))

    doc.build(elements)
    return buf.getvalue()


def build_docx(data: ReportData) -> bytes:
    from docx import Document
    from docx.shared import Inches, RGBColor

    navy = RGBColor(0x1E, 0x3A, 0x5F)
    accent = RGBColor(0x25, 0x63, 0xEB)

    doc = Document()
    if data.logo_path.exists():
        doc.add_picture(str(data.logo_path), width=Inches(2))

    doc.add_heading(f"{data.period_label} hisobot", level=0)
    doc.add_paragraph(f"Davr: {data.start} — {data.end}")
    doc.add_paragraph(f"Yaratildi: {data.generated_at.strftime('%Y-%m-%d %H:%M')}")

    def section_title(text: str, color: RGBColor = navy):
        h = doc.add_heading(text, level=2)
        for run in h.runs:
            run.font.color.rgb = color

    def fill_table(headers: list[str], rows: list[list[str]], widths: list[float] | None = None):
        table = doc.add_table(rows=1, cols=len(headers))
        table.style = "Light Grid Accent 1"
        hdr = table.rows[0].cells
        for i, h in enumerate(headers):
            hdr[i].text = h
            for run in hdr[i].paragraphs[0].runs:
                run.font.bold = True
        for row in rows:
            cells = table.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = str(v)
        if widths:
            for row in table.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Inches(w)
        return table

    section_title("Umumiy ko'rsatkichlar")
    fill_table(
        ["Ko'rsatkich", "Qiymat"],
        [[label, str(value)] for label, value in _summary_rows(data)],
        widths=[4.2, 1.8],
    )

    if data.statuses:
        section_title("Holatlar bo'yicha")
        fill_table(
            ["Holat", "Soni"],
            [[s.name, str(s.count)] for s in data.statuses],
            widths=[4.2, 1.8],
        )

    if data.departments:
        section_title("Bo'limlar bo'yicha")
        fill_table(
            ["Bo'lim", "Jami", "Bajarilgan", "Foiz"],
            [[d.name, str(d.total), str(d.done), f"{d.percent}%"] for d in data.departments],
            widths=[3, 1, 1, 1],
        )

    if data.projects:
        section_title("Loyihalar")
        for proj in data.projects:
            h = doc.add_heading(proj.name, level=3)
            for run in h.runs:
                run.font.color.rgb = accent

            fill_table(
                ["", ""],
                [
                    ["Holat", proj.status_label],
                    ["Muddat", proj.deadline_label],
                    ["Bajarilgan vazifalar", f"{proj.done}/{proj.total} ({proj.percent}%)"],
                    ["Joriy jarayon", proj.schedule_label],
                ],
                widths=[2, 4],
            )
            doc.add_paragraph()

            if proj.tasks:
                fill_table(
                    ["#", "Vazifa", "Mas'ul", "Muddat", "Holat"],
                    [[t.seq, t.name, t.assignee, t.deadline, t.status_label] for t in proj.tasks],
                    widths=[0.4, 2.6, 1.6, 1.2, 1.2],
                )
            else:
                doc.add_paragraph("Vazifalar mavjud emas")
            doc.add_paragraph()

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
