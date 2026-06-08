"""Vazifa biznes-logikasi: yaratish, holat o'zgartirish, o'chirish.

Guruh xabarlari va eslatma shu yerda boshqariladi (handlerlarda emas).
"""
import logging
from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import notifications as notify
from app.core.constants import TaskStatus
from app.models import Department, Log, Reminder, Task, User
from app.schemas.task import TaskCreate

logger = logging.getLogger(__name__)


async def _dep(session: AsyncSession, dep_id: str | None) -> Department | None:
    return await session.get(Department, dep_id) if dep_id else None


async def _user(session: AsyncSession, uid: int | None) -> User | None:
    return await session.get(User, uid) if uid else None


def _mention(user: User | None) -> str:
    if not user:
        return "—"
    return f"@{user.username}" if user.username else user.name


def _dep_label(dep: Department | None) -> str:
    return f"{dep.emoji} {dep.name}" if dep else "—"


async def _log(session: AsyncSession, user_id: int, action: str) -> None:
    session.add(Log(user_id=user_id, action=action))


async def create_task(
    session: AsyncSession, data: TaskCreate, created_by: int
) -> Task:
    task = Task(
        name=data.name,
        description=data.description,
        dep_id=data.dep_id,
        masul_id=data.masul_id,
        created_by=created_by,
        deadline=data.deadline,
        type=data.type,
    )
    session.add(task)
    await session.flush()  # task.id olish uchun

    await _log(session, created_by, f"Vazifa yaratildi: #{task.id} {task.name}")

    # Deadline'dan 1 kun oldin eslatma
    if task.deadline:
        remind_at = datetime.combine(
            task.deadline - timedelta(days=1), time(9, 0)
        )
        session.add(Reminder(task_id=task.id, remind_at=remind_at))

    # Guruhga e'lon (commit'dan keyin ID kerak emas, lekin nomlar kerak)
    dep = await _dep(session, task.dep_id)
    masul = await _user(session, task.masul_id)
    await session.flush()

    text = (
        f"📌 <b>Yangi vazifa #{task.id}</b>\n"
        f"🏢 {_dep_label(dep)}\n"
        f"📝 {task.name}\n"
        f"👤 Mas'ul: {_mention(masul)}\n"
        f"⏰ Muddat: {task.deadline or 'belgilanmagan'}"
    )
    if task.description:
        text += f"\n📄 {task.description}"
    topic_id = dep.topic_id if dep else None
    await notify.send_to_group(text, topic_id)
    if masul:
        await notify.send_dm(masul.id, text)

    return task


async def change_status(
    session: AsyncSession, task: Task, new_status: TaskStatus, actor: User
) -> Task:
    task.status = new_status
    await _log(
        session, actor.id, f"Vazifa holati: #{task.id} → {new_status.value}"
    )

    dep = await _dep(session, task.dep_id)
    masul = await _user(session, task.masul_id)

    if new_status == TaskStatus.DONE:
        creator = await _user(session, task.created_by)
        text = (
            f"✅ <b>Vazifa bajarildi #{task.id}</b>\n"
            f"🏢 {_dep_label(dep)}\n"
            f"📝 {task.name}\n"
            f"👤 Bajaruvchi: {_mention(masul)}\n"
            f"📣 Qo'ygan: {_mention(creator)}"
        )
    else:
        text = (
            f"📌 <b>Vazifa holati o'zgardi</b>\n"
            f"🏢 {_dep_label(dep)}\n"
            f"📝 #{task.id} {task.name}\n"
            f"➡️ {new_status.emoji} {new_status.label}\n"
            f"👤 O'zgartirdi: {actor.name}"
        )
    await notify.send_to_group(text, dep.topic_id if dep else None)
    return task


async def get_board_tasks(
    session: AsyncSession, user: User
) -> list[Task]:
    """Doska uchun vazifalar — boshliq hammasini, xodim o'zinikini."""
    from app.core.constants import Role, TaskType

    stmt = select(Task).where(Task.type != TaskType.PROJECT)
    if user.role != Role.BOSS:
        stmt = stmt.where(
            (Task.masul_id == user.id) | (Task.created_by == user.id)
        )
    stmt = stmt.order_by(Task.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())
