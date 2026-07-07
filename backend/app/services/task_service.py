"""Vazifa biznes-logikasi: yaratish, holat o'zgartirish, o'chirish.

Guruh xabarlari va eslatma shu yerda boshqariladi (handlerlarda emas).
"""
import logging
from datetime import datetime, time, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import notifications as notify
from app.models import BoardColumn, Comment, Department, Log, Reminder, Task, TaskAssignee, User
from app.schemas.task import TaskCreate
from app.services import board_service, notification_service, settings_service
from app.services.report_service import user_label

logger = logging.getLogger(__name__)


def resolve_primary(masul_id: int | None, assignee_ids: list[int] | None) -> int | None:
    """Asosiy mas'ulni aniqlash: ro'yxat berilgan bo'lsa — birinchisi."""
    if assignee_ids is not None:
        return assignee_ids[0] if assignee_ids else None
    return masul_id


async def set_assignees(
    session: AsyncSession,
    task: Task,
    masul_id: int | None,
    assignee_ids: list[int] | None,
) -> list[int]:
    """task_assignees jadvalini yangilaydi va task.masul_id ni asosiyga tenglaydi.

    Qaytaradi: yakuniy mas'ullar ID ro'yxati (asosiy birinchi).
    """
    if assignee_ids is None:
        # Ro'yxat berilmagan — masul_id atrofida qurib olamiz
        ids = [masul_id] if masul_id else []
    else:
        # Tartibni saqlab, takrorlarni olib tashlaymiz
        ids = list(dict.fromkeys(assignee_ids))

    task.masul_id = ids[0] if ids else None

    await session.execute(
        delete(TaskAssignee).where(TaskAssignee.task_id == task.id)
    )
    for uid in ids:
        session.add(TaskAssignee(task_id=task.id, user_id=uid))
    await session.flush()
    return ids


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


async def get_assignee_ids(session: AsyncSession, task_id: int) -> list[int]:
    result = await session.execute(
        select(TaskAssignee.user_id).where(TaskAssignee.task_id == task_id)
    )
    return list(result.scalars().all())


async def _assignee_mentions(session: AsyncSession, task: Task) -> str:
    """Vazifaga biriktirilgan xodimlar: bittasi bo'lsa oddiy matn, bir nechtasi
    bo'lsa har biri o'z qatorida, raqamlangan holda ko'rsatiladi."""
    ids = await get_assignee_ids(session, task.id)
    mentions = [_mention(await _user(session, uid)) for uid in ids]
    if not mentions:
        return "—"
    if len(mentions) == 1:
        return mentions[0]
    return "\n" + "\n".join(f"{i}. {m}" for i, m in enumerate(mentions, 1))


async def _assignment_text(session: AsyncSession, task: Task) -> str:
    dep = await _dep(session, task.dep_id)
    tpl = await settings_service.get_template(session, "new_task")
    return settings_service.render_template(
        tpl,
        id=task.id,
        department=_dep_label(dep),
        name=task.name,
        assignee=await _assignee_mentions(session, task),
        deadline=_fmt_deadline(task.deadline),
        description=task.description or "—",
    )


async def reassign_notify(session: AsyncSession, task: Task, added_ids: set[int]) -> None:
    """Vazifaga qayta tahrirlashda yangi qo'shilgan xodimlarga xabar (DM + ilova ichi)."""
    if not added_ids:
        return
    text = await _assignment_text(session, task)
    for uid in added_ids:
        await notification_service.notify_user(session, uid, "task_assigned", text, task.id)


async def create_task(
    session: AsyncSession, data: TaskCreate, created_by: int
) -> Task:
    task = Task(
        name=data.name,
        description=data.description,
        dep_id=data.dep_id,
        masul_id=resolve_primary(data.masul_id, data.assignee_ids),
        created_by=created_by,
        deadline=data.deadline,
        type=data.type,
        project_id=data.project_id,
        status=await board_service.get_initial_key(session),
    )
    session.add(task)
    await session.flush()  # task.id olish uchun

    assignee_ids = await set_assignees(session, task, data.masul_id, data.assignee_ids)

    await _log(session, created_by, f"Vazifa yaratildi: #{task.id} {task.name}")

    # Deadline'dan 1 kun oldin eslatma
    if task.deadline:
        remind_at = datetime.combine(
            task.deadline - timedelta(days=1), time(9, 0)
        )
        session.add(Reminder(task_id=task.id, remind_at=remind_at))

    # Guruhga e'lon (commit'dan keyin ID kerak emas, lekin nomlar kerak)
    dep = await _dep(session, task.dep_id)
    await session.flush()

    text = await _assignment_text(session, task)

    initial_col = await board_service.get_column(session, task.status)
    if not initial_col or initial_col.notify:
        topic_id = (dep.topic_id if dep else None) or await settings_service.get_routed_topic(
            session, "new_task"
        )
        await notify.send_to_group(text, topic_id)
    # Har bir mas'ulga shaxsiy xabar (topshiriq berildi) — DM + ilova ichi
    for uid in assignee_ids:
        await notification_service.notify_user(session, uid, "task_assigned", text, task.id)

    return task


async def change_status(
    session: AsyncSession, task: Task, column: BoardColumn, actor: User
) -> Task:
    task.status = column.key
    # "Yakuniy" ustunga kirganda arxiv sanog'i boshlanadi; chiqib ketsa — bekor bo'ladi
    task.done_at = datetime.now() if column.is_done else None
    await _log(session, actor.id, f"Vazifa holati: #{task.id} → {column.key}")

    dep = await _dep(session, task.dep_id)

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
            assignee=await _assignee_mentions(session, task),
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
        assignee_ids = await get_assignee_ids(session, task.id)
        for uid in assignee_ids:
            if uid != actor.id:
                await notification_service.notify_user(session, uid, event, text, task.id)
    return task


async def notify_comment(
    session: AsyncSession,
    task: Task,
    author: User,
    text: str,
    target_user_id: int | None = None,
) -> None:
    """Izoh qoldirilganda bildirishnoma (DM + ilova ichi).

    target_user_id berilgan bo'lsa — faqat o'shaga; aks holda barcha
    biriktirilgan xodimlar + yaratuvchiga (muallifdan tashqari).
    """
    if target_user_id:
        recipients = {target_user_id} - {author.id}
    else:
        assignee_ids = await get_assignee_ids(session, task.id)
        recipients = set(assignee_ids) | {task.created_by} - {author.id, None}
    if not recipients:
        return
    msg = (
        f"💬 <b>Yangi izoh — vazifa #{task.id}</b>\n"
        f"📝 {task.name}\n"
        f"👤 {author.name}:\n"
        f"{text}"
    )
    for uid in recipients:
        await notification_service.notify_user(session, uid, "comment", msg, task.id)


async def get_board_tasks(
    session: AsyncSession, user: User
) -> list[Task]:
    """Doska uchun vazifalar — boshliq va kuzatuvchi hammasini, xodim o'zinikini."""
    from app.core.constants import Role, TaskType

    stmt = select(Task).where(Task.type != TaskType.PROJECT)
    if user.role not in (Role.BOSS, Role.OBSERVER):
        assignee_exists = (
            select(TaskAssignee.task_id)
            .where(TaskAssignee.task_id == Task.id, TaskAssignee.user_id == user.id)
            .exists()
        )
        stmt = stmt.where(
            (Task.masul_id == user.id) | (Task.created_by == user.id) | assignee_exists
        )
    stmt = stmt.order_by(Task.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())
