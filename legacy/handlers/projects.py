from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler as CQH
import db
import keyboards as kb
import group
import calendar_kb as cal
from handlers.common import cancel_conv
from decorators import role_required

(
    PROJ_NAME,
    PROJ_DESC,
    PROJ_STATUS,
    STAGE_SEQ, STAGE_DEP, STAGE_DESC, STAGE_USER, STAGE_DEADLINE, STAGE_MORE,
    STAGE_EDIT_FIELD, STAGE_EDIT_VALUE,
) = range(11)


def _progress(stages):
    total = len(stages)
    if not total:
        return 0
    done = sum(1 for s in stages if s["status"] == "done")
    return int(done / total * 100)


def _fmt_project(p, stages):
    status_map = {
        "rejalashtirilgan": "🔵 Rejalashtirilgan",
        "jarayonda": "🟡 Jarayonda",
        "yakunlangan": "🟢 Yakunlangan",
        "toxtatilgan": "🔴 To'xtatilgan",
        "faol": "🔄 Faol",
        "tugadi": "✅ Tugadi",
    }
    proj_status = p["proj_status"] or p["status"]
    status_text = status_map.get(proj_status, proj_status)
    prog = _progress(stages)
    text = (
        f"📁 <b>Loyiha #{p['id']}: {p['name']}</b>\n"
        f"📌 Holat: {status_text}\n"
        f"📊 Progress: {prog}%\n"
        f"📋 Bosqichlar: {len(stages)} ta"
    )
    if p["description"]:
        text += f"\n📝 {p['description']}"
    return text


def _fmt_stages(stages):
    from itertools import groupby
    lines = []
    for seq, group_iter in groupby(stages, key=lambda s: s["seq"]):
        group_stages = list(group_iter)
        if len(group_stages) > 1:
            lines.append(f"  <b>Navbat {seq}</b> (parallel):")
        else:
            lines.append(f"  <b>Navbat {seq}:</b>")
        for s in group_stages:
            icon = {"wait": "⏳", "active": "🔄", "done": "✅"}.get(s["status"], "❓")
            lines.append(f"    {icon} {s['description'][:40]} | {s['dep_id']} | {s['deadline'] or '—'}")
    return "\n".join(lines)


# ─── LIST ────────────────────────────────────────────────────

@role_required("super")
async def proj_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = 0
    if query.data.startswith("proj_page:"):
        page = int(query.data.split(":")[1])

    projects = await db.get_all_projects()
    if not projects:
        await query.edit_message_text(
            "📂 Hozircha loyihalar yo'q.",
            reply_markup=InlineKeyboardMarkup([
                [kb.InlineKeyboardButton("➕ Loyiha qʻo'shish", callback_data="proj_create")],
                kb.menu_button(),
            ])
        )
        return
    await query.edit_message_text(
        kb.proj_list_text(projects, page),
        parse_mode="HTML",
        reply_markup=kb.project_list_kb(projects, page),
    )


# ─── VIEW ────────────────────────────────────────────────────

@role_required("super")
async def proj_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":")[1])
    p = await db.get_project(project_id)
    if not p:
        await query.edit_message_text("❌ Loyiha topilmadi.", reply_markup=InlineKeyboardMarkup([kb.menu_button()]))
        return
    stages = await db.get_stages_by_project(project_id)
    await query.edit_message_text(
        _fmt_project(p, stages),
        parse_mode="HTML",
        reply_markup=kb.project_actions_kb(project_id, p["proj_status"] or p["status"]),
    )


# ─── STAGES VIEW ─────────────────────────────────────────────

@role_required("super")
async def proj_stages_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":")[1])
    p = await db.get_project(project_id)
    stages = await db.get_stages_by_project(project_id)
    if not stages:
        await query.edit_message_text(
            f"📋 <b>{p['name']}</b> — Bosqichlar yo'q.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [kb.InlineKeyboardButton("➕ Bosqich qo'shish", callback_data=f"stage_add:{project_id}")],
                kb.back_button(f"proj_view:{project_id}"),
            ])
        )
        return
    text = f"📋 <b>{p['name']}</b> — Bosqichlar:\n\n" + _fmt_stages(stages)
    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.stage_list_kb(stages, project_id),
    )


# ─── STAGE VIEW ──────────────────────────────────────────────

@role_required("super")
async def stage_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stage_id = int(query.data.split(":")[1])
    s = await db.get_stage(stage_id)
    if not s:
        await query.edit_message_text("❌ Bosqich topilmadi.")
        return
    dep = await db.get_department(s["dep_id"])
    masul = await db.get_user(s["masul_id"]) if s["masul_id"] else None
    icon = {"wait": "⏳", "active": "🔄", "done": "✅"}.get(s["status"], "❓")
    text = (
        f"{icon} <b>Bosqich #{s['id']}</b>\n"
        f"📋 Navbat: {s['seq']}\n"
        f"🏢 Bo'lim: {dep['emoji']} {dep['name']}\n"
        f"📝 Tavsif: {s['description']}\n"
        f"👤 Mas'ul: {masul['name'] if masul else '—'}\n"
        f"⏰ Muddat: {s['deadline'] or '—'}\n"
        f"📌 Holat: {s['status']}"
    )
    await query.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=kb.stage_actions_kb(stage_id, s["status"], s["project_id"]),
    )


# ─── CREATE PROJECT (conversation) ───────────────────────────

@role_required("super")
async def proj_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📁 <b>Yangi loyiha</b>\n\nLoyiha nomini kiriting:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.back_button()]),
    )
    return PROJ_NAME


async def proj_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("❗ Nom kamida 3 harf:")
        return PROJ_NAME
    context.user_data["new_proj_name"] = name
    await update.message.reply_text(
        "📝 <b>Loyiha tasnifi</b> (qisqacha tavsif) kiriting\n"
        "yoki o'tkazish uchun <code>-</code>:",
        parse_mode="HTML",
    )
    return PROJ_DESC


async def proj_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    context.user_data["new_proj_desc"] = "" if desc == "-" else desc
    await update.message.reply_text(
        "📌 <b>Loyiha holati</b> — tanlang:",
        parse_mode="HTML",
        reply_markup=kb.proj_status_kb(),
    )
    return PROJ_STATUS


async def proj_status_sel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    status = query.data.split(":")[1]
    name = context.user_data["new_proj_name"]
    desc = context.user_data.get("new_proj_desc", "")
    creator_id = update.effective_user.id

    project_id = await db.create_project(name, creator_id, desc, status)
    await db.add_log(creator_id, f"Loyiha yaratildi: #{project_id} {name}")

    for k in ["new_proj_name", "new_proj_desc"]:
        context.user_data.pop(k, None)

    await query.edit_message_text(
        f"✅ <b>Loyiha #{project_id}: {name}</b> yaratildi!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👁 Ko'rish",              callback_data=f"proj_view:{project_id}")],
            [kb.InlineKeyboardButton("➕ Bosqich qo'shish",     callback_data=f"stage_add:{project_id}")],
            kb.menu_button(),
        ])
    )
    return ConversationHandler.END


async def stage_seq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or int(text) < 1:
        await update.message.reply_text("❗ Musbat raqam kiriting:")
        return STAGE_SEQ
    context.user_data["new_stage_seq"] = int(text)
    deps = await db.get_all_departments()
    await update.message.reply_text(
        "🏢 Bo'lim tanlang:",
        reply_markup=kb.dep_select_kb(deps, "stagedep"),
    )
    return STAGE_DEP


async def stage_dep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dep_id = query.data.split(":")[1]
    context.user_data["new_stage_dep"] = dep_id
    await query.edit_message_text("📝 Bosqich tavsifini kiriting:")
    return STAGE_DESC


async def stage_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    context.user_data["new_stage_desc"] = desc
    dep_id = context.user_data["new_stage_dep"]
    users = await db.get_users_by_dep(dep_id)
    await update.message.reply_text(
        "👤 Mas'ul xodimni tanlang:",
        reply_markup=kb.user_select_kb(users, "stageuser"),
    )
    return STAGE_USER


async def stage_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid_str = query.data.split(":")[1]
    context.user_data["new_stage_masul"] = None if uid_str == "none" else int(uid_str)
    await query.edit_message_text(
        "⏰ <b>Muddat tanlang:</b>",
        parse_mode="HTML",
        reply_markup=cal.today_calendar(),
    )
    return STAGE_DEADLINE


async def stage_deadline_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, year, month = query.data.split(":")
    await query.edit_message_reply_markup(cal.build_calendar(int(year), int(month)))
    return STAGE_DEADLINE


async def stage_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    deadline = cal.parse_cal_data(query.data)

    project_id = context.user_data["new_project_id"]
    seq = context.user_data["new_stage_seq"]
    dep_id = context.user_data["new_stage_dep"]
    desc = context.user_data["new_stage_desc"]
    masul_id = context.user_data["new_stage_masul"]

    stage_id = await db.create_stage(project_id, seq, dep_id, desc, masul_id, deadline)
    stages = context.user_data.setdefault("new_project_stages", [])
    stages.append(stage_id)

    await query.edit_message_text(
        f"✅ Bosqich qo'shildi (navbat {seq}).\n\n"
        "Yana bosqich qo'shish yoki saqlash?",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("➕ Yana bosqich", callback_data="stage_add_more")],
            [kb.InlineKeyboardButton("💾 Saqlash va tugatish", callback_data="stage_save_done")],
        ])
    )
    return STAGE_MORE


async def stage_add_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📋 Keyingi bosqich uchun navbat raqamini kiriting:"
    )
    return STAGE_SEQ


async def stage_save_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = context.user_data.get("new_project_id")
    creator_id = update.effective_user.id
    await db.activate_first_stages(project_id)
    p = await db.get_project(project_id)
    stages = await db.get_stages_by_project(project_id)

    for k in ["new_project_id", "new_project_stages", "new_stage_seq",
              "new_stage_dep", "new_stage_desc", "new_stage_masul",
              "new_proj_name", "new_proj_desc"]:
        context.user_data.pop(k, None)

    await query.edit_message_text(
        f"🎉 <b>Loyiha #{project_id}: {p['name']}</b> tayyor!\n"
        f"📋 {len(stages)} ta bosqich, birinchi navbat faol.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👁 Ko'rish", callback_data=f"proj_view:{project_id}")],
            kb.menu_button(),
        ])
    )
    return ConversationHandler.END


# ─── ADD STAGE to existing project (conversation) ─────────────

@role_required("super")
async def stage_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":")[1])
    context.user_data["new_project_id"] = project_id
    context.user_data["adding_to_existing"] = True
    await query.edit_message_text(
        "📋 Navbat raqamini kiriting:"
    )
    return STAGE_SEQ


async def stage_save_done_existing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = context.user_data.get("new_project_id")
    await db.activate_first_stages(project_id)
    p = await db.get_project(project_id)
    for k in ["new_project_id", "adding_to_existing", "new_stage_seq",
              "new_stage_dep", "new_stage_desc", "new_stage_masul"]:
        context.user_data.pop(k, None)
    await query.edit_message_text(
        f"✅ Bosqich saqlandi.",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👁 Loyiha", callback_data=f"proj_view:{project_id}")],
            kb.menu_button(),
        ])
    )
    return ConversationHandler.END


# ─── STAGE DONE ───────────────────────────────────────────────

@role_required("super")
async def stage_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stage_id = int(query.data.split(":")[1])
    s = await db.get_stage(stage_id)
    if not s:
        await query.edit_message_text("❌ Bosqich topilmadi.")
        return
    if s["status"] != "active":
        await query.answer("Bu bosqich hali faol emas.", show_alert=True)
        return
    await db.update_stage(stage_id, status="done")
    caller_id = update.effective_user.id
    await db.add_log(caller_id, f"Bosqich tugadi: #{stage_id}")

    # Keyingi navbatni faollashtirish
    new_stages = await db.advance_project_stages(s["project_id"])
    p = await db.get_project(s["project_id"])

    if new_stages:
        # Guruhga xabar
        deps_map = {}
        users_map = {}
        for ns in new_stages:
            if ns["dep_id"] not in deps_map:
                deps_map[ns["dep_id"]] = await db.get_department(ns["dep_id"])
            if ns["masul_id"] and ns["masul_id"] not in users_map:
                users_map[ns["masul_id"]] = await db.get_user(ns["masul_id"])
        await group.notify_stage_activated(context.bot, new_stages, deps_map, users_map)
        msg = "✅ Bosqich tugadi! Keyingi navbat faollashdi."
    elif p["status"] == "tugadi":
        await group.notify_project_done(context.bot, p)
        msg = "🎉 Barcha bosqichlar tugadi! Loyiha yakunlandi."
    else:
        msg = "✅ Bosqich tugadi."

    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("📋 Bosqichlar", callback_data=f"proj_stages:{s['project_id']}")],
            kb.menu_button(),
        ])
    )


# ─── STAGE EDIT (conversation) ────────────────────────────────

@role_required("super")
async def stage_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    stage_id = int(query.data.split(":")[1])
    context.user_data["edit_stage_id"] = stage_id
    await query.edit_message_text(
        "✏️ Bosqichni tahrirlash — nimani o'zgartirmoqchisiz?",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("📝 Tavsif", callback_data="stageedit:description")],
            [kb.InlineKeyboardButton("⏰ Muddat", callback_data="stageedit:deadline")],
            kb.back_button(),
        ])
    )
    return STAGE_EDIT_FIELD


async def stage_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    field = query.data.split(":")[1]
    context.user_data["edit_stage_field"] = field
    if field == "deadline":
        await query.edit_message_text(
            "⏰ <b>Yangi muddat tanlang:</b>",
            parse_mode="HTML",
            reply_markup=cal.today_calendar(),
        )
    else:
        await query.edit_message_text("📝 Yangi tavsifni kiriting:")
    return STAGE_EDIT_VALUE


async def stage_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stage_id = context.user_data["edit_stage_id"]
    field = context.user_data["edit_stage_field"]
    caller_id = update.effective_user.id

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data.startswith("cal_nav:"):
            _, year, month = query.data.split(":")
            await query.edit_message_reply_markup(cal.build_calendar(int(year), int(month)))
            return STAGE_EDIT_VALUE
        value = cal.parse_cal_data(query.data)
        await db.update_stage(stage_id, **{field: value})
        await db.add_log(caller_id, f"Bosqich tahrirlandi: #{stage_id} {field}")
        await query.edit_message_text(
            "✅ Bosqich yangilandi.",
            reply_markup=InlineKeyboardMarkup([
                [kb.InlineKeyboardButton("👁 Ko'rish", callback_data=f"stage_view:{stage_id}")],
                kb.menu_button(),
            ])
        )
        return ConversationHandler.END

    value = update.message.text.strip()
    await db.update_stage(stage_id, **{field: value})
    await db.add_log(caller_id, f"Bosqich tahrirlandi: #{stage_id} {field}")
    await update.message.reply_text(
        "✅ Bosqich yangilandi.",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👁 Ko'rish", callback_data=f"stage_view:{stage_id}")],
            kb.menu_button(),
        ])
    )
    return ConversationHandler.END


# ─── STATUS CHANGE ────────────────────────────────────────────

_PROJ_STATUS_LABELS = {
    "rejalashtirilgan": "🔵 Rejalashtirilgan",
    "jarayonda":        "🟡 Jarayonda",
    "yakunlangan":      "🟢 Yakunlangan",
    "toxtatilgan":      "🔴 To'xtatilgan",
}


@role_required("super")
async def proj_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":")[1])
    p = await db.get_project(project_id)
    if not p:
        await query.answer("❌ Topilmadi.", show_alert=True)
        return
    current = p["proj_status"] or p["status"]
    await query.edit_message_text(
        f"📌 <b>Loyiha #{project_id}: {p['name']}</b>\n\nYangi holat tanlang:",
        parse_mode="HTML",
        reply_markup=kb.proj_status_change_kb(project_id, current),
    )


@role_required("super")
async def proj_set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    project_id, new_status = int(parts[1]), parts[2]
    p = await db.get_project(project_id)
    if not p:
        await query.answer("❌ Topilmadi.", show_alert=True)
        return
    await db.update_project(project_id, proj_status=new_status)
    await db.add_log(update.effective_user.id, f"Loyiha holati: #{project_id} → {new_status}")
    label = _PROJ_STATUS_LABELS.get(new_status, new_status)
    await query.edit_message_text(
        f"✅ Holat o'zgartirildi: {label}",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👁 Ko'rish", callback_data=f"proj_view:{project_id}")],
            kb.menu_button(),
        ])
    )


# ─── DELETE PROJECT ───────────────────────────────────────────

@role_required("super")
async def proj_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":")[1])
    p = await db.get_project(project_id)
    if not p:
        await query.edit_message_text("❌ Loyiha topilmadi.")
        return
    await query.edit_message_text(
        f"⚠️ <b>{p['name']}</b> loyihasini va barcha bosqichlarini o'chirishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=kb.confirm_kb(f"proj_del:{project_id}", f"proj_view:{project_id}"),
    )


@role_required("super")
async def proj_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":")[1])
    caller_id = update.effective_user.id
    p = await db.get_project(project_id)
    await db.delete_project(project_id)
    await db.add_log(caller_id, f"Loyiha o'chirildi: #{project_id} {p['name'] if p else ''}")
    await query.edit_message_text(
        "🗑 Loyiha o'chirildi.",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("🗂 Loyihalar", callback_data="proj_list")],
            kb.menu_button(),
        ])
    )


# ─── CONVERSATION HANDLERS ────────────────────────────────────

def get_proj_create_conv():
    return ConversationHandler(
        entry_points=[CQH(proj_create_start, pattern="^proj_create$")],
        states={
            PROJ_NAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, proj_name)],
            PROJ_DESC:   [MessageHandler(filters.TEXT & ~filters.COMMAND, proj_desc)],
            PROJ_STATUS: [CQH(proj_status_sel, pattern="^projstatus:")],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )


def get_stage_add_conv():
    return ConversationHandler(
        entry_points=[CQH(stage_add_start, pattern="^stage_add:")],
        states={
            STAGE_SEQ: [MessageHandler(filters.TEXT & ~filters.COMMAND, stage_seq)],
            STAGE_DEP: [CQH(stage_dep, pattern="^stagedep:")],
            STAGE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, stage_desc)],
            STAGE_USER: [CQH(stage_user, pattern="^stageuser:")],
            STAGE_DEADLINE: [
                CQH(stage_deadline_nav, pattern="^cal_nav:"),
                CQH(stage_deadline, pattern="^cal:"),
            ],
            STAGE_MORE: [
                CQH(stage_add_more, pattern="^stage_add_more$"),
                CQH(stage_save_done_existing, pattern="^stage_save_done$"),
            ],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )


def get_stage_edit_conv():
    return ConversationHandler(
        entry_points=[CQH(stage_edit_start, pattern="^stage_edit:")],
        states={
            STAGE_EDIT_FIELD: [CQH(stage_edit_field, pattern="^stageedit:")],
            STAGE_EDIT_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, stage_edit_value),
                CQH(stage_edit_value, pattern="^cal_nav:"),
                CQH(stage_edit_value, pattern="^cal:"),
            ],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )
