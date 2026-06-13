"""Doska ustunlari (BoardColumn) bilan ishlash — ro'yxat, qidiruv, "yakuniy" kalitlar.

Vazifa holati endi qattiq enum emas, shuning uchun "bajarilgan/kechikkan" kabi
hisoblar shu yerdagi yordamchilar orqali (BoardColumn.is_done) aniqlanadi.
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BoardColumn, Task


async def list_columns(session: AsyncSession) -> list[BoardColumn]:
    result = await session.execute(select(BoardColumn).order_by(BoardColumn.seq, BoardColumn.id))
    return list(result.scalars().all())


async def get_column(session: AsyncSession, key: str) -> BoardColumn | None:
    return await session.scalar(select(BoardColumn).where(BoardColumn.key == key))


async def get_done_keys(session: AsyncSession) -> set[str]:
    result = await session.execute(select(BoardColumn.key).where(BoardColumn.is_done.is_(True)))
    return set(result.scalars().all())


async def get_initial_keys(session: AsyncSession) -> set[str]:
    result = await session.execute(select(BoardColumn.key).where(BoardColumn.is_initial.is_(True)))
    return set(result.scalars().all())


async def get_initial_key(session: AsyncSession) -> str:
    col = await session.scalar(select(BoardColumn).where(BoardColumn.is_initial.is_(True)))
    if col:
        return col.key
    first = await session.scalar(select(BoardColumn).order_by(BoardColumn.seq, BoardColumn.id))
    return first.key if first else "new"


def is_overdue(task: Task, done_keys: set[str]) -> bool:
    """Kechikkan: muddat o'tgan va hali "yakuniy" ustunga tushmagan."""
    return (
        task.deadline is not None
        and task.status not in done_keys
        and task.deadline < datetime.now()
    )
