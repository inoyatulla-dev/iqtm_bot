import os
from telegram import Bot
from telegram.constants import ParseMode
import db as _db


async def get_group_id() -> int:
    val = await _db.get_setting("group_chat_id")
    if val:
        return int(val)
    return int(os.getenv("GROUP_CHAT_ID", "0"))


async def _get_topic(key: str) -> int | None:
    val = await _db.get_setting(key)
    return int(val) if val and str(val).lstrip("-").isdigit() else None


async def send_to_topic(bot: Bot, topic_id: int | None, text: str):
    group_id = await get_group_id()
    if not group_id:
        return
    kwargs = {"chat_id": group_id, "text": text, "parse_mode": ParseMode.HTML}
    if topic_id:
        kwargs["message_thread_id"] = topic_id
    try:
        await bot.send_message(**kwargs)
    except Exception as e:
        print(f"[group] xabar yuborishda xato: {e}")


def _dep_label(dep) -> str:
    return f"{dep['emoji']} {dep['name']}" if dep else "—"


def _mention(user) -> str:
    if not user:
        return "—"
    return f"@{user['username']}" if user["username"] else user["name"]


# ─── TASK NOTIFICATIONS → topic_vazifalar ────────────────────────

async def notify_new_task(bot: Bot, task, dep, masul):
    text = (
        f"📌 <b>Yangi vazifa #{task['id']}</b>\n"
        f"🏢 {_dep_label(dep)}\n"
        f"📝 {task['name']}\n"
        f"👤 Mas'ul: {_mention(masul)}\n"
        f"⏰ Muddat: {task['deadline'] or 'belgilanmagan'}"
    )
    if task["description"]:
        text += f"\n📄 {task['description']}"
    await send_to_topic(bot, await _get_topic("topic_vazifalar"), text)


async def notify_task_status_changed(bot: Bot, task, dep, masul, changer, new_status: str):
    status_labels = {
        "faol":        "🆕 Yangi",
        "jarayonda":   "🔄 Jarayonda",
        "tekshiruvda": "🔍 Tekshiruvda",
        "bajarildi":   "✅ Bajarildi",
        "kechikdi":    "⚠️ Kechikdi",
    }
    label = status_labels.get(new_status, new_status)
    changer_name = changer["name"] if changer else "—"
    text = (
        f"📌 <b>Vazifa holati o'zgardi</b>\n"
        f"🏢 {_dep_label(dep)}\n"
        f"📝 #{task['id']} {task['name']}\n"
        f"➡️ Yangi holat: {label}\n"
        f"👤 O'zgartirdi: {changer_name}"
    )
    await send_to_topic(bot, await _get_topic("topic_vazifalar"), text)


async def notify_task_done(bot: Bot, task, dep, masul, creator):
    text = (
        f"✅ <b>Vazifa bajarildi #{task['id']}</b>\n"
        f"🏢 {_dep_label(dep)}\n"
        f"📝 {task['name']}\n"
        f"👤 Bajaruvchi: {_mention(masul)}\n"
        f"📣 Qo'ygan: {_mention(creator)}"
    )
    await send_to_topic(bot, await _get_topic("topic_vazifalar"), text)


# ─── DEADLINE / OVERDUE → topic_reja ─────────────────────────────

async def notify_task_deadline(bot: Bot, task, dep, masul):
    text = (
        f"⚠️ <b>Muddat eslatmasi</b>\n"
        f"🏢 {_dep_label(dep)}\n"
        f"Vazifa #{task['id']}: {task['name']}\n"
        f"👤 Mas'ul: {_mention(masul)}\n"
        f"⏰ Muddat: {task['deadline']}"
    )
    await send_to_topic(bot, await _get_topic("topic_reja"), text)


async def notify_task_overdue(bot: Bot, task, dep, masul):
    text = (
        f"🚨 <b>Vazifa kechikdi!</b>\n"
        f"🏢 {_dep_label(dep)}\n"
        f"Vazifa #{task['id']}: {task['name']}\n"
        f"👤 Mas'ul: {_mention(masul)}\n"
        f"⏰ Muddat o'tdi: {task['deadline']}"
    )
    await send_to_topic(bot, await _get_topic("topic_reja"), text)


async def notify_stage_activated(bot: Bot, stages, deps_map, users_map):
    topic_id = await _get_topic("topic_reja")
    for s in stages:
        dep = deps_map.get(s["dep_id"])
        masul = users_map.get(s["masul_id"])
        text = (
            f"🔄 <b>Yangi bosqich faollashdi</b>\n"
            f"🏢 {_dep_label(dep)}\n"
            f"📋 Navbat {s['seq']}: {s['description']}\n"
            f"👤 Mas'ul: {_mention(masul)}\n"
            f"⏰ Muddat: {s['deadline'] or 'belgilanmagan'}"
        )
        await send_to_topic(bot, topic_id, text)


async def notify_dept_task_assigned(bot: Bot, task, dep, work_desc: str, worker=None):
    """Bo'limga vazifa biriktirilganda shu bo'lim topiciga yuborish."""
    worker_text = _mention(worker) if worker else "belgilanmagan"
    text = (
        f"📌 <b>Yangi vazifa: #{task['id']} {task['name']}</b>\n"
        f"🏢 Bo'lim: {_dep_label(dep)}\n"
        f"📋 Ish: {work_desc or '—'}\n"
        f"👤 Xodim: {worker_text}\n"
        f"⏰ Muddat: {task['deadline'] or 'belgilanmagan'}"
    )
    # Bo'lim o'z topiciga yuborish
    topic_id = dep["topic_id"] if dep else None
    await send_to_topic(bot, topic_id, text)


# ─── ANNOUNCEMENTS → topic_elonlar ───────────────────────────────

async def notify_project_done(bot: Bot, project):
    text = f"🎉 <b>Loyiha yakunlandi!</b>\n📁 {project['name']}"
    await send_to_topic(bot, await _get_topic("topic_elonlar"), text)


# ─── REPORTS → topic_hisobotlar ──────────────────────────────────

async def send_weekly_report(bot: Bot, text: str):
    await send_to_topic(bot, await _get_topic("topic_hisobotlar"), text)
