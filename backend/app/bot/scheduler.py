"""Scheduler — eslatma, kechikkan vazifa, haftalik hisobot."""
import logging
from datetime import date, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app import notifications as notify
from app.core.constants import TaskStatus, TaskType
from app.db.base import SessionFactory
from app.models import Department, Reminder, Task, User

logger = logging.getLogger(__name__)


async def check_reminders():
    """Vaqti kelgan eslatmalarni yuborish."""
    async with SessionFactory() as session:
        now = datetime.now()
        result = await session.execute(
            select(Reminder).where(Reminder.sent == False, Reminder.remind_at <= now)  # noqa: E712
        )
        for r in result.scalars().all():
            task = await session.get(Task, r.task_id)
            if not task or task.status == TaskStatus.DONE:
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
            await notify.send_to_group(text, dep.topic_id if dep else None)
            r.sent = True
        await session.commit()


async def check_overdue():
    """Kechikkan vazifalar bo'yicha kunlik guruh xabari."""
    async with SessionFactory() as session:
        today = date.today()
        result = await session.execute(
            select(Task).where(
                Task.type != TaskType.PROJECT,
                Task.status != TaskStatus.DONE,
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
        from app.services.settings_service import get_topic

        await notify.send_to_group("\n".join(lines), await get_topic("topic_reports"))


async def weekly_report():
    """Haftalik hisobot — har juma."""
    async with SessionFactory() as session:
        result = await session.execute(
            select(Task.status, Task.id).where(Task.type != TaskType.PROJECT)
        )
        rows = result.all()
        total = len(rows)
        done = sum(1 for s, _ in rows if s == TaskStatus.DONE)
        prog = int(done / total * 100) if total else 0
        text = (
            f"📈 <b>Haftalik hisobot — {date.today()}</b>\n\n"
            f"Jami: {total} | ✅ {done} | {prog}%"
        )
        from app.services.settings_service import get_topic

        await notify.send_to_group(text, await get_topic("topic_reports"))


def setup_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(check_reminders, "interval", minutes=30, id="reminders")
    scheduler.add_job(check_overdue, "cron", hour=9, minute=0, id="overdue")
    scheduler.add_job(
        weekly_report, "cron", day_of_week="fri", hour=18, minute=0, id="weekly"
    )
    return scheduler
