"""Statistika va xodimlar reytingi."""
from datetime import date, datetime

from fastapi import APIRouter
from sqlalchemy import case, func, select

from app.api.deps import BossUser, CurrentUser, DashboardUser, SessionDep
from app.core.constants import TaskType
from app.models import Department, Task, User
from app.schemas.stats import DashboardOut, DeptProgress, DistributionSlice, RatingRow, StatusCounts
from app.services import board_service, report_service

router = APIRouter(prefix="/stats", tags=["stats"])


def _period_range(
    period: str, year: int | None, month: int | None,
    date_from: date | None, date_to: date | None,
) -> tuple[datetime, datetime]:
    start, end = report_service.resolve_period_range(period, year, month, date_from, date_to)
    return datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.max.time())


@router.get("/me", response_model=StatusCounts)
async def my_stats(
    user: CurrentUser, session: SessionDep, period: str = "month",
    year: int | None = None, month: int | None = None,
    date_from: date | None = None, date_to: date | None = None,
):
    return await _counts(
        session, masul_id=user.id, period=period,
        year=year, month=month, date_from=date_from, date_to=date_to,
    )


@router.get("/global", response_model=StatusCounts)
async def global_stats(
    _: BossUser, session: SessionDep, period: str = "month",
    year: int | None = None, month: int | None = None,
    date_from: date | None = None, date_to: date | None = None,
):
    return await _counts(
        session, period=period,
        year=year, month=month, date_from=date_from, date_to=date_to,
    )


@router.get("/rating", response_model=list[RatingRow])
async def rating(
    _: BossUser, session: SessionDep, period: str = "month",
    year: int | None = None, month: int | None = None,
    date_from: date | None = None, date_to: date | None = None,
):
    today = date.today()
    period_start, period_end = _period_range(period, year, month, date_from, date_to)
    done_keys = await board_service.get_done_keys(session)
    is_done = Task.status.in_(done_keys) if done_keys else False
    is_active = Task.status.not_in(done_keys) if done_keys else True
    result = await session.execute(
        select(
            User.id,
            User.name,
            func.sum(case((is_done, 1), else_=0)).label("done"),
            func.sum(case((is_active, 1), else_=0)).label("active"),
            func.sum(
                case(
                    (
                        is_active
                        & (Task.deadline.is_not(None))
                        & (Task.deadline < today),
                        1,
                    ),
                    else_=0,
                )
            ).label("overdue"),
            func.sum(
                case(
                    (is_done & (Task.updated_at >= period_start) & (Task.updated_at <= period_end), 1),
                    else_=0,
                )
            ).label("done_in_period"),
        )
        .select_from(User)
        .outerjoin(Task, (Task.masul_id == User.id) & (Task.type != TaskType.PROJECT.value))
        .where(User.status == "active")
        .group_by(User.id)
        .order_by(func.count(Task.id).desc())
    )
    return [
        RatingRow(
            user_id=r.id, name=r.name,
            done=r.done or 0, active=r.active or 0, overdue=r.overdue or 0,
            done_in_period=r.done_in_period or 0,
        )
        for r in result.all()
    ]


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(
    _: DashboardUser, session: SessionDep, period: str = "month",
    year: int | None = None, month: int | None = None,
    date_from: date | None = None, date_to: date | None = None,
):
    done_keys = await board_service.get_done_keys(session)
    initial_keys = await board_service.get_initial_keys(session)

    result = await session.execute(
        select(Task.status, Task.deadline, Task.created_at, Task.updated_at, Task.dep_id)
        .where(Task.type != TaskType.PROJECT.value)
    )
    rows = result.all()

    now = datetime.now()
    period_start, period_end = _period_range(period, year, month, date_from, date_to)

    total = len(rows)
    done = overdue = new_count = new_in_period = closed_in_period = 0
    dept_totals: dict[str, int] = {}
    dept_done: dict[str, int] = {}

    for st, deadline, created_at, updated_at, dep_id in rows:
        is_done = st in done_keys
        is_overdue_task = not is_done and deadline is not None and deadline < now
        if is_done:
            done += 1
        elif is_overdue_task:
            overdue += 1
        elif st in initial_keys:
            new_count += 1

        if created_at and period_start <= created_at <= period_end:
            new_in_period += 1
        if is_done and updated_at and period_start <= updated_at <= period_end:
            closed_in_period += 1

        if dep_id:
            dept_totals[dep_id] = dept_totals.get(dep_id, 0) + 1
            if is_done:
                dept_done[dep_id] = dept_done.get(dep_id, 0) + 1

    in_progress = total - done - overdue - new_count

    deps_result = await session.execute(select(Department).order_by(Department.name))
    departments = []
    for dep in deps_result.scalars().all():
        d_total = dept_totals.get(dep.id, 0)
        d_done = dept_done.get(dep.id, 0)
        departments.append(
            DeptProgress(
                dep_id=dep.id,
                name=dep.name,
                emoji=dep.emoji,
                color=dep.color,
                total=d_total,
                done=d_done,
                percent=round(d_done * 100 / d_total) if d_total else 0,
            )
        )

    def pct(n: int) -> int:
        return round(n * 100 / total) if total else 0

    distribution = [
        DistributionSlice(key="done", label="Bajarilgan", color="var(--ok)", percent=pct(done)),
        DistributionSlice(key="in_progress", label="Jarayonda", color="var(--accent)", percent=pct(in_progress)),
        DistributionSlice(key="new", label="Yangi", color="var(--warn)", percent=pct(new_count)),
        DistributionSlice(key="overdue", label="Kechikkan", color="var(--danger)", percent=pct(overdue)),
    ]

    return DashboardOut(
        total=total,
        done=done,
        in_progress=in_progress,
        overdue=overdue,
        new_in_period=new_in_period,
        closed_in_period=closed_in_period,
        departments=departments,
        distribution=distribution,
    )


async def _counts(
    session: SessionDep, masul_id: int | None = None, period: str = "month",
    year: int | None = None, month: int | None = None,
    date_from: date | None = None, date_to: date | None = None,
) -> StatusCounts:
    period_start, period_end = _period_range(period, year, month, date_from, date_to)
    done_keys = await board_service.get_done_keys(session)
    stmt = select(Task.status, func.count()).where(Task.type != TaskType.PROJECT.value)
    if masul_id:
        stmt = stmt.where(Task.masul_id == masul_id)
    stmt = stmt.group_by(Task.status)
    result = await session.execute(stmt)
    counts = StatusCounts()
    for st, cnt in result.all():
        counts.counts[st] = cnt
        counts.total += cnt

    # Kechikkan
    today = date.today()
    over_stmt = (
        select(func.count())
        .select_from(Task)
        .where(
            Task.type != TaskType.PROJECT.value,
            Task.status.not_in(done_keys) if done_keys else True,
            Task.deadline.is_not(None),
            Task.deadline < today,
        )
    )
    if masul_id:
        over_stmt = over_stmt.where(Task.masul_id == masul_id)
    counts.overdue = await session.scalar(over_stmt) or 0

    # Davr ichida bajarilgan
    done_stmt = (
        select(func.count())
        .select_from(Task)
        .where(
            Task.type != TaskType.PROJECT.value,
            Task.status.in_(done_keys) if done_keys else False,
            Task.updated_at >= period_start,
            Task.updated_at <= period_end,
        )
    )
    if masul_id:
        done_stmt = done_stmt.where(Task.masul_id == masul_id)
    counts.done_in_period = await session.scalar(done_stmt) or 0
    return counts
