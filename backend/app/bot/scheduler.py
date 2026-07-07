"""Scheduler — eslatma, kechikkan vazifa, haftalik hisobot, tug'ilgan kun, zaxira."""
import logging
from datetime import date, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app import notifications as notify
from app.core.constants import TaskType, UserStatus
from app.db.base import SessionFactory
from app.models import Department, Reminder, Task, User
from app.services import board_service, notification_service, settings_service, task_service
from app.services.backup_service import backup_database
from app.services.storage_service import archive_overflow_files

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
            tpl = await settings_service.get_template(session, "reminder")
            text = settings_service.render_template(
                tpl,
                id=task.id,
                name=task.name,
                deadline=task_service._fmt_deadline(task.deadline),
            )
            assignee_ids = await task_service.get_assignee_ids(session, task.id)
            for uid in assignee_ids:
                await notification_service.notify_user(session, uid, "reminder", text, task.id)
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
        now = datetime.now()
        done_keys = await board_service.get_done_keys(session)
        result = await session.execute(
            select(Task).where(
                Task.type != TaskType.PROJECT,
                Task.status.not_in(done_keys) if done_keys else True,
                Task.deadline.is_not(None),
                Task.deadline < now,
            )
        )
        tasks = list(result.scalars().all())
        if not tasks:
            return
        tpl = await settings_service.get_template(session, "overdue")
        header = settings_service.render_template(tpl, date=date.today(), count=len(tasks))
        lines = [header, ""]
        for t in tasks:
            lines.append(f"• #{t.id} {t.name} — muddat {task_service._fmt_deadline(t.deadline)}")
        topic_id = await settings_service.get_routed_topic(session, "overdue")
        await notify.send_to_group("\n".join(lines), topic_id)


async def check_birthdays():
    """Bugun tug'ilgan kuni bo'lgan xodimlarni tabriklash — guruh + shaxsiy."""
    async with SessionFactory() as session:
        today = date.today()
        result = await session.execute(
            select(User).where(User.status == UserStatus.ACTIVE, User.birthday.is_not(None))
        )
        for u in result.scalars().all():
            if u.birthday.month == today.month and u.birthday.day == today.day:
                tpl = await settings_service.get_template(session, "birthday")
                text = settings_service.render_template(tpl, name=u.name)
                topic_id = await settings_service.get_routed_topic(session, "birthday")
                await notify.send_to_group(text, topic_id)
                await notify.send_dm(u.id, "🎉🎂 <b>Tug'ilgan kuningiz bilan!</b>\n\nSizga sog'lik, omad va yutuqlar tilaymiz! 🎁")


async def daily_backup():
    """Bazadan har kuni avtomatik zaxira nusxa olish (oxirgi 7 kun saqlanadi)."""
    try:
        backup_database()
    except Exception:
        logger.exception("Zaxira nusxa olishda xato")


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
        tpl = await settings_service.get_template(session, "weekly")
        text = settings_service.render_template(
            tpl, date=date.today(), total=total, done=done, percent=prog
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
    scheduler.add_job(check_birthdays, "cron", hour=8, minute=0, id="birthdays")
    scheduler.add_job(daily_backup, "cron", hour=3, minute=0, id="daily_backup")
    scheduler.add_job(archive_overflow_files, "cron", hour=4, minute=0, id="archive_overflow")
    return scheduler
