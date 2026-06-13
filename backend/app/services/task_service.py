"""Vazifa biznes-logikasi: yaratish, holat o'zgartirish, o'chirish.

Guruh xabarlari va eslatma shu yerda boshqariladi (handlerlarda emas).
"""
import logging
from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import notifications as notify
from app.models import BoardColumn, Comment, Department, Log, Reminder, Task, User
from app.schemas.task import TaskCreate
from app.services import board_service, settings_service
from app.services.report_service import user_label

logger = logging.getLogger(__name__)


async def _dep(session: AsyncSession, dep_id: str | None) -> Department | None:
    return await session.get(Department, dep_id) if dep_id else None


async def _user(session: AsyncSession, uid: int | None) -> User | None:
    return await session.get(User, uid) if uid else None


def _mention(user: User | None) -> str:
    if not user:
        return "—"
    return user_label(user.name, user.username)


def _dep_label(dep: Department | None) -> str:
    return f"{dep.emoji} {dep.name}" if dep else "—"


def _fmt_deadline(value: datetime | None) -> str:
    if not value:
        return "belgilanmagan"
    if value.hour == 0 and value.minute == 0:
        return value.strftime("%d.%m.%Y")
    return value.strftime("%d.%m.%Y %H:%M")


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
        status=await board_service.get_initial_key(session),
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

    tpl = await settings_service.get_template(session, "new_task")
    text = settings_service.render_template(
        tpl,
        id=task.id,
        department=_dep_label(dep),
        name=task.name,
        assignee=_mention(masul),
        deadline=_fmt_deadline(task.deadline),
        description=task.description or "—",
    )

    initial_col = await board_service.get_column(session, task.status)
    if not initial_col or initial_col.notify:
        topic_id = (dep.topic_id if dep else None) or await settings_service.get_routed_topic(
            session, "new_task"
        )
        await notify.send_to_group(text, topic_id)
    # Mas'ulga doim shaxsiy xabar (topshiriq berildi)
    if masul:
        await notify.send_dm(masul.id, text)

    return task


async def change_status(
    session: AsyncSession, task: Task, column: BoardColumn, actor: User
) -> Task:
    task.status = column.key
    await _log(session, actor.id, f"Vazifa holati: #{task.id} → {column.key}")

    dep = await _dep(session, task.dep_id)
    masul = await _user(session, task.masul_id)

    if column.is_done:
        event = "done"
        creator = await _user(session, task.created_by)
        last_comment = await session.scalar(
            select(Comment)
            .where(Comment.task_id == task.id)
            .order_by(Comment.created_at.desc())
            .limit(1)
        )
        tpl = await settings_service.get_template(session, event)
        text = settings_service.render_template(
            tpl,
            id=task.id,
            department=_dep_label(dep),
            name=task.name,
            assignee=_mention(masul),
            creator=_mention(creator),
            checker=actor.name,
            comment=last_comment.text if last_comment else "—",
        )
    else:
        event = "status_change"
        tpl = await settings_service.get_template(session, event)
        text = settings_service.render_template(
            tpl,
            id=task.id,
            department=_dep_label(dep),
            name=task.name,
            status=f"{column.emoji} {column.name}",
            actor=actor.name,
        )
    # Ustunда bildirishnoma o'chirilган bo'lsa — xabar yuborilmaydi
    if column.notify:
        topic_id = (dep.topic_id if dep else None) or await settings_service.get_routed_topic(
            session, event
        )
        await notify.send_to_group(text, topic_id)
        if masul and masul.id != actor.id:
            await notify.send_dm(masul.id, text)
    return task


async def notify_comment(
    session: AsyncSession,
    task: Task,
    author: User,
    text: str,
    target_user_id: int | None = None,
) -> None:
    """Izoh qoldirilganda DM yuborish.

    target_user_id berilgan bo'lsa — faqat o'shaga; aks holda mas'ul + yaratuvchiga.
    """
    if target_user_id:
        recipients = {target_user_id} - {author.id}
    else:
        recipients = {task.masul_id, task.created_by} - {author.id, None}
    if not recipients:
        return
    msg = (
        f"💬 <b>Yangi izoh — vazifa #{task.id}</b>\n"
        f"📝 {task.name}\n"
        f"👤 {author.name}:\n"
        f"{text}"
    )
    for uid in recipients:
        await notify.send_dm(uid, msg)


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
