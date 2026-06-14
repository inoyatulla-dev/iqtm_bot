"""Hisobotni PDF/DOCX formatida tayyorlash. PDF — HTML shabloni (HISOBOT_TEMPLATE.md) asosida."""
import base64
import io
from html import escape

from app.services.report_service import ProjectTaskRow, ReportData, StatusCount

_SUMMARY_LABELS = [
    ("Jami vazifalar (joriy)", "total"),
    ("Davrda yaratilgan", "created_in_period"),
    ("Davrda bajarilgan", "done_in_period"),
    ("Kechikkan", "overdue"),
]

# Tashkilot nomi (sahifa tepasidagi takrorlanuvchi header uchun standart qiymat)
ORG_FULL_NAME = "Innovatsiyalarni qo'llab-quvvatlash va tijoratlashtirish markazi"

# Ba'zi qurilmalarda o'zbekcha tutuq belgisi (masalan U+02BB) standart shriftlarda
# ko'rsatilmasligi mumkin (▀ bo'lib chiqadi) — bularni oddiy apostrofga almashtiramiz.
_APOSTROPHE_VARIANTS = "ʻʼ‘’´`′"


def _clean(value) -> str:
    text = "" if value is None else str(value)
    for ch in _APOSTROPHE_VARIANTS:
        text = text.replace(ch, "'")
    return text


def _summary_rows(data: ReportData) -> list[tuple[str, int]]:
    return [(label, getattr(data, attr)) for label, attr in _SUMMARY_LABELS]


# ── HTML hisobot (HISOBOT_TEMPLATE.md) ──────────────────────────────────────

_KPI_COLORS = {
    "total": "var(--brand-dark)",
    "created_in_period": "#2563EB",
    "done_in_period": "#16A34A",
    "overdue": "#DC2626",
}

_HTML_CSS = """
:root {
  --brand: #0E7C5A;
  --brand-dark: #0A5B42;
  --brand-tint: #E7F4EF;
  --ink: #111827;
  --muted: #6B7280;
  --line: #E6E8EB;
}
* { box-sizing: border-box; }
body {
  font-family: 'Inter', -apple-system, "Segoe UI", Roboto, sans-serif;
  color: var(--ink);
  background: #f1f5f9;
  margin: 0;
  padding: 24px;
}
.sheet {
  max-width: 900px;
  margin: 0 auto;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,.06);
}
.header {
  background: linear-gradient(135deg, var(--brand-dark), var(--brand));
  color: #fff;
  padding: 24px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.header__brand { display: flex; align-items: center; gap: 14px; }
.header__logo { width: 48px; height: 48px; border-radius: 10px; background: #fff; object-fit: contain; padding: 4px; }
.header__title { font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 800; font-size: 20px; }
.header__sub { font-size: 12px; opacity: .85; margin-top: 2px; }
.header__meta { text-align: right; font-size: 12px; opacity: .9; line-height: 1.6; }
.header__meta b { font-weight: 700; }
.pad { padding: 24px 28px; }
h2.section {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 13px; font-weight: 800; color: var(--brand-dark);
  text-transform: uppercase; letter-spacing: .5px;
  margin: 26px 0 12px; padding-bottom: 6px;
  border-bottom: 2px solid var(--brand-tint);
}
h2.section:first-child { margin-top: 0; }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.kpi { border: 1px solid var(--line); border-radius: 10px; padding: 14px; text-align: center; }
.kpi .value { font-size: 24px; font-weight: 800; font-family: 'Plus Jakarta Sans', sans-serif; }
.kpi .label { font-size: 11px; color: var(--muted); margin-top: 4px; }
.status-wrap { display: flex; align-items: center; gap: 28px; flex-wrap: wrap; }
.donut { width: 140px; height: 140px; border-radius: 50%; flex-shrink: 0; position: relative; }
.donut::after { content: ""; position: absolute; inset: 26px; background: #fff; border-radius: 50%; }
.donut-legend { display: flex; flex-direction: column; gap: 8px; font-size: 13px; }
.legend-dot, .dot { width: 10px; height: 10px; border-radius: 3px; display: inline-block; margin-right: 6px; flex-shrink: 0; }
.dept { margin-bottom: 12px; }
.dept-head { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px; gap: 8px; }
.dept-name { font-weight: 700; display: flex; align-items: center; }
.dept-count { color: var(--muted); white-space: nowrap; }
.dot { border-radius: 50%; }
.track, .ptrack { height: 8px; border-radius: 4px; background: var(--line); overflow: hidden; }
.fill, .pfill { height: 100%; border-radius: 4px; }
.project { border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; margin-bottom: 14px; }
.project.late { border-color: #FCA5A5; background: #FEF2F2; }
.proj-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
.proj-title { display: flex; align-items: center; gap: 10px; font-weight: 800; font-family: 'Plus Jakarta Sans', sans-serif; }
.pill { font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 999px; background: var(--brand-tint); color: var(--brand-dark); }
.pill.late { background: #FEE2E2; color: #DC2626; }
.proj-prog { display: flex; align-items: center; gap: 10px; min-width: 170px; }
.proj-prog .ptrack { flex: 1; }
.ptxt { font-size: 12px; color: var(--muted); white-space: nowrap; }
.proj-sub { font-size: 12px; color: var(--muted); margin-bottom: 10px; }
.proj-sub.late { color: #DC2626; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { text-align: left; background: var(--brand-tint); color: var(--brand-dark); padding: 6px 10px; font-weight: 700; }
td { padding: 6px 10px; border-bottom: 1px solid var(--line); }
tr:last-child td { border-bottom: none; }
.badge { display: inline-block; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px; }
.due.over { color: #DC2626; font-weight: 700; }
.empty { color: var(--muted); font-size: 13px; padding: 6px 0 14px; }
.footer { padding: 14px 28px; border-top: 1px solid var(--line); font-size: 11px; color: var(--muted); display: flex; justify-content: space-between; }
@media print {
  body { background: #fff; padding: 0; }
  .sheet { box-shadow: none; border-radius: 0; max-width: none; }
  .project, .kpis, .status-wrap { break-inside: avoid; }
  h2.section { break-after: avoid; }
  @page { size: A4; margin: 14mm; }
}
"""


def _esc(value) -> str:
    return escape(_clean(value), quote=False)


def _tint(hex_color: str, alpha: float = 0.15) -> str:
    hex_color = (hex_color or "").lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(ch * 2 for ch in hex_color)
    try:
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        r, g, b = 0x64, 0x74, 0x8b
    return f"rgba({r}, {g}, {b}, {alpha})"


def _conic_gradient(statuses: list[StatusCount], total: int) -> str:
    if total <= 0:
        return "var(--line)"
    parts = []
    current = 0.0
    for s in statuses:
        if s.count == 0:
            continue
        end = current + (s.count / total * 100)
        parts.append(f"{s.color} {current:.2f}% {end:.2f}%")
        current = end
    return f"conic-gradient({', '.join(parts)})"


def _progress_color(percent: int) -> str:
    if percent >= 100:
        return "#16A34A"
    if percent >= 50:
        return "#2563EB"
    if percent > 0:
        return "#D97706"
    return "var(--line)"


def _task_row(t: ProjectTaskRow) -> str:
    if t.overdue:
        bg, color = "rgba(220, 38, 38, 0.12)", "#DC2626"
    else:
        bg, color = _tint(t.status_color), t.status_color
    due_attr = ' class="due over"' if t.overdue else ""
    return (
        f"<tr><td>{t.seq}</td><td>{_esc(t.name)}</td><td>{_esc(t.assignee)}</td>"
        f"<td{due_attr}>{_esc(t.deadline)}</td>"
        f'<td><span class="badge" style="background:{bg};color:{color}">{_esc(t.status_label)}</span></td></tr>'
    )


def build_html(data: ReportData) -> str:
    """HISOBOT_TEMPLATE.md ko'rinishidagi to'liq hisobot — A4 chop etishga tayyor HTML."""
    org_name = _clean(data.org_name) or ORG_FULL_NAME

    logo_html = ""
    if data.logo_path.exists():
        logo_b64 = base64.b64encode(data.logo_path.read_bytes()).decode("ascii")
        logo_html = f'<img class="header__logo" src="data:image/png;base64,{logo_b64}" alt="logo">'

    kpi_html = "".join(
        f'<div class="kpi"><div class="value" style="color:{_KPI_COLORS[attr]}">{getattr(data, attr)}</div>'
        f'<div class="label">{_esc(label)}</div></div>'
        for label, attr in _SUMMARY_LABELS
    )

    total_status = sum(s.count for s in data.statuses)
    gradient = _conic_gradient(data.statuses, total_status)
    legend_html = "".join(
        f'<span><span class="legend-dot" style="background:{s.color}"></span>'
        f"{_esc(s.name)} — {round(s.count * 100 / total_status) if total_status else 0}% ({s.count})</span>"
        for s in data.statuses
    ) or '<div class="empty">Holatlar mavjud emas</div>'

    depts_sorted = sorted(data.departments, key=lambda d: d.percent, reverse=True)
    depts_html = "".join(
        f'<div class="dept"><div class="dept-head">'
        f'<div class="dept-name"><span class="dot" style="background:{d.color}"></span>{_esc(d.name)}</div>'
        f'<div class="dept-count">{d.done} / {d.total} · {d.percent}%</div></div>'
        f'<div class="track"><div class="fill" style="width:{max(d.percent, 3) if d.total else 0}%;background:{d.color}"></div></div>'
        f"</div>"
        for d in depts_sorted
    ) or '<div class="empty">Bo\'limlar mavjud emas</div>'

    projects_html = ""
    for proj in data.projects:
        late = proj.schedule_label.startswith("Orqada qolmoqda") or proj.schedule_label.startswith("Muddat o'tgan")
        pill_label = "Orqada qolmoqda" if late else proj.status_label
        width = f"{max(proj.percent, 3)}%" if proj.total else "0%"
        rows = "".join(_task_row(t) for t in proj.tasks) or (
            '<tr><td colspan="5" class="empty">Vazifalar mavjud emas</td></tr>'
        )
        projects_html += (
            f'<div class="project{" late" if late else ""}">'
            f'<div class="proj-head">'
            f'<div class="proj-title"><span>{_esc(proj.name)}</span>'
            f'<span class="pill{" late" if late else ""}">{_esc(pill_label)}</span></div>'
            f'<div class="proj-prog"><div class="ptrack"><div class="pfill" '
            f'style="width:{width};background:{_progress_color(proj.percent)}"></div></div>'
            f'<div class="ptxt"><b>{proj.done}/{proj.total}</b> · {proj.percent}%</div></div>'
            f"</div>"
            f'<div class="proj-sub{" late" if late else ""}">Muddat: {_esc(proj.deadline_label)} · {_esc(proj.schedule_label)}</div>'
            f"<table><tr><th>#</th><th>Vazifa</th><th>Mas'ul</th><th>Muddat</th><th>Holat</th></tr>{rows}</table>"
            f"</div>"
        )
    projects_html = projects_html or '<div class="empty">Loyihalar mavjud emas</div>'

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(data.period_title)} hisobot</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@700;800&display=swap" rel="stylesheet">
<style>{_HTML_CSS}</style>
</head>
<body>
<div class="sheet">
  <div class="header">
    <div class="header__brand">
      {logo_html}
      <div>
        <div class="header__title">{_esc(org_name)}</div>
        <div class="header__sub">{_esc(data.period_title)} hisobot</div>
      </div>
    </div>
    <div class="header__meta">
      Davr: <b>{data.start.strftime('%d.%m.%Y')} — {data.end.strftime('%d.%m.%Y')}</b><br>
      Yaratildi: <b>{data.generated_at.strftime('%d.%m.%Y %H:%M')}</b>
    </div>
  </div>
  <div class="pad">
    <h2 class="section">Umumiy ko'rsatkichlar</h2>
    <div class="kpis">{kpi_html}</div>

    <h2 class="section">Holatlar bo'yicha taqsimot</h2>
    <div class="status-wrap">
      <div class="donut" style="background:{gradient}"></div>
      <div class="donut-legend">{legend_html}</div>
    </div>

    <h2 class="section">Bo'limlar bo'yicha progress</h2>
    <div class="depts">{depts_html}</div>

    <h2 class="section">Loyihalar</h2>
    <div class="loyihalar">{projects_html}</div>
  </div>
  <div class="footer">
    <span>{_esc(org_name)}</span>
    <span>{data.generated_at.strftime('%d.%m.%Y %H:%M')}</span>
  </div>
</div>
</body>
</html>"""


def build_pdf(data: ReportData) -> bytes:
    """HTML hisobotni (HISOBOT_TEMPLATE.md dizayni) PDF'ga aylantiradi."""
    from weasyprint import HTML

    return HTML(string=build_html(data)).write_pdf()


def build_docx(data: ReportData) -> bytes:
    from docx import Document
    from docx.enum.table import WD_ALIGN_VERTICAL
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    navy = RGBColor(0x1E, 0x3A, 0x5F)
    accent = RGBColor(0x25, 0x63, 0xEB)
    org_name = _clean(data.org_name) or ORG_FULL_NAME

    doc = Document()

    # ── Har bir sahifada takrorlanuvchi header: logotip + tashkilot nomi + chiziq ──
    header = doc.sections[0].header
    header_table = header.add_table(rows=1, cols=2, width=Inches(6.5))
    header_table.autofit = False
    header_table.allow_autofit = False
    header_table.columns[0].width = Inches(0.9)
    header_table.columns[1].width = Inches(5.6)
    logo_cell, org_cell = header_table.rows[0].cells
    logo_cell.width = Inches(0.9)
    org_cell.width = Inches(5.6)
    logo_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    org_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    if data.logo_path.exists():
        logo_cell.paragraphs[0].add_run().add_picture(str(data.logo_path), width=Inches(0.7))
    run = org_cell.paragraphs[0].add_run(org_name)
    run.bold = True
    run.font.size = Pt(12)
    run.font.color.rgb = navy

    line_p = header.add_paragraph()
    line_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pPr = line_p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "1E3A5F")
    pBdr.append(bottom)
    pPr.append(pBdr)

    doc.add_heading(f"{data.period_title} hisobot", level=0)
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
                cells[i].text = _clean(v)
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
            h = doc.add_heading(_clean(proj.name), level=3)
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
