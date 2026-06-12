"""Hisobotni PDF/DOCX/XLSX formatida tayyorlash."""
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

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def build_xlsx(data: ReportData) -> bytes:
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, Reference
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.styles import Font

    wb = Workbook()
    ws = wb.active
    ws.title = "Hisobot"

    ws["A1"] = f"{data.period_label} hisobot"
    ws["A1"].font = Font(size=14, bold=True)
    ws["A2"] = f"Davr: {data.start} — {data.end}"
    ws["A3"] = f"Yaratildi: {data.generated_at.strftime('%Y-%m-%d %H:%M')}"

    if data.logo_path.exists():
        img = XLImage(str(data.logo_path))
        img.width, img.height = 150, 100
        ws.add_image(img, "E1")

    row = 5
    ws.cell(row=row, column=1, value="Ko'rsatkich").font = Font(bold=True)
    ws.cell(row=row, column=2, value="Qiymat").font = Font(bold=True)
    for label, value in _summary_rows(data):
        row += 1
        ws.cell(row=row, column=1, value=label)
        ws.cell(row=row, column=2, value=value)

    # ── Holatlar jadvali + diagramma ──
    status_header_row = row + 2
    ws.cell(row=status_header_row, column=1, value="Holat").font = Font(bold=True)
    ws.cell(row=status_header_row, column=2, value="Soni").font = Font(bold=True)
    for i, s in enumerate(data.statuses, start=1):
        ws.cell(row=status_header_row + i, column=1, value=f"{s.emoji} {s.name}")
        ws.cell(row=status_header_row + i, column=2, value=s.count)

    if data.statuses:
        chart = BarChart()
        chart.title = "Vazifalar holati bo'yicha"
        last_row = status_header_row + len(data.statuses)
        chart.add_data(
            Reference(ws, min_col=2, min_row=status_header_row, max_row=last_row),
            titles_from_data=True,
        )
        chart.set_categories(
            Reference(ws, min_col=1, min_row=status_header_row + 1, max_row=last_row)
        )
        ws.add_chart(chart, f"D{status_header_row}")
        row = last_row
    else:
        row = status_header_row

    # ── Bo'limlar jadvali ──
    if data.departments:
        row += 2
        ws.cell(row=row, column=1, value="Bo'lim").font = Font(bold=True)
        ws.cell(row=row, column=2, value="Jami").font = Font(bold=True)
        ws.cell(row=row, column=3, value="Bajarilgan").font = Font(bold=True)
        for d in data.departments:
            row += 1
            ws.cell(row=row, column=1, value=f"{d.emoji} {d.name}")
            ws.cell(row=row, column=2, value=d.total)
            ws.cell(row=row, column=3, value=d.done)

    # ── Xodimlar reytingi ──
    if data.rating:
        row += 2
        rating_header_row = row
        headers = ["Xodim", "Bajarilgan", "Faol", "Kechikkan", "Davrda bajarilgan"]
        for col, h in enumerate(headers, start=1):
            ws.cell(row=row, column=col, value=h).font = Font(bold=True)
        for r in data.rating:
            row += 1
            ws.cell(row=row, column=1, value=r.name)
            ws.cell(row=row, column=2, value=r.done)
            ws.cell(row=row, column=3, value=r.active)
            ws.cell(row=row, column=4, value=r.overdue)
            ws.cell(row=row, column=5, value=r.done_period)

        rating_chart_obj = BarChart()
        rating_chart_obj.title = "Davrda bajarilgan vazifalar — xodimlar"
        last_row = row
        rating_chart_obj.add_data(
            Reference(ws, min_col=5, min_row=rating_header_row, max_row=last_row),
            titles_from_data=True,
        )
        rating_chart_obj.set_categories(
            Reference(ws, min_col=1, min_row=rating_header_row + 1, max_row=last_row)
        )
        ws.add_chart(rating_chart_obj, f"G{rating_header_row}")

    for col, width in {"A": 32, "B": 14, "C": 14, "D": 14, "E": 18}.items():
        ws.column_dimensions[col].width = width

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
