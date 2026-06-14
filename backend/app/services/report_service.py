"""Statistik hisobotlar uchun ma'lumot yig'ish.

Format-ga xos generatsiya (PDF/DOCX) ``report_export`` modulida.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import case, func, select
from sqlalchemy import false as sql_false, true as sql_true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProjectStatus, TaskType
from app.models import Department, Project, Task, User
from app.services import board_service, settings_service
from app.services.upload_service import resolve_path

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
DEFAULT_LOGO = ASSETS_DIR / "logo.png"

_PERIOD_DAYS = {"week": 7, "month": 30, "year": 365}
_PERIOD_LABELS = {"week": "Haftalik", "month": "Oylik", "year": "Yillik"}
_PERIOD_TITLES = {"week": "Haftalik", "month": "Oylik", "year": "Yillik"}
_MONTH_NAMES = {
    1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel", 5: "May", 6: "Iyun",
    7: "Iyul", 8: "Avgust", 9: "Sentyabr", 10: "Oktyabr", 11: "Noyabr", 12: "Dekabr",
}


def resolve_period_range(
    period: str,
    year: int | None = None,
    month: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[date, date]:
    """Davr uchun (boshlanish, tugash) sanalarini hisoblaydi.

    Ustunlik tartibi: aniq sana oralig'i > aniq oy/yil > nisbiy davr (oxirgi N kun).
    """
    if date_from and date_to:
        return date_from, date_to
    if period == "year" and year:
        return date(year, 1, 1), date(year, 12, 31)
    if period == "month" and year and month:
        start = date(year, month, 1)
        end = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
        return start, end
    days = _PERIOD_DAYS.get(period, _PERIOD_DAYS["month"])
    end = date.today()
    start = end - timedelta(days=days - 1)
    return start, end


def period_label(
    period: str,
    start: date,
    end: date,
    year: int | None = None,
    month: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> str:
    """Hisobot sarlavhasi uchun davr nomi."""
    if date_from and date_to:
        return f"{start.strftime('%d.%m.%Y')} — {end.strftime('%d.%m.%Y')}"
    if period == "year" and year:
        return str(year)
    if period == "month" and year and month:
        return f"{_MONTH_NAMES.get(month, '')} {year}"
    return _PERIOD_LABELS.get(period, _PERIOD_LABELS["week"])


@dataclass
class StatusCount:
    key: str
    name: str
    count: int
    color: str = "#64748b"


@dataclass
class DeptRow:
    name: str
    total: int
    done: int
    percent: int
    color: str = "#2481cc"


@dataclass
class ProjectTaskRow:
    seq: int
    name: str
    assignee: str
    deadline: str
    status_label: str
    status_color: str = "#64748b"
    overdue: bool = False


@dataclass
class ProjectRow:
    name: str
    status_label: str
    total: int
    done: int
    percent: int
    deadline_label: str
    schedule_label: str
    tasks: list[ProjectTaskRow] = field(default_factory=list)


@dataclass
class ReportData:
    period: str
    period_label: str
    period_title: str
    start: date
    end: date
    generated_at: datetime
    total: int
    overdue: int
    created_in_period: int
    done_in_period: int
    statuses: list[StatusCount] = field(default_factory=list)
    departments: list[DeptRow] = field(default_factory=list)
    projects: list[ProjectRow] = field(default_factory=list)
    logo_path: Path = DEFAULT_LOGO
    org_name: str = ""


def user_label(name: str, username: str | None) -> str:
    """Xodim ism-familiyasi va telegram foydalanuvchi nomi: "Ism Familiya (@username)"."""
    return f"{name} (@{username})" if username else name


def _schedule_label(
    deadline: date | None, created_at: date, today: date, percent: int
) -> str:
    """Loyihaning muddatga nisbatan holati — matn ko'rinishida."""
    if deadline is None:
        return "Muddat belgilanmagan"
    days_left = (deadline - today).days
    if percent >= 100:
        return "Bajarildi"
    if days_left < 0:
        return f"Muddat o'tgan — {abs(days_left)} kun kechikdi"

    total_days = (deadline - created_at).days
    time_percent = round((today - created_at).days * 100 / total_days) if total_days > 0 else 100
    time_percent = max(0, min(100, time_percent))

    if percent >= time_percent:
        return f"Muddatida — {days_left} kun qoldi"
    return f"Orqada qolmoqda — {days_left} kun qoldi (vaqt {time_percent}%, bajarildi {percent}%)"


async def collect_report_data(
    session: AsyncSession,
    period: str,
    year: int | None = None,
    month: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> ReportData:
    if period not in _PERIOD_DAYS:
        period = "week"

    start, end = resolve_period_range(period, year, month, date_from, date_to)
    period_start = datetime.combine(start, datetime.min.time())
    period_end = datetime.combine(end, datetime.max.time())
    now = datetime.now()
    label = period_label(period, start, end, year, month, date_from, date_to)

    columns = await board_service.list_columns(session)
    done_keys = {c.key for c in columns if c.is_done}
    columns_by_key = {c.key: c for c in columns}
    done_filter = Task.status.in_(done_keys) if done_keys else sql_false()
    active_filter = Task.status.not_in(done_keys) if done_keys else sql_true()

    # ── Joriy holat bo'yicha umumiy son ──
    status_result = await session.execute(
        select(Task.status, func.count())
        .where(Task.type != TaskType.PROJECT.value)
        .group_by(Task.status)
    )
    status_counts = dict(status_result.all())
    total = sum(status_counts.values())

    overdue = await session.scalar(
        select(func.count())
        .select_from(Task)
        .where(
            Task.type != TaskType.PROJECT.value,
            active_filter,
            Task.deadline.is_not(None),
            Task.deadline < now,
        )
    ) or 0

    created_in_period = await session.scalar(
        select(func.count())
        .select_from(Task)
        .where(
            Task.type != TaskType.PROJECT.value,
            Task.created_at >= period_start,
            Task.created_at <= period_end,
        )
    ) or 0

    done_in_period = await session.scalar(
        select(func.count())
        .select_from(Task)
        .where(
            Task.type != TaskType.PROJECT.value,
            done_filter,
            Task.updated_at >= period_start,
            Task.updated_at <= period_end,
        )
    ) or 0

    statuses = [
        StatusCount(key=c.key, name=c.name, count=status_counts.get(c.key, 0), color=c.color)
        for c in columns
    ]

    # ── Bo'limlar bo'yicha ──
    dept_result = await session.execute(
        select(
            Department.name,
            Department.color,
            func.count(Task.id),
            func.sum(case((done_filter, 1), else_=0)),
        )
        .select_from(Department)
        .outerjoin(Task, (Task.dep_id == Department.id) & (Task.type != TaskType.PROJECT.value))
        .group_by(Department.id, Department.name, Department.color)
        .order_by(Department.name)
    )
    departments = [
        DeptRow(
            name=name, total=total_n or 0, done=done_n or 0,
            percent=round((done_n or 0) * 100 / total_n) if total_n else 0,
            color=color,
        )
        for name, color, total_n, done_n in dept_result.all()
    ]

    # ── Loyihalar ──
    proj_result = await session.execute(select(Project).order_by(Project.created_at.desc()))
    db_projects = list(proj_result.scalars().all())

    proj_task_result = await session.execute(
        select(Task.project_id, Task.name, Task.status, Task.deadline, User.name)
        .select_from(Task)
        .outerjoin(User, Task.masul_id == User.id)
        .where(Task.project_id.is_not(None))
        .order_by(Task.project_id, Task.created_at)
    )
    proj_tasks: dict[int, list[tuple[str, str, datetime | None, str | None]]] = {}
    for project_id, task_name, task_status, task_deadline, masul_name in proj_task_result.all():
        proj_tasks.setdefault(project_id, []).append(
            (task_name, task_status, task_deadline, masul_name)
        )

    projects = []
    for proj in db_projects:
        rows = proj_tasks.get(proj.id, [])
        tasks = []
        for seq, (task_name, task_status, task_deadline, masul_name) in enumerate(rows, start=1):
            col = columns_by_key.get(task_status)
            label = col.name if col else task_status
            overdue = task_status not in done_keys and bool(task_deadline) and task_deadline < now
            if overdue:
                label = f"{label} (kechikkan)"
            tasks.append(ProjectTaskRow(
                seq=seq,
                name=task_name,
                assignee=masul_name or "—",
                deadline=task_deadline.strftime("%d.%m.%Y %H:%M") if task_deadline else "—",
                status_label=label,
                status_color=col.color if col else "#64748b",
                overdue=overdue,
            ))
        total_tasks = len(rows)
        done_count = sum(1 for _, status_key, _, _ in rows if status_key in done_keys)
        percent = round(done_count * 100 / total_tasks) if total_tasks else 0
        projects.append(ProjectRow(
            name=proj.name,
            status_label="Tugagan" if proj.status == ProjectStatus.DONE else "Faol",
            total=total_tasks,
            done=done_count,
            percent=percent,
            deadline_label=proj.deadline.strftime("%d.%m.%Y") if proj.deadline else "—",
            schedule_label=_schedule_label(proj.deadline, proj.created_at.date(), end, percent),
            tasks=tasks,
        ))

    logo_path = await _resolve_logo(session)
    org_name = await settings_service.get_org_name(session)

    return ReportData(
        period=period,
        period_label=label,
        period_title=_PERIOD_TITLES.get(period, "Hisobot"),
        start=start, end=end, generated_at=now,
        total=total, overdue=overdue,
        created_in_period=created_in_period, done_in_period=done_in_period,
        statuses=statuses, departments=departments,
        projects=projects,
        logo_path=logo_path,
        org_name=org_name,
    )


async def _resolve_logo(session: AsyncSession) -> Path:
    """Hujjatlar uchun original logotip — sozlanmagan bo'lsa standart logo."""
    logo_path = await settings_service.get_logo_doc_path(session)
    if logo_path and logo_path.startswith("/uploads/"):
        path = resolve_path(logo_path)
        if path.exists():
            return path
    return DEFAULT_LOGO
