from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import db
import keyboards as kb
from decorators import role_required, any_role


def _stats_text(stats: dict, title: str) -> str:
    t = stats.get("tasks", {})
    faol = t.get("faol", 0)
    done = t.get("bajarildi", 0)
    late = t.get("kechikdi", 0)
    total = faol + done + late
    prog = int(done / total * 100) if total else 0
    lines = [
        f"📊 <b>{title}</b>",
        "",
        f"📋 Jami vazifalar: {total}",
        f"✅ Bajarildi: {done}",
        f"🔄 Jarayonda: {faol}",
        f"⚠️ Kechikdi: {late}",
        f"📈 Progress: {prog}%",
    ]
    if "users" in stats:
        lines.append(f"\n👥 Faol xodimlar: {stats['users']}")
    if "projects" in stats:
        lines.append(f"📁 Faol loyihalar: {stats['projects']}")
    return "\n".join(lines)


@role_required("super")
async def stats_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stats = await db.get_stats_global()

    # Per-department
    deps = await db.get_all_departments()
    dep_lines = []
    for dep in deps:
        ds = await db.get_stats_by_dep(dep["id"])
        dt = ds.get("tasks", {})
        total = sum(dt.values())
        done = dt.get("bajarildi", 0)
        prog = int(done / total * 100) if total else 0
        dep_lines.append(f"  {dep['emoji']} {dep['name']}: {prog}% ({done}/{total})")

    text = _stats_text(stats, "To'liq statistika")
    if dep_lines:
        text += "\n\n<b>Bo'limlar:</b>\n" + "\n".join(dep_lines)

    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.menu_button()])
    )


@role_required("super", "admin")
async def stats_dep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    dep_id = db_user.get("dep_id")
    if not dep_id:
        await query.edit_message_text("🚫 Bo'lim biriktirilmagan.", reply_markup=InlineKeyboardMarkup([kb.menu_button()]))
        return
    dep = await db.get_department(dep_id)
    stats = await db.get_stats_by_dep(dep_id)
    text = _stats_text(stats, f"{dep['emoji']} {dep['name']} statistikasi")
    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.menu_button()])
    )


@any_role
async def stats_personal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    stats = await db.get_stats_by_user(db_user["id"])
    total = sum(stats.values())
    done = stats.get("bajarildi", 0)
    prog = int(done / total * 100) if total else 0
    text = (
        f"📊 <b>Shaxsiy statistika</b>\n\n"
        f"👤 {db_user['name']}\n\n"
        f"📋 Jami: {total}\n"
        f"✅ Bajarildi: {done}\n"
        f"🔄 Jarayonda: {stats.get('faol', 0)}\n"
        f"⚠️ Kechikdi: {stats.get('kechikdi', 0)}\n"
        f"📈 Progress: {prog}%"
    )
    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.menu_button()])
    )


@role_required("super", "admin")
async def rating_global(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))

    if db_user["role"] == "super":
        users = await db.get_rating()
        title = "🏆 Xodimlar reytingi (butun tizim)"
    else:
        dep_id = db_user.get("dep_id")
        if not dep_id:
            await query.edit_message_text("🚫 Bo'lim biriktirilmagan.", reply_markup=InlineKeyboardMarkup([kb.menu_button()]))
            return
        users = await db.get_rating(dep_id)
        dep = await db.get_department(dep_id)
        title = f"🏆 {dep['emoji']} {dep['name']} reytingi"

    if not users:
        await query.edit_message_text(f"{title}\n\nMa'lumot yo'q.", reply_markup=InlineKeyboardMarkup([kb.menu_button()]))
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = [f"<b>{title}</b>", ""]
    has_tasks = []
    no_tasks = []

    for u in users:
        total = (u["done"] or 0) + (u["active"] or 0) + (u["late"] or 0)
        if total == 0:
            no_tasks.append(u["name"])
        else:
            has_tasks.append(u)

    for i, u in enumerate(has_tasks):
        medal = medals[i] if i < 3 else f"  {i+1}."
        done = u["done"] or 0
        active = u["active"] or 0
        late = u["late"] or 0
        total = done + active + late
        prog = int(done / total * 100) if total else 0
        lines.append(
            f"{medal} <b>{u['name']}</b>\n"
            f"   ✅{done} 🔄{active} ⚠️{late} | {prog}%"
        )

    if no_tasks:
        lines.append("\n<i>Vazifasiz xodimlar:</i>")
        lines.extend(f"  — {n}" for n in no_tasks)

    await query.edit_message_text(
        "\n".join(lines), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.menu_button()])
    )


@role_required("super", "admin")
async def rating_dep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin uchun o'z bo'limi reytingi."""
    await rating_global(update, context)


async def _build_weekly_text() -> str:
    from datetime import date
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

    return "\n".join(lines)


@role_required("super")
async def report_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hisobotni botda ko'rsatadi — guruhga YUBORMAYDI."""
    query = update.callback_query
    await query.answer()
    text = await _build_weekly_text()
    from telegram import InlineKeyboardButton
    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Guruhga yuborish", callback_data="report_weekly_send")],
            kb.menu_button(),
        ])
    )


@role_required("super")
async def report_weekly_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hisobotni guruhga yuboradi."""
    query = update.callback_query
    await query.answer()
    text = await _build_weekly_text()
    from group import send_weekly_report
    await send_weekly_report(context.bot, text)
    await query.edit_message_text(
        text + "\n\n✅ Guruhga yuborildi.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.menu_button()])
    )


@role_required("super", "admin")
async def report_dep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    dep_id = db_user.get("dep_id")
    if db_user["role"] == "super":
        await stats_global(update, context)
        return
    if not dep_id:
        await query.edit_message_text("🚫 Bo'lim biriktirilmagan.", reply_markup=InlineKeyboardMarkup([kb.menu_button()]))
        return
    dep = await db.get_department(dep_id)
    stats = await db.get_stats_by_dep(dep_id)
    text = _stats_text(stats, f"📈 {dep['emoji']} {dep['name']} hisoboti")
    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.menu_button()])
    )
