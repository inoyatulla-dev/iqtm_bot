"""Statistika va xodimlar reytingi."""
from datetime import date

from fastapi import APIRouter
from sqlalchemy import case, func, select

from app.api.deps import BossUser, CurrentUser, SessionDep
from app.core.constants import TaskType
from app.models import Task, User
from app.schemas.stats import RatingRow, StatusCounts
from app.services import board_service

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/me", response_model=StatusCounts)
async def my_stats(user: CurrentUser, session: SessionDep):
    return await _counts(session, masul_id=user.id)


@router.get("/global", response_model=StatusCounts)
async def global_stats(_: BossUser, session: SessionDep):
    return await _counts(session)


@router.get("/rating", response_model=list[RatingRow])
async def rating(_: BossUser, session: SessionDep):
    today = date.today()
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
        )
        for r in result.all()
    ]


async def _counts(session: SessionDep, masul_id: int | None = None) -> StatusCounts:
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
    return counts
