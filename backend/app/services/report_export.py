"""Hisobotni PDF/DOCX formatida tayyorlash. PDF — hisobot.html dizayni asosida."""
import base64
import io
import math
from html import escape

from app.services.report_service import ProjectTaskRow, ReportData, StatusCount

_SUMMARY_LABELS = [
    ("Jami vazifalar", "total"),
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


# ── HTML hisobot (hisobot.html dizayni) ─────────────────────────────────────

_HTML_CSS = """
:root {
  --brand: #0E7C5A;
  --brand-dark: #0A5B42;
  --brand-tint: #E7F4EF;
  --ink: #111827;
  --muted: #6B7280;
  --line: #E6E8EB;
  --surface: #FFFFFF;
  --late: #DC2626;
  --late-bg: #FEE2E2;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', -apple-system, "Segoe UI", Roboto, sans-serif;
  color: var(--ink);
  background: #fff;
}
.sheet { width: 100%; background: var(--surface); }
.pad { padding: 24px 28px; }

h2.section {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 13px; font-weight: 700; letter-spacing: .06em;
  text-transform: uppercase; color: var(--brand-dark);
  display: flex; align-items: center; gap: 10px;
  margin: 26px 0 14px;
}
h2.section::before { content: ""; width: 5px; height: 16px; border-radius: 3px; background: var(--brand); }
h2.section:first-child { margin-top: 0; }

/* ---------- HEADER ---------- */
.header {
  background: linear-gradient(135deg, var(--brand-dark), var(--brand));
  color: #fff; padding: 24px 28px;
  display: flex; justify-content: space-between; align-items: flex-start; gap: 20px;
}
.header__brand { display: flex; align-items: center; gap: 12px; }
.header__logo {
  width: 44px; height: 44px; border-radius: 10px; background: #fff;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 800; color: var(--brand);
  font-size: 13px; letter-spacing: -.02em; object-fit: contain;
}
.header__name { font-size: 12px; font-weight: 600; opacity: .92; max-width: 280px; line-height: 1.3; }
.header__doctype {
  font-family: 'Plus Jakarta Sans', sans-serif; font-size: 10px; font-weight: 700; letter-spacing: .14em;
  text-transform: uppercase; opacity: .8; margin-top: 16px; display: block;
}
.header__h1 { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 26px; font-weight: 800; letter-spacing: -.02em; margin-top: 2px; }
.header__meta { text-align: right; font-size: 12px; opacity: .9; white-space: nowrap; }
.header__meta .period { font-weight: 700; font-size: 14px; opacity: 1; }
.header__meta .gen { margin-top: 6px; opacity: .8; }

/* ---------- KPI CARDS ---------- */
.kpis { display: flex; gap: 12px; }
.kpi {
  flex: 1; border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; background: #fff;
  position: relative; overflow: hidden;
}
.kpi::after { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--brand); }
.kpi.accent-red::after { background: var(--late); }
.kpi .label { font-size: 10px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
.kpi .value { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 24px; font-weight: 800; line-height: 1.1; margin-top: 6px; }
.kpi .sub { font-size: 11px; color: var(--muted); margin-top: 2px; }
.kpi.accent-red .value { color: var(--late); }

/* ---------- STATUS: donut + legend ---------- */
.status-wrap {
  display: flex; gap: 28px; align-items: center;
  border: 1px solid var(--line); border-radius: 10px; padding: 18px 22px; background: #fff;
}
.legend { display: flex; flex-wrap: wrap; gap: 10px 24px; flex: 1; }
.leg { display: flex; align-items: center; gap: 8px; font-size: 12px; width: 46%; }
.leg .dot { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; margin-right: 8px; }
.leg .ln { flex: 1; color: var(--ink); font-weight: 500; }
.leg .cnt { font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; margin-left: 8px; }
.leg.zero { opacity: .45; }

/* ---------- DEPARTMENTS: progress bars ---------- */
.dept { display: flex; align-items: center; gap: 14px; padding: 9px 0; border-bottom: 1px solid var(--line); }
.dept:last-child { border-bottom: none; }
.dept .nm { width: 120px; font-weight: 600; font-size: 12px; flex-shrink: 0; }
.dept .track { flex: 1; height: 8px; border-radius: 6px; background: #EFF2F4; overflow: hidden; }
.dept .fill { height: 100%; border-radius: 6px; }
.dept .pct { width: 84px; text-align: right; font-size: 11px; color: var(--muted); flex-shrink: 0; }
.dept .pct b { font-family: 'Plus Jakarta Sans', sans-serif; color: var(--ink); font-size: 12px; }

/* ---------- PROJECTS ---------- */
.project { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; margin-bottom: 14px; background: #fff; }
.project.late { border-color: #F5C2C2; }
.proj-head {
  padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; gap: 14px;
  background: linear-gradient(180deg, #FAFBFC, #fff); border-bottom: 1px solid var(--line); flex-wrap: wrap;
}
.project.late .proj-head { background: linear-gradient(180deg, #FEF4F4, #fff); border-bottom-color: #F5C2C2; }
.proj-title { display: flex; align-items: center; gap: 10px; flex: 1 1 auto; min-width: 0; }
.proj-title .pn { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 14px; font-weight: 700; margin-right: 10px; }
.pill {
  font-size: 10px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase;
  padding: 3px 9px; border-radius: 20px; background: var(--brand-tint); color: var(--brand-dark);
  white-space: nowrap;
}
.pill.late { background: var(--late-bg); color: var(--late); }
.proj-prog { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.proj-prog .ptrack { width: 110px; height: 7px; border-radius: 6px; background: #EFF2F4; overflow: hidden; }
.proj-prog .pfill { height: 100%; }
.proj-prog .ptxt { font-size: 12px; color: var(--muted); white-space: nowrap; margin-left: 10px; }
.proj-prog .ptxt b { font-family: 'Plus Jakarta Sans', sans-serif; color: var(--ink); }
.proj-sub {
  padding: 8px 16px; font-size: 12px; color: var(--muted); border-bottom: 1px solid var(--line);
  display: flex; gap: 20px; flex-wrap: wrap;
}
.proj-sub > div { margin-right: 20px; }
.proj-sub > div:last-child { margin-right: 0; }
.proj-sub div b { color: var(--ink); font-weight: 600; }
.proj-sub .warn { color: var(--late); font-weight: 600; }

table { width: 100%; border-collapse: collapse; }
thead th {
  font-size: 10px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--muted);
  text-align: left; padding: 8px 16px; background: #F8FAFB; border-bottom: 1px solid var(--line);
}
tbody td { padding: 9px 16px; font-size: 12px; border-bottom: 1px solid #F0F2F4; vertical-align: middle; }
tbody tr:last-child td { border-bottom: none; }
td.num { width: 28px; color: var(--muted); font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; text-align: center; }
td.who { white-space: nowrap; color: var(--ink); font-weight: 500; }
td.due { white-space: nowrap; color: var(--muted); font-variant-numeric: tabular-nums; }
td.due.over { color: var(--late); font-weight: 600; }

.badge { display: inline-flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 20px; white-space: nowrap; }
.badge::before { content: ""; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

.empty { color: var(--muted); font-size: 13px; padding: 6px 0 14px; }
.footer { padding: 16px 28px; border-top: 1px solid var(--line); display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); }

.project, .status-wrap, .kpis { break-inside: avoid; }
h2.section { break-after: avoid; }
@page { size: A4; margin: 14mm; }
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


def _donut_svg(statuses: list[StatusCount], total: int, size: int = 160) -> str:
    """Holatlar taqsimoti — to'ldirilgan pie + markazda umumiy son (CSS conic-gradient o'rniga SVG)."""
    cx = cy = size / 2
    r = size / 2
    hole_r = r * 0.65

    nonzero = [s for s in statuses if s.count > 0]
    if total <= 0:
        pie = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#EFF2F4"/>'
    elif len(nonzero) == 1:
        pie = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{nonzero[0].color}"/>'
    else:
        segments = []
        angle = -90.0
        for s in nonzero:
            sweep = s.count / total * 360
            start_rad, end_rad = math.radians(angle), math.radians(angle + sweep)
            x1, y1 = cx + r * math.cos(start_rad), cy + r * math.sin(start_rad)
            x2, y2 = cx + r * math.cos(end_rad), cy + r * math.sin(end_rad)
            large = 1 if sweep > 180 else 0
            segments.append(
                f'<path d="M{cx},{cy} L{x1:.3f},{y1:.3f} A{r},{r} 0 {large} 1 {x2:.3f},{y2:.3f} Z" fill="{s.color}"/>'
            )
            angle += sweep
        pie = "".join(segments)

    hole = f'<circle cx="{cx}" cy="{cy}" r="{hole_r}" fill="#fff"/>'
    n_size = hole_r * 0.5
    l_size = hole_r * 0.17
    text = (
        f'<text x="{cx}" y="{cy + n_size * 0.32:.1f}" text-anchor="middle" '
        f'font-family="\'Plus Jakarta Sans\',sans-serif" font-size="{n_size:.1f}" font-weight="800" fill="#111827">{total}</text>'
        f'<text x="{cx}" y="{cy + n_size * 0.32 + l_size + 8:.1f}" text-anchor="middle" '
        f'font-family="Inter,sans-serif" font-size="{l_size:.1f}" font-weight="600" '
        f'letter-spacing="1" fill="#6B7280">VAZIFA</text>'
    )
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">{pie}{hole}{text}</svg>'


def _bar_width(percent: int, total: int) -> str:
    """Progress-bar to'ldirilish foizi — 0% bo'lsa bo'sh, aks holda ko'rinishi uchun min. 3%."""
    if not total or percent <= 0:
        return "0%"
    return f"{max(percent, 3)}%"


def _progress_color(percent: int) -> str:
    if percent >= 100:
        return "#16A34A"
    if percent >= 50:
        return "#2563EB"
    if percent > 0:
        return "#D97706"
    return "var(--line)"


def _kpi_sub(data: ReportData, attr: str) -> str:
    if attr == "total":
        return "joriy faol"
    if attr == "created_in_period":
        return "shu davrda"
    if attr == "done_in_period":
        percent = round(data.done_in_period * 100 / data.total) if data.total else 0
        return f"{percent}% bajarilish"
    if attr == "overdue":
        return "e'tibor talab etadi"
    return ""


def _task_row(t: ProjectTaskRow) -> str:
    if t.overdue:
        bg, color = "rgba(220, 38, 38, 0.12)", "#DC2626"
    else:
        bg, color = _tint(t.status_color), t.status_color
    due_attr = ' class="due over"' if t.overdue else ' class="due"'
    return (
        f'<tr><td class="num">{t.seq}</td><td>{_esc(t.name)}</td><td class="who">{_esc(t.assignee)}</td>'
        f"<td{due_attr}>{_esc(t.deadline)}</td>"
        f'<td><span class="badge" style="background:{bg};color:{color}">{_esc(t.status_label)}</span></td></tr>'
    )


def build_html(data: ReportData) -> str:
    """hisobot.html ko'rinishidagi to'liq hisobot — A4 chop etishga tayyor HTML."""
    org_name = _clean(data.org_name) or ORG_FULL_NAME

    if data.logo_path.exists():
        logo_b64 = base64.b64encode(data.logo_path.read_bytes()).decode("ascii")
        logo_html = f'<img class="header__logo" src="data:image/png;base64,{logo_b64}" alt="logo">'
    else:
        logo_html = '<div class="header__logo">IQTM</div>'

    kpi_html = "".join(
        f'<div class="kpi{" accent-red" if attr == "overdue" else ""}">'
        f'<div class="label">{_esc(label)}</div>'
        f'<div class="value">{getattr(data, attr)}</div>'
        f'<div class="sub">{_esc(_kpi_sub(data, attr))}</div></div>'
        for label, attr in _SUMMARY_LABELS
    )

    total_status = sum(s.count for s in data.statuses)
    donut_svg = _donut_svg(data.statuses, total_status)
    legend_html = "".join(
        f'<div class="leg{" zero" if s.count == 0 else ""}">'
        f'<div class="dot" style="background:{s.color}"></div>'
        f'<div class="ln">{_esc(s.name)}</div><div class="cnt">{s.count}</div></div>'
        for s in data.statuses
    ) or '<div class="empty">Holatlar mavjud emas</div>'

    depts_sorted = sorted(data.departments, key=lambda d: d.percent, reverse=True)
    depts_html = "".join(
        f'<div class="dept"><div class="nm">{_esc(d.name)}</div>'
        f'<div class="track"><div class="fill" style="width:{_bar_width(d.percent, d.total)};background:{d.color}"></div></div>'
        f'<div class="pct"><b>{f"{d.percent}%" if d.total else "—"}</b> · {d.done}/{d.total}</div></div>'
        for d in depts_sorted
    ) or '<div class="empty">Bo\'limlar mavjud emas</div>'

    projects_html = ""
    for proj in data.projects:
        late = proj.schedule_label.startswith("Orqada qolmoqda") or proj.schedule_label.startswith("Muddat o'tgan")
        pill_label = "Orqada qolmoqda" if late else proj.status_label
        width = _bar_width(proj.percent, proj.total)
        pfill_color = "var(--late)" if late else _progress_color(proj.percent)
        rows = "".join(_task_row(t) for t in proj.tasks) or (
            '<tr><td colspan="5" class="empty">Vazifalar mavjud emas</td></tr>'
        )
        second_div = (
            f'<div class="warn">⚠ {_esc(proj.schedule_label)}</div>'
            if late else
            f'<div>Joriy jarayon: <b>{_esc(proj.schedule_label)}</b></div>'
        )
        projects_html += (
            f'<div class="project{" late" if late else ""}">'
            f'<div class="proj-head">'
            f'<div class="proj-title"><div class="pn">{_esc(proj.name)}</div>'
            f'<div class="pill{" late" if late else ""}">{_esc(pill_label)}</div></div>'
            f'<div class="proj-prog"><div class="ptrack"><div class="pfill" '
            f'style="width:{width};background:{pfill_color}"></div></div>'
            f'<div class="ptxt"><b>{proj.done}/{proj.total}</b> · {proj.percent}%</div></div>'
            f"</div>"
            f'<div class="proj-sub"><div>Muddat: <b>{_esc(proj.deadline_label)}</b></div>{second_div}</div>'
            f"<table><thead><tr><th>#</th><th>Vazifa</th><th>Mas'ul</th><th>Muddat</th><th>Holat</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
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
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{_HTML_CSS}</style>
</head>
<body>
<div class="sheet">
  <div class="header">
    <div>
      <div class="header__brand">
        {logo_html}
        <div class="header__name">{_esc(org_name)}</div>
      </div>
      <span class="header__doctype">{_esc(data.period_title)} hisobot</span>
      <div class="header__h1">Hisobot</div>
    </div>
    <div class="header__meta">
      <div class="period">{data.start.strftime('%d.%m.%Y')} — {data.end.strftime('%d.%m.%Y')}</div>
      <div class="gen">Yaratildi: {data.generated_at.strftime('%d.%m.%Y, %H:%M')}</div>
    </div>
  </div>
  <div class="pad">
    <h2 class="section">Umumiy ko'rsatkichlar</h2>
    <div class="kpis">{kpi_html}</div>

    <h2 class="section">Holatlar bo'yicha</h2>
    <div class="status-wrap">
      {donut_svg}
      <div class="legend">{legend_html}</div>
    </div>

    <h2 class="section">Bo'limlar bo'yicha</h2>
    <div class="depts">{depts_html}</div>

    <h2 class="section">Loyihalar</h2>
    <div class="loyihalar">{projects_html}</div>
  </div>
  <div class="footer">
    <span>{_esc(org_name)}</span>
    <span>Avtomatik yaratilgan hisobot</span>
  </div>
</div>
</body>
</html>"""


def build_pdf(data: ReportData) -> bytes:
    """HTML hisobotni (hisobot.html dizayni) PDF'ga aylantiradi."""
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

    # ── Faqat birinchi sahifa tepasida: logotip + tashkilot nomi + chiziq ──
    top_table = doc.add_table(rows=1, cols=2)
    top_table.autofit = False
    top_table.allow_autofit = False
    top_table.columns[0].width = Inches(0.6)
    top_table.columns[1].width = Inches(5.9)
    logo_cell, org_cell = top_table.rows[0].cells
    logo_cell.width = Inches(0.6)
    org_cell.width = Inches(5.9)
    logo_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    org_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    if data.logo_path.exists():
        logo_cell.paragraphs[0].add_run().add_picture(str(data.logo_path), width=Inches(0.45))
    run = org_cell.paragraphs[0].add_run(org_name)
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = navy

    line_p = doc.add_paragraph()
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
