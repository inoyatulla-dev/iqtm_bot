"""Scheduler — eslatma, kechikkan vazifa, haftalik hisobot."""
import logging
from datetime import date, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app import notifications as notify
from app.core.constants import TaskType
from app.db.base import SessionFactory
from app.models import Department, Reminder, Task, User
from app.services import board_service, settings_service

logger = logging.getLogger(__name__)


async def check_reminders():
    """Vaqti kelgan eslatmalarni yuborish."""
    async with SessionFactory() as session:
        now = datetime.now()
        done_keys = await board_service.get_done_keys(session)
        result = await session.execute(
            select(Reminder).where(Reminder.sent == False, Reminder.remind_at <= now)  # noqa: E712
        )
        for r in result.scalars().all():
            task = await session.get(Task, r.task_id)
            if not task or task.status in done_keys:
                r.sent = True
                continue
            text = (
                f"🔔 <b>Vazifa eslatmasi!</b>\n"
                f"📝 #{task.id}: {task.name}\n"
                f"⏰ Muddat: {task.deadline}"
            )
            if task.masul_id:
                await notify.send_dm(task.masul_id, text)
            dep = await session.get(Department, task.dep_id) if task.dep_id else None
            topic_id = (dep.topic_id if dep else None) or await settings_service.get_routed_topic(
                session, "reminder"
            )
            await notify.send_to_group(text, topic_id)
            r.sent = True
        await session.commit()


async def check_overdue():
    """Kechikkan vazifalar bo'yicha kunlik guruh xabari."""
    async with SessionFactory() as session:
        today = date.today()
        done_keys = await board_service.get_done_keys(session)
        result = await session.execute(
            select(Task).where(
                Task.type != TaskType.PROJECT,
                Task.status.not_in(done_keys) if done_keys else True,
                Task.deadline.is_not(None),
                Task.deadline < today,
            )
        )
        tasks = list(result.scalars().all())
        if not tasks:
            return
        lines = ["🚨 <b>Kechikkan vazifalar:</b>", ""]
        for t in tasks:
            lines.append(f"• #{t.id} {t.name} — muddat {t.deadline}")
        topic_id = await settings_service.get_routed_topic(session, "overdue")
        await notify.send_to_group("\n".join(lines), topic_id)


async def weekly_report():
    """Haftalik hisobot — har juma."""
    async with SessionFactory() as session:
        done_keys = await board_service.get_done_keys(session)
        result = await session.execute(
            select(Task.status, Task.id).where(Task.type != TaskType.PROJECT)
        )
        rows = result.all()
        total = len(rows)
        done = sum(1 for s, _ in rows if s in done_keys)
        prog = int(done / total * 100) if total else 0
        text = (
            f"📈 <b>Haftalik hisobot — {date.today()}</b>\n\n"
            f"Jami: {total} | ✅ {done} | {prog}%"
        )
        topic_id = await settings_service.get_routed_topic(session, "weekly")
        await notify.send_to_group(text, topic_id)


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(check_reminders, "interval", minutes=30, id="reminders")
    scheduler.add_job(check_overdue, "cron", hour=9, minute=0, id="overdue")
    scheduler.add_job(
        weekly_report, "cron", day_of_week="fri", hour=18, minute=0, id="weekly"
    )
    return scheduler
