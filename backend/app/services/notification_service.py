"""Foydalanuvchiga bildirishnoma: Telegram DM + ilova ichi (notifications jadvali)."""
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app import notifications as notify
from app.models import Notification, Task


async def notify_user(
    session: AsyncSession,
    user_id: int,
    type_: str,
    text: str,
    task_id: int | None = None,
) -> None:
    session.add(Notification(user_id=user_id, type=type_, text=text, task_id=task_id))
    await notify.send_dm(user_id, text)


async def list_for_user(
    session: AsyncSession, user_id: int, limit: int = 300
) -> list[tuple[Notification, str | None]]:
    result = await session.execute(
        select(Notification, Task.name)
        .outerjoin(Task, Task.id == Notification.task_id)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return result.all()


async def unread_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
    )
    return result.scalar_one()


async def mark_read(session: AsyncSession, user_id: int, notif_id: int) -> None:
    await session.execute(
        update(Notification)
        .where(Notification.id == notif_id, Notification.user_id == user_id)
        .values(is_read=True)
    )


async def mark_all_read(session: AsyncSession, user_id: int) -> None:
    await session.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .values(is_read=True)
    )


async def set_archived(session: AsyncSession, user_id: int, notif_id: int) -> None:
    """Arxivlash — o'qilgan deb ham belgilanadi (ko'rilgan/hal qilingan hisoblanadi)."""
    await session.execute(
        update(Notification)
        .where(Notification.id == notif_id, Notification.user_id == user_id)
        .values(is_archived=True, is_read=True)
    )
