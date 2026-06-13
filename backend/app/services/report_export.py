"""Hisobotni PDF/DOCX formatida tayyorlash."""
import io

from app.services.report_service import ReportData, rating_chart, status_chart

_SUMMARY_LABELS = [
    ("Jami vazifalar (joriy)", "total"),
    ("Davrda yaratilgan", "created_in_period"),
    ("Davrda bajarilgan", "done_in_period"),
    ("Kechikkan", "overdue"),
]


def _summary_rows(data: ReportData) -> list[tuple[str, int]]:
    return [(label, getattr(data, attr)) for label, attr in _SUMMARY_LABELS]


def build_pdf(data: ReportData) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
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
    table_style = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
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

    elements.append(Paragraph("Umumiy ko'rsatkichlar", styles["Heading2"]))
    elements.append(Table(
        [["Ko'rsatkich", "Qiymat"]] + [[label, str(value)] for label, value in _summary_rows(data)],
        style=table_style, colWidths=[100 * mm, 40 * mm],
    ))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Holatlar bo'yicha", styles["Heading2"]))
    elements.append(RLImage(io.BytesIO(status_chart(data.statuses)), width=160 * mm, height=88 * mm))
    elements.append(Spacer(1, 12))

    if data.departments:
        elements.append(Paragraph("Bo'limlar bo'yicha", styles["Heading2"]))
        rows = [["Bo'lim", "Jami", "Bajarilgan"]] + [
            [f"{d.emoji} {d.name}", str(d.total), str(d.done)] for d in data.departments
        ]
        elements.append(Table(rows, style=table_style, colWidths=[100 * mm, 20 * mm, 20 * mm]))
        elements.append(Spacer(1, 12))

    if data.rating:
        elements.append(Paragraph("Xodimlar reytingi", styles["Heading2"]))
        elements.append(RLImage(io.BytesIO(rating_chart(data.rating)), width=160 * mm, height=88 * mm))
        elements.append(Spacer(1, 8))
        rows = [["Xodim", "Bajarilgan", "Faol", "Kechikkan", "Davrda bajarilgan"]] + [
            [r.name, str(r.done), str(r.active), str(r.overdue), str(r.done_period)]
            for r in data.rating
        ]
        elements.append(Table(rows, style=table_style, colWidths=[70 * mm, 22 * mm, 18 * mm, 22 * mm, 28 * mm]))

    if data.projects:
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("Loyihalar", styles["Heading2"]))
        for proj in data.projects:
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(
                f"<b>{proj.name}</b> — {proj.status_label}, {proj.done}/{proj.total} ({proj.percent}%)",
                styles["Normal"],
            ))
            for label, tasks in (
                ("Bajarilgan", proj.done_tasks),
                ("Jarayonda", proj.in_progress_tasks),
                ("Rejalashtirilgan", proj.planned_tasks),
            ):
                if not tasks:
                    continue
                elements.append(Paragraph(label, styles["Heading4"]))
                rows = [["Vazifa", "Mas'ul", "Holat"]] + [
                    [t.name, t.assignee, t.status_label] for t in tasks
                ]
                elements.append(Table(rows, style=table_style, colWidths=[80 * mm, 40 * mm, 40 * mm]))
                elements.append(Spacer(1, 4))

    doc.build(elements)
    return buf.getvalue()


def build_docx(data: ReportData) -> bytes:
    from docx import Document
    from docx.shared import Inches

    doc = Document()
    if data.logo_path.exists():
        doc.add_picture(str(data.logo_path), width=Inches(2))

    doc.add_heading(f"{data.period_label} hisobot", level=0)
    doc.add_paragraph(f"Davr: {data.start} — {data.end}")
    doc.add_paragraph(f"Yaratildi: {data.generated_at.strftime('%Y-%m-%d %H:%M')}")

    doc.add_heading("Umumiy ko'rsatkichlar", level=2)
    table = doc.add_table(rows=1, cols=2)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text = "Ko'rsatkich", "Qiymat"
    for label, value in _summary_rows(data):
        row = table.add_row().cells
        row[0].text, row[1].text = label, str(value)

    doc.add_heading("Holatlar bo'yicha", level=2)
    doc.add_picture(io.BytesIO(status_chart(data.statuses)), width=Inches(6))

    if data.departments:
        doc.add_heading("Bo'limlar bo'yicha", level=2)
        table = doc.add_table(rows=1, cols=3)
        table.style = "Light Grid Accent 1"
        hdr = table.rows[0].cells
        hdr[0].text, hdr[1].text, hdr[2].text = "Bo'lim", "Jami", "Bajarilgan"
        for d in data.departments:
            row = table.add_row().cells
            row[0].text, row[1].text, row[2].text = f"{d.emoji} {d.name}", str(d.total), str(d.done)

    if data.rating:
        doc.add_heading("Xodimlar reytingi", level=2)
        doc.add_picture(io.BytesIO(rating_chart(data.rating)), width=Inches(6))
        table = doc.add_table(rows=1, cols=5)
        table.style = "Light Grid Accent 1"
        hdr = table.rows[0].cells
        for i, h in enumerate(["Xodim", "Bajarilgan", "Faol", "Kechikkan", "Davrda bajarilgan"]):
            hdr[i].text = h
        for r in data.rating:
            row = table.add_row().cells
            for i, v in enumerate([r.name, str(r.done), str(r.active), str(r.overdue), str(r.done_period)]):
                row[i].text = v

    if data.projects:
        doc.add_heading("Loyihalar", level=2)
        for proj in data.projects:
            doc.add_heading(
                f"{proj.name} — {proj.status_label}, {proj.done}/{proj.total} ({proj.percent}%)",
                level=3,
            )
            for label, tasks in (
                ("Bajarilgan", proj.done_tasks),
                ("Jarayonda", proj.in_progress_tasks),
                ("Rejalashtirilgan", proj.planned_tasks),
            ):
                if not tasks:
                    continue
                p = doc.add_paragraph()
                p.add_run(label).bold = True
                table = doc.add_table(rows=1, cols=3)
                table.style = "Light Grid Accent 1"
                hdr = table.rows[0].cells
                hdr[0].text, hdr[1].text, hdr[2].text = "Vazifa", "Mas'ul", "Holat"
                for t in tasks:
                    row = table.add_row().cells
                    row[0].text, row[1].text, row[2].text = t.name, t.assignee, t.status_label

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


