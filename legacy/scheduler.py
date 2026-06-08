import logging
from datetime import datetime, date, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot
import db
import group

logger = logging.getLogger(__name__)


async def check_reminders(bot: Bot):
    reminders = await db.get_pending_reminders()
    for r in reminders:
        task = await db.get_task(r["task_id"])
        if not task or task["status"] not in ("faol", "jarayonda"):
            await db.mark_reminder_sent(r["id"])
            continue

        dep = await db.get_department(task["dep_id"]) if task["dep_id"] and task["dep_id"] != "multi" else None
        masul = await db.get_user(task["masul_id"]) if task["masul_id"] else None

        # Mas'ulga shaxsiy
        if masul:
            try:
                await bot.send_message(
                    chat_id=masul["id"],
                    text=(
                        f"🔔 <b>Vazifa eslatmasi!</b>\n"
                        f"📝 #{task['id']}: {task['name']}\n"
                        f"⏰ Muddat: {task['deadline']}"
                    ),
                    parse_mode="HTML",
                )
            except Exception as e:
                logger.warning(f"Eslatma yuborishda xato (user {masul['id']}): {e}")

        # Bo'lim mavzusiga
        await group.notify_task_deadline(bot, task, dep, masul)
        await db.mark_reminder_sent(r["id"])


async def check_overdue_tasks(bot: Bot):
    tasks = await db.get_overdue_tasks()
    for task in tasks:
        await db.update_task(task["id"], status="kechikdi")
        dep = await db.get_department(task["dep_id"])
        masul = await db.get_user(task["masul_id"]) if task["masul_id"] else None
        await group.notify_task_overdue(bot, task, dep, masul)
        logger.info(f"Vazifa kechikdi: #{task['id']}")


async def send_weekly_report(bot: Bot):
    """Har Juma avtomatik — guruhga yuboradi."""
    stats = await db.get_stats_global()
    deps = await db.get_all_departments()

    lines = [f"📈 <b>Haftalik hisobot — {date.today()}</b>", ""]
    t = stats.get("tasks", {})
    total = sum(t.values())
    done = t.get("bajarildi", 0)
    prog = int(done / total * 100) if total else 0
    lines.append(f"Jami: {total} | ✅{done} 🔄{t.get('faol',0)} ⚠️{t.get('kechikdi',0)} | {prog}%")
    lines.append("")

    for dep in deps:
        ds = await db.get_stats_by_dep(dep["id"])
        dt = ds.get("tasks", {})
        dtotal = sum(dt.values())
        ddone = dt.get("bajarildi", 0)
        dprog = int(ddone / dtotal * 100) if dtotal else 0
        lines.append(f"{dep['emoji']} {dep['name']}: {dprog}% ({ddone}/{dtotal})")

    text = "\n".join(lines)
    await group.send_weekly_report(bot, text)
    logger.info("Haftalik hisobot guruhga yuborildi.")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")

    # Har 30 daqiqada eslatmalarni tekshirish
    scheduler.add_job(
        check_reminders, "interval", minutes=30, args=[bot], id="reminders"
    )
    # Har kuni soat 09:00 kechikkan vazifalarni tekshirish
    scheduler.add_job(
        check_overdue_tasks, "cron", hour=9, minute=0, args=[bot], id="overdue"
    )
    # Har juma soat 18:00 haftalik hisobot
    scheduler.add_job(
        send_weekly_report, "cron", day_of_week="fri", hour=18, minute=0,
        args=[bot], id="weekly_report"
    )

    return scheduler
