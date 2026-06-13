"""Statistik hisobotlar uchun ma'lumot yig'ish va diagramma chizish.

Format-ga xos generatsiya (PDF/DOCX/XLSX) ``report_export`` modulida.
"""
import io
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


@dataclass
class StatusCount:
    key: str
    name: str
    emoji: str
    color: str
    count: int


@dataclass
class DeptRow:
    name: str
    emoji: str
    total: int
    done: int


@dataclass
class RatingRow:
    name: str
    done: int
    active: int
    overdue: int
    done_period: int


@dataclass
class ProjectTaskRow:
    name: str
    assignee: str
    status_label: str


@dataclass
class ProjectRow:
    name: str
    status_label: str
    total: int
    done: int
    percent: int
    done_tasks: list[ProjectTaskRow] = field(default_factory=list)
    in_progress_tasks: list[ProjectTaskRow] = field(default_factory=list)
    planned_tasks: list[ProjectTaskRow] = field(default_factory=list)


@dataclass
class ReportData:
    period: str
    period_label: str
    start: date
    end: date
    generated_at: datetime
    total: int
    overdue: int
    created_in_period: int
    done_in_period: int
    statuses: list[StatusCount] = field(default_factory=list)
    departments: list[DeptRow] = field(default_factory=list)
    rating: list[RatingRow] = field(default_factory=list)
    projects: list[ProjectRow] = field(default_factory=list)
    logo_path: Path = DEFAULT_LOGO


def user_label(name: str, username: str | None) -> str:
    """Xodim ism-familiyasi va telegram foydalanuvchi nomi: "Ism Familiya (@username)"."""
    return f"{name} (@{username})" if username else name


async def collect_report_data(session: AsyncSession, period: str) -> ReportData:
    if period not in _PERIOD_DAYS:
        period = "week"

    end = date.today()
    start = end - timedelta(days=_PERIOD_DAYS[period] - 1)
    period_start = datetime.combine(start, datetime.min.time())
    now = datetime.now()

    columns = await board_service.list_columns(session)
    done_keys = {c.key for c in columns if c.is_done}
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
        .where(Task.type != TaskType.PROJECT.value, Task.created_at >= period_start)
    ) or 0

    done_in_period = await session.scalar(
        select(func.count())
        .select_from(Task)
        .where(
            Task.type != TaskType.PROJECT.value,
            done_filter,
            Task.updated_at >= period_start,
        )
    ) or 0

    statuses = [
        StatusCount(
            key=c.key, name=c.name, emoji=c.emoji, color=c.color,
            count=status_counts.get(c.key, 0),
        )
        for c in columns
    ]

    # ── Bo'limlar bo'yicha ──
    dept_result = await session.execute(
        select(
            Department.name,
            Department.emoji,
            func.count(Task.id),
            func.sum(case((done_filter, 1), else_=0)),
        )
        .select_from(Department)
        .outerjoin(Task, (Task.dep_id == Department.id) & (Task.type != TaskType.PROJECT.value))
        .group_by(Department.id, Department.name, Department.emoji)
        .order_by(Department.name)
    )
    departments = [
        DeptRow(name=name, emoji=emoji, total=total_n or 0, done=done_n or 0)
        for name, emoji, total_n, done_n in dept_result.all()
    ]

    # ── Xodimlar reytingi ──
    rating_result = await session.execute(
        select(
            User.name,
            User.username,
            func.sum(case((done_filter, 1), else_=0)).label("done"),
            func.sum(case((active_filter, 1), else_=0)).label("active"),
            func.sum(
                case(
                    (
                        active_filter
                        & Task.deadline.is_not(None)
                        & (Task.deadline < now),
                        1,
                    ),
                    else_=0,
                )
            ).label("overdue"),
            func.sum(
                case(
                    (done_filter & (Task.updated_at >= period_start), 1),
                    else_=0,
                )
            ).label("done_period"),
        )
        .select_from(User)
        .outerjoin(Task, (Task.masul_id == User.id) & (Task.type != TaskType.PROJECT.value))
        .where(User.status == "active")
        .group_by(User.id)
        .order_by(func.count(Task.id).desc())
    )
    rating = [
        RatingRow(
            name=user_label(name, username),
            done=done or 0, active=active or 0, overdue=overdue_n or 0,
            done_period=done_period or 0,
        )
        for name, username, done, active, overdue_n, done_period in rating_result.all()
    ]

    # ── Loyihalar ──
    initial_keys = {c.key for c in columns if c.is_initial}
    columns_by_key = {c.key: c for c in columns}

    proj_result = await session.execute(select(Project).order_by(Project.created_at.desc()))
    db_projects = list(proj_result.scalars().all())

    proj_task_result = await session.execute(
        select(Task.project_id, Task.name, Task.status, User.name)
        .select_from(Task)
        .outerjoin(User, Task.masul_id == User.id)
        .where(Task.project_id.is_not(None))
    )
    proj_tasks: dict[int, list[tuple[str, str, str]]] = {}
    for project_id, task_name, task_status, masul_name in proj_task_result.all():
        proj_tasks.setdefault(project_id, []).append((task_name, task_status, masul_name or "—"))

    projects = []
    for proj in db_projects:
        rows = proj_tasks.get(proj.id, [])
        done_tasks, in_progress_tasks, planned_tasks = [], [], []
        for task_name, task_status, masul_name in rows:
            col = columns_by_key.get(task_status)
            status_label = f"{col.emoji} {col.name}" if col else task_status
            row = ProjectTaskRow(name=task_name, assignee=masul_name, status_label=status_label)
            if task_status in done_keys:
                done_tasks.append(row)
            elif task_status in initial_keys:
                planned_tasks.append(row)
            else:
                in_progress_tasks.append(row)
        total_tasks = len(rows)
        done_count = len(done_tasks)
        projects.append(ProjectRow(
            name=proj.name,
            status_label="Tugagan" if proj.status == ProjectStatus.DONE else "Faol",
            total=total_tasks,
            done=done_count,
            percent=round(done_count * 100 / total_tasks) if total_tasks else 0,
            done_tasks=done_tasks,
            in_progress_tasks=in_progress_tasks,
            planned_tasks=planned_tasks,
        ))

    logo_path = await _resolve_logo(session)

    return ReportData(
        period=period,
        period_label=_PERIOD_LABELS[period],
        start=start, end=end, generated_at=now,
        total=total, overdue=overdue,
        created_in_period=created_in_period, done_in_period=done_in_period,
        statuses=statuses, departments=departments, rating=rating,
        projects=projects,
        logo_path=logo_path,
    )


async def _resolve_logo(session: AsyncSession) -> Path:
    logo_path = await settings_service.get_logo_path(session)
    if logo_path and logo_path.startswith("/uploads/"):
        path = resolve_path(logo_path)
        if path.exists():
            return path
    return DEFAULT_LOGO


def status_chart(statuses: list[StatusCount]) -> bytes:
    """Holatlar bo'yicha ustunli diagramma — PNG bayt."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [f"{s.emoji} {s.name}" for s in statuses]
    values = [s.count for s in statuses]
    colors = [s.color for s in statuses]

    fig, ax = plt.subplots(figsize=(6, 3.3))
    ax.bar(labels, values, color=colors)
    ax.set_title("Vazifalar holati bo'yicha")
    for i, v in enumerate(values):
        ax.text(i, v, str(v), ha="center", va="bottom", fontsize=9)
    plt.xticks(rotation=25, ha="right", fontsize=8)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def rating_chart(rating: list[RatingRow], top: int = 8) -> bytes:
    """Eng faol xodimlar (davr ichida bajarilgan vazifalar) — PNG bayt."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = sorted(rating, key=lambda r: r.done_period, reverse=True)[:top]
    rows = [r for r in rows if r.done_period > 0] or rows

    fig, ax = plt.subplots(figsize=(6, 3.3))
    names = [r.name for r in rows]
    values = [r.done_period for r in rows]
    ax.barh(names, values, color="#22c55e")
    ax.invert_yaxis()
    ax.set_title("Davrda bajarilgan vazifalar — xodimlar")
    for i, v in enumerate(values):
        ax.text(v, i, f" {v}", va="center", fontsize=9)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
