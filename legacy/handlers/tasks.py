from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler as CQH
import db
import keyboards as kb
import group
import calendar_kb as cal
from handlers.common import cancel_conv
from decorators import role_required, any_role

(
    TASK_TYPE,      # Super: vazifa turi
    TASK_SEL_PROJ,  # Super: loyiha tanlash
    TASK_SEL_DEP,   # (zaxira, eski compat)
    TASK_SEL_USER,  # Admin: mas'ul tanlash
    TASK_NAME,
    TASK_DESC,
    TASK_DEADLINE,
    TASK_SEL_DEPS,  # Super: ko'p bo'lim tanlash
    TASK_WORK_DESC, # Super: har bo'lim uchun tavsif
    TASK_EDIT_FIELD,
    TASK_EDIT_VALUE,
) = range(11)

REMINDER_TASK_ID, REMINDER_DATE = range(100, 102)

PTASK_NAME, PTASK_DESC, PTASK_DEADLINE = range(200, 203)


def _status_icon(s):
    return {"faol": "🔄", "bajarildi": "✅", "kechikdi": "⚠️"}.get(s, "❓")


def _fmt_task(t, dep=None, masul=None, creator=None, task_deps_list=None):
    is_multi = t["dep_id"] == "multi"
    if dep:
        dep_text = f"{dep['emoji']} {dep['name']}"
    elif is_multi and task_deps_list:
        dep_text = f"{len(task_deps_list)} ta bo'lim"
    else:
        dep_text = "—"

    masul_text = masul["name"] if masul else "—"
    creator_text = creator["name"] if creator else "—"
    task_type = t["type"] or "standalone"
    if task_type == "personal":
        type_icon = "👤"
    elif task_type == "project":
        type_icon = "📁"
    else:
        type_icon = "📋"
    locked_icon = " 🔒" if t["is_locked"] else ""
    personal_badge = "  <i>[Shaxsiy vazifa]</i>" if task_type == "personal" else ""

    text = (
        f"{_status_icon(t['status'])} {type_icon} <b>Vazifa #{t['id']}</b>{locked_icon}{personal_badge}\n"
        f"📝 {t['name']}\n"
    )
    if t["description"]:
        text += f"📄 {t['description']}\n"
    text += (
        f"🏢 Bo'lim: {dep_text}\n"
        f"👤 Mas'ul: {masul_text}\n"
        f"🧑‍💼 Qo'ygan: {creator_text}\n"
        f"⏰ Muddat: {t['deadline'] or '—'}\n"
        f"📌 Holat: {t['status']}"
    )
    return text


def _cleanup_task_data(context):
    for k in [
        "new_task_dep", "new_task_masul", "new_task_name", "new_task_desc",
        "new_task_deadline", "new_task_type", "new_task_project_id",
        "new_task_is_locked", "sel_deps", "task_work_dep_list",
        "task_work_idx", "task_work_descs", "creator_role",
    ]:
        context.user_data.pop(k, None)


# ─── LIST ───────────────────────────────────────────────────────

def _parse_list_cb(data: str):
    """'dep_tasks:faol:1' → ('faol', 1);  'dep_tasks' → ('all', 0)"""
    parts = data.split(":")
    if len(parts) >= 3:
        return parts[1], int(parts[2])
    return "all", 0


@role_required("super", "admin")
async def dep_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    status_filter, page = _parse_list_cb(query.data)

    if db_user["role"] == "super":
        tasks = await db.get_all_tasks()
        title = "Barcha vazifalar"
    else:
        dep_id = db_user.get("dep_id")
        if not dep_id:
            await query.edit_message_text("🚫 Sizga bo'lim biriktirilmagan.", reply_markup=InlineKeyboardMarkup([kb.menu_button()]))
            return
        tasks = await db.get_tasks_by_dep(dep_id)
        dep = await db.get_department(dep_id)
        title = f"{dep['emoji']} {dep['name']} vazifalari"

    tasks = [dict(t) for t in tasks]

    if not tasks:
        await query.edit_message_text("📋 Vazifalar yo'q.", reply_markup=InlineKeyboardMarkup([kb.menu_button()]))
        return

    await query.edit_message_text(
        kb.task_list_paged_text(tasks, page, status_filter, title),
        parse_mode="HTML",
        reply_markup=kb.task_list_paged_kb(tasks, page, status_filter, "dep_tasks"),
    )


# ─── MY TASKS ───────────────────────────────────────────────────

@any_role
async def my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    status_filter, page = _parse_list_cb(query.data)

    tasks = await db.get_tasks_by_user(db_user["id"])
    tasks = [dict(t) for t in tasks]

    if not tasks:
        await query.edit_message_text("📁 Hozircha vazifalaringiz yo'q.", reply_markup=InlineKeyboardMarkup([kb.menu_button()]))
        return

    await query.edit_message_text(
        kb.task_list_paged_text(tasks, page, status_filter, "Mening vazifalarim"),
        parse_mode="HTML",
        reply_markup=kb.task_list_paged_kb(tasks, page, status_filter, "my_tasks"),
    )


# ─── VIEW ───────────────────────────────────────────────────────

@any_role
async def task_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split(":")[1])
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))

    t = await db.get_task(task_id)
    if not t:
        await query.edit_message_text("❌ Vazifa topilmadi.", reply_markup=InlineKeyboardMarkup([kb.menu_button()]))
        return

    is_multi = t["dep_id"] == "multi"
    task_deps_list = await db.get_task_deps(task_id) if is_multi else []

    if not is_multi and t["dep_id"]:
        dep = await db.get_department(t["dep_id"])
        masul = await db.get_user(t["masul_id"]) if t["masul_id"] else None
    else:
        dep = None
        masul = None
    creator = await db.get_user(t["created_by"])

    role = db_user["role"]
    is_masul = t["masul_id"] == db_user["id"]
    dep_match = db_user.get("dep_id") == t["dep_id"]
    is_personal_owner = t["type"] == "personal" and t["created_by"] == db_user["id"]

    text = _fmt_task(t, dep, masul, creator, task_deps_list)

    if is_multi and task_deps_list:
        text += "\n\n<b>Bo'limlar:</b>"
        for td in task_deps_list:
            td_dep = await db.get_department(td["dep_id"])
            td_worker = await db.get_user(td["worker_id"]) if td["worker_id"] else None
            si = {"jarayonda": "🔄", "bajarildi": "✅"}.get(td["status"], "⏳")
            worker_text = td_worker["name"] if td_worker else "belgilanmagan"
            text += f"\n  {si} {td_dep['emoji']} {td_dep['name']}: {td['work_desc'] or '—'} | 👤 {worker_text}"

    if is_multi:
        buttons = []
        if role == "super":
            if t["status"] != "bajarildi":
                buttons.append([InlineKeyboardButton("✅ Barchasi bajarildi", callback_data=f"task_done:{task_id}")])
            buttons.append([InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"task_edit:{task_id}")])
            buttons.append([InlineKeyboardButton("🗑 O'chirish", callback_data=f"task_del_confirm:{task_id}")])
        if db_user.get("dep_id"):
            my_td = next((td for td in task_deps_list if td["dep_id"] == db_user["dep_id"]), None)
            if my_td and my_td["status"] != "bajarildi":
                if role == "admin":
                    buttons.append([InlineKeyboardButton("👤 Xodim belgilash", callback_data=f"td_assign:{my_td['id']}")])
                if role in ("admin", "super") or my_td["worker_id"] == db_user["id"]:
                    buttons.append([InlineKeyboardButton("📌 Holat o'zgartirish", callback_data=f"td_status_menu:{my_td['id']}")])
                    buttons.append([InlineKeyboardButton("✅ Bajarildi", callback_data=f"td_done:{my_td['id']}")])
        buttons.append(kb.back_button("menu"))
        reply_markup = InlineKeyboardMarkup(buttons)
    else:
        reply_markup = kb.task_actions_kb(task_id, role, is_masul, dep_match, is_personal_owner)

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)


# ─── TASK DEP DONE ──────────────────────────────────────────────

@any_role
async def task_dep_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    td_id = int(query.data.split(":")[1])
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))

    td = await db.get_task_dep(td_id)
    if not td:
        await query.answer("❌ Topilmadi.", show_alert=True)
        return

    role = db_user["role"]
    if role == "worker" and td["worker_id"] != db_user["id"]:
        await query.answer("🚫 Ruxsat yo'q.", show_alert=True)
        return
    if role == "admin" and db_user.get("dep_id") != td["dep_id"]:
        await query.answer("🚫 Ruxsat yo'q.", show_alert=True)
        return

    await db.update_task_dep(td_id, status="bajarildi")
    await db.add_log(db_user["id"], f"Bo'lim ulushi bajarildi: td#{td_id}")

    all_deps = await db.get_task_deps(td["task_id"])
    all_done = all(d["status"] == "bajarildi" for d in all_deps)
    if all_done:
        await db.update_task(td["task_id"], status="bajarildi")

    await query.edit_message_text(
        "✅ Belgilandi." + (" Barcha bo'limlar tugatdi!" if all_done else ""),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 Vazifaga qaytish", callback_data=f"task_view:{td['task_id']}")],
            kb.menu_button(),
        ])
    )


# ─── TASK DEP ASSIGN WORKER ─────────────────────────────────────

@role_required("super", "admin")
async def task_dep_assign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    td_id = int(query.data.split(":")[1])
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))

    td = await db.get_task_dep(td_id)
    if not td:
        await query.answer("❌ Topilmadi.", show_alert=True)
        return
    if db_user["role"] == "admin" and db_user.get("dep_id") != td["dep_id"]:
        await query.answer("🚫 Ruxsat yo'q.", show_alert=True)
        return

    users = await db.get_users_by_dep(td["dep_id"])
    await query.edit_message_text(
        "👤 Xodimni tanlang:",
        reply_markup=kb.user_select_kb(users, f"td_worker:{td_id}", f"task_view:{td['task_id']}"),
    )


@role_required("super", "admin")
async def task_dep_assign_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # callback_data: td_worker:td_id:user_id
    parts = query.data.split(":")
    td_id = int(parts[1])
    worker_id_str = parts[2]

    td = await db.get_task_dep(td_id)
    if not td:
        await query.answer("❌ Topilmadi.", show_alert=True)
        return

    worker_id = None if worker_id_str == "none" else int(worker_id_str)
    await db.update_task_dep(td_id, worker_id=worker_id)

    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    await db.add_log(db_user["id"], f"Bo'lim xodimi belgilandi: td#{td_id}")

    task = await db.get_task(td["task_id"])
    dep = await db.get_department(td["dep_id"])
    worker = await db.get_user(worker_id) if worker_id else None
    await group.notify_dept_task_assigned(context.bot, task, dep, td["work_desc"] or "", worker)

    await query.edit_message_text(
        "✅ Xodim belgilandi, bo'lim topiciga xabar yuborildi.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 Vazifaga qaytish", callback_data=f"task_view:{td['task_id']}")],
            kb.menu_button(),
        ])
    )


# ─── STATUS CHANGE ──────────────────────────────────────────────

_STATUS_LABELS = {
    "faol":       "🆕 Yangi",
    "jarayonda":  "🔄 Jarayonda",
    "tekshiruvda": "🔍 Tekshiruvda",
    "bajarildi":  "✅ Bajarildi",
    "kechikdi":   "⚠️ Kechikdi",
}


@any_role
async def task_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Oddiy vazifa holati tanlash menyusi."""
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split(":")[1])
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    t = await db.get_task(task_id)
    if not t:
        await query.answer("❌ Topilmadi.", show_alert=True)
        return
    role = db_user["role"]
    is_masul = t["masul_id"] == db_user["id"]
    if role not in ("super", "admin") and not is_masul:
        await query.answer("🚫 Ruxsat yo'q.", show_alert=True)
        return
    await query.edit_message_text(
        f"📌 <b>Vazifa #{task_id}</b> — holat tanlang:\n(hozirgi: {_STATUS_LABELS.get(t['status'], t['status'])})",
        parse_mode="HTML",
        reply_markup=kb.task_status_select_kb(task_id, t["status"]),
    )


@any_role
async def task_set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Oddiy vazifa holatini saqlash."""
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    task_id, new_status = int(parts[1]), parts[2]
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    t = await db.get_task(task_id)
    if not t:
        await query.answer("❌ Topilmadi.", show_alert=True)
        return
    role = db_user["role"]
    is_masul = t["masul_id"] == db_user["id"]
    if role not in ("super", "admin") and not is_masul:
        await query.answer("🚫 Ruxsat yo'q.", show_alert=True)
        return
    await db.update_task(task_id, status=new_status)
    await db.add_log(db_user["id"], f"Vazifa holati: #{task_id} → {new_status}")
    dep = await db.get_department(t["dep_id"]) if t["dep_id"] and t["dep_id"] != "multi" else None
    masul = await db.get_user(t["masul_id"]) if t["masul_id"] else None
    await group.notify_task_status_changed(context.bot, t, dep, masul, db_user, new_status)
    label = _STATUS_LABELS.get(new_status, new_status)
    await query.edit_message_text(
        f"✅ Holat o'zgartirildi: {label}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 Ko'rish", callback_data=f"task_view:{task_id}")],
            kb.menu_button(),
        ])
    )


@any_role
async def td_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ko'p bo'limli vazifa — bo'lim ulushi holat tanlash."""
    query = update.callback_query
    await query.answer()
    td_id = int(query.data.split(":")[1])
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    td = await db.get_task_dep(td_id)
    if not td:
        await query.answer("❌ Topilmadi.", show_alert=True)
        return
    role = db_user["role"]
    if role not in ("super", "admin") and td["worker_id"] != db_user["id"]:
        await query.answer("🚫 Ruxsat yo'q.", show_alert=True)
        return
    dep = await db.get_department(td["dep_id"])
    await query.edit_message_text(
        f"📌 <b>{dep['emoji']} {dep['name']}</b> — holat tanlang:\n(hozirgi: {_STATUS_LABELS.get(td['status'], td['status'])})",
        parse_mode="HTML",
        reply_markup=kb.td_status_select_kb(td_id, td["status"], td["task_id"]),
    )


@any_role
async def td_set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bo'lim ulushi holatini saqlash."""
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    td_id, new_status = int(parts[1]), parts[2]
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    td = await db.get_task_dep(td_id)
    if not td:
        await query.answer("❌ Topilmadi.", show_alert=True)
        return
    role = db_user["role"]
    if role not in ("super", "admin") and td["worker_id"] != db_user["id"]:
        await query.answer("🚫 Ruxsat yo'q.", show_alert=True)
        return
    await db.update_task_dep(td_id, status=new_status)
    await db.add_log(db_user["id"], f"Bo'lim ulushi holati: td#{td_id} → {new_status}")
    if new_status == "bajarildi":
        all_deps = await db.get_task_deps(td["task_id"])
        if all(d["status"] == "bajarildi" for d in all_deps):
            await db.update_task(td["task_id"], status="bajarildi")
    dep = await db.get_department(td["dep_id"])
    task = await db.get_task(td["task_id"])
    await group.notify_task_status_changed(context.bot, task, dep, None, db_user, new_status)
    label = _STATUS_LABELS.get(new_status, new_status)
    await query.edit_message_text(
        f"✅ Holat o'zgartirildi: {label}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 Vazifaga qaytish", callback_data=f"task_view:{td['task_id']}")],
            kb.menu_button(),
        ])
    )


# ─── CREATE ─────────────────────────────────────────────────────

@role_required("super", "admin")
async def task_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    context.user_data["creator_role"] = db_user["role"]

    if db_user["role"] == "super":
        await query.edit_message_text(
            "📋 <b>Yangi vazifa</b>\n\nVazifa turini tanlang:",
            parse_mode="HTML",
            reply_markup=kb.task_type_kb(),
        )
        return TASK_TYPE
    else:
        dep_id = db_user.get("dep_id")
        if not dep_id:
            await query.edit_message_text("🚫 Sizga bo'lim biriktirilmagan.", reply_markup=InlineKeyboardMarkup([kb.menu_button()]))
            return ConversationHandler.END
        context.user_data["new_task_dep"] = dep_id
        context.user_data["new_task_is_locked"] = 0
        context.user_data["new_task_type"] = "standalone"
        users = await db.get_users_by_dep(dep_id)
        dep = await db.get_department(dep_id)
        await query.edit_message_text(
            f"📋 <b>{dep['emoji']} {dep['name']}</b>\n\nMas'ul xodimni tanlang:",
            parse_mode="HTML",
            reply_markup=kb.user_select_kb(users, "taskuser"),
        )
        return TASK_SEL_USER


async def task_type_sel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_type = query.data.split(":")[1]  # project | standalone
    context.user_data["new_task_type"] = task_type
    context.user_data["new_task_is_locked"] = 1

    if task_type == "project":
        projects = await db.get_all_projects()
        if not projects:
            await query.edit_message_text(
                "❌ Loyihalar yo'q. Avval loyiha yarating.",
                reply_markup=InlineKeyboardMarkup([kb.menu_button()])
            )
            return ConversationHandler.END
        await query.edit_message_text(
            "📁 Loyihani tanlang:",
            reply_markup=kb.project_select_kb(projects),
        )
        return TASK_SEL_PROJ

    await query.edit_message_text("✏️ <b>Vazifa nomini</b> kiriting:", parse_mode="HTML")
    return TASK_NAME


async def task_sel_proj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    project_id = int(query.data.split(":")[1])
    context.user_data["new_task_project_id"] = project_id
    await query.edit_message_text("✏️ <b>Vazifa nomini</b> kiriting:", parse_mode="HTML")
    return TASK_NAME


async def task_sel_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id_str = query.data.split(":")[1]
    context.user_data["new_task_masul"] = None if user_id_str == "none" else int(user_id_str)
    await query.edit_message_text("✏️ <b>Vazifa nomini</b> kiriting:", parse_mode="HTML")
    return TASK_NAME


async def task_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("❗ Nom kamida 3 harf:")
        return TASK_NAME
    context.user_data["new_task_name"] = name
    await update.message.reply_text(
        "📄 <b>Tavsif</b> kiriting yoki o'tkazish uchun <code>-</code>:",
        parse_mode="HTML",
    )
    return TASK_DESC


async def task_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = update.message.text.strip()
    context.user_data["new_task_desc"] = "" if desc == "-" else desc
    await update.message.reply_text(
        "⏰ <b>Muddat tanlang:</b>",
        parse_mode="HTML",
        reply_markup=cal.today_calendar(),
    )
    return TASK_DEADLINE


async def task_deadline_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, year, month = query.data.split(":")
    await query.edit_message_reply_markup(cal.build_calendar(int(year), int(month)))
    return TASK_DEADLINE


async def task_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    deadline = cal.parse_cal_data(query.data)
    role = context.user_data.get("creator_role", "admin")

    if role == "super":
        context.user_data["new_task_deadline"] = deadline
        deps = await db.get_all_departments()
        context.user_data["sel_deps"] = set()
        await query.edit_message_text(
            "🏢 <b>Bo'limlar tanlang</b> (bir nechta bo'lishi mumkin):",
            parse_mode="HTML",
            reply_markup=kb.dep_multiselect_kb(deps, set()),
        )
        return TASK_SEL_DEPS

    # Admin: save directly
    dep_id = context.user_data["new_task_dep"]
    masul_id = context.user_data.get("new_task_masul")
    name = context.user_data["new_task_name"]
    desc = context.user_data["new_task_desc"]
    created_by = update.effective_user.id

    task_id = await db.create_task(name, desc, dep_id, masul_id, created_by, deadline)
    await db.add_log(created_by, f"Vazifa qo'shildi: #{task_id} {name}")

    task = await db.get_task(task_id)
    dep = await db.get_department(dep_id)
    masul = await db.get_user(masul_id) if masul_id else None
    await group.notify_new_task(context.bot, task, dep, masul)

    if deadline:
        from datetime import date, timedelta
        try:
            remind_date = date.fromisoformat(deadline) - timedelta(days=1)
            await db.create_reminder(task_id, f"{remind_date}T09:00:00")
        except Exception:
            pass

    _cleanup_task_data(context)
    await query.edit_message_text(
        f"✅ <b>Vazifa #{task_id} qo'shildi!</b>\n📝 {name}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 Ko'rish", callback_data=f"task_view:{task_id}")],
            kb.menu_button(),
        ])
    )
    return ConversationHandler.END


# ─── MULTI-DEPT SELECTION ────────────────────────────────────────

async def task_dep_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dep_id = query.data.split(":")[1]
    sel = context.user_data.setdefault("sel_deps", set())
    if dep_id in sel:
        sel.discard(dep_id)
    else:
        sel.add(dep_id)
    deps = await db.get_all_departments()
    await query.edit_message_reply_markup(kb.dep_multiselect_kb(deps, sel))
    return TASK_SEL_DEPS


async def task_dep_sel_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    sel = context.user_data.get("sel_deps", set())
    if not sel:
        await query.answer("⚠️ Kamida bitta bo'lim tanlang!", show_alert=True)
        return TASK_SEL_DEPS
    await query.answer()
    context.user_data["task_work_dep_list"] = list(sel)
    context.user_data["task_work_idx"] = 0
    context.user_data["task_work_descs"] = {}
    await _ask_work_desc(query, context)
    return TASK_WORK_DESC


async def _ask_work_desc(qm, context):
    dep_list = context.user_data["task_work_dep_list"]
    idx = context.user_data["task_work_idx"]
    dep = await db.get_department(dep_list[idx])
    total = len(dep_list)
    text = (
        f"📝 <b>{idx+1}/{total} — {dep['emoji']} {dep['name']}</b>\n\n"
        "Bu bo'lim uchun vazifa tavsifini kiriting\n"
        "(<code>-</code> — bo'sh qoldirish):"
    )
    if hasattr(qm, "edit_message_text"):
        await qm.edit_message_text(text, parse_mode="HTML")
    else:
        await qm.reply_text(text, parse_mode="HTML")


async def task_work_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    work_desc = "" if text == "-" else text
    dep_list = context.user_data["task_work_dep_list"]
    idx = context.user_data["task_work_idx"]
    context.user_data["task_work_descs"][dep_list[idx]] = work_desc
    idx += 1
    context.user_data["task_work_idx"] = idx

    if idx < len(dep_list):
        await _ask_work_desc(update.message, context)
        return TASK_WORK_DESC

    return await _save_multidept_task(update.message, context, update.effective_user.id)


async def _save_multidept_task(msg, context, creator_id):
    name = context.user_data["new_task_name"]
    desc = context.user_data["new_task_desc"]
    deadline = context.user_data["new_task_deadline"]
    task_type = context.user_data.get("new_task_type", "standalone")
    project_id = context.user_data.get("new_task_project_id")
    dep_list = context.user_data["task_work_dep_list"]
    work_descs = context.user_data["task_work_descs"]

    task_id = await db.create_task(name, desc, "multi", None, creator_id, deadline, project_id)
    await db.update_task(task_id, is_locked=1, **{"type": task_type})
    await db.add_log(creator_id, f"Ko'p bo'limli vazifa qo'shildi: #{task_id} {name}")

    task = await db.get_task(task_id)
    for dep_id in dep_list:
        work_desc = work_descs.get(dep_id, "")
        await db.create_task_dep(task_id, dep_id, work_desc)
        dep = await db.get_department(dep_id)
        await group.notify_dept_task_assigned(context.bot, task, dep, work_desc)

    if deadline:
        from datetime import date, timedelta
        try:
            remind_date = date.fromisoformat(deadline) - timedelta(days=1)
            await db.create_reminder(task_id, f"{remind_date}T09:00:00")
        except Exception:
            pass

    _cleanup_task_data(context)
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("👁 Ko'rish", callback_data=f"task_view:{task_id}")],
        kb.menu_button(),
    ])
    text = f"✅ <b>Vazifa #{task_id} qo'shildi!</b>\n📝 {name}\n🏢 {len(dep_list)} ta bo'lim"
    if hasattr(msg, "reply_text"):
        await msg.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await msg.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
    return ConversationHandler.END


# ─── DONE ───────────────────────────────────────────────────────

@any_role
async def task_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split(":")[1])
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    t = await db.get_task(task_id)
    if not t:
        await query.edit_message_text("❌ Vazifa topilmadi.")
        return
    if t["status"] == "bajarildi":
        await query.answer("Bu vazifa allaqachon bajarilgan.", show_alert=True)
        return

    role = db_user["role"]
    is_masul = t["masul_id"] == db_user["id"]
    if role not in ("super", "admin") and not is_masul:
        await query.answer("🚫 Faqat mas'ul yoki admin belgilashi mumkin.", show_alert=True)
        return

    await db.update_task(task_id, status="bajarildi")
    await db.add_log(db_user["id"], f"Vazifa bajarildi: #{task_id}")

    dep = await db.get_department(t["dep_id"]) if t["dep_id"] and t["dep_id"] != "multi" else None
    masul = await db.get_user(t["masul_id"]) if t["masul_id"] else None
    creator = await db.get_user(t["created_by"])
    await group.notify_task_done(context.bot, t, dep, masul, creator)

    await query.edit_message_text(
        f"✅ <b>Vazifa #{task_id} bajarildi!</b>\n📝 {t['name']}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.menu_button()])
    )


# ─── DELETE ─────────────────────────────────────────────────────

@any_role
async def task_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split(":")[1])
    t = await db.get_task(task_id)
    if not t:
        await query.edit_message_text("❌ Vazifa topilmadi.")
        return
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    role = db_user["role"]
    is_personal_owner = t["type"] == "personal" and t["created_by"] == db_user["id"]
    if role == "admin" and db_user.get("dep_id") != t["dep_id"] and not is_personal_owner:
        await query.answer("🚫 Ruxsat yo'q — boshqa bo'lim vazifasi.", show_alert=True)
        return
    if role == "worker" and not is_personal_owner:
        await query.answer("🚫 Ruxsat yo'q.", show_alert=True)
        return
    await query.edit_message_text(
        f"⚠️ <b>Vazifa #{task_id}</b> — <i>{t['name']}</i> ni o'chirishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=kb.confirm_kb(f"task_del:{task_id}", f"task_view:{task_id}"),
    )


@any_role
async def task_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split(":")[1])
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    t = await db.get_task(task_id)
    if not t:
        await query.edit_message_text("❌ Vazifa topilmadi.")
        return
    role = db_user["role"]
    is_personal_owner = t["type"] == "personal" and t["created_by"] == db_user["id"]
    if role == "admin" and db_user.get("dep_id") != t["dep_id"] and not is_personal_owner:
        await query.answer("🚫 Ruxsat yo'q.", show_alert=True)
        return
    if role == "worker" and not is_personal_owner:
        await query.answer("🚫 Ruxsat yo'q.", show_alert=True)
        return
    await db.delete_task(task_id)
    await db.add_log(db_user["id"], f"Vazifa o'chirildi: #{task_id}")
    await query.edit_message_text(
        f"🗑 Vazifa #{task_id} o'chirildi.",
        reply_markup=InlineKeyboardMarkup([kb.menu_button()])
    )


# ─── EDIT ───────────────────────────────────────────────────────

@role_required("super", "admin")
async def task_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split(":")[1])
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    t = await db.get_task(task_id)
    if not t:
        await query.edit_message_text("❌ Vazifa topilmadi.")
        return ConversationHandler.END
    if db_user["role"] == "admin" and db_user.get("dep_id") != t["dep_id"]:
        await query.answer("🚫 Ruxsat yo'q.", show_alert=True)
        return ConversationHandler.END

    is_locked = t["is_locked"]
    if is_locked and db_user["role"] != "super":
        await query.answer("🔒 Deadline qulflangan — faqat super admin o'zgartira oladi.", show_alert=True)
        return ConversationHandler.END

    context.user_data["edit_task_id"] = task_id

    buttons = [
        [InlineKeyboardButton("📝 Nom", callback_data="taskedit:name")],
        [InlineKeyboardButton("📄 Tavsif", callback_data="taskedit:description")],
    ]
    if not is_locked or db_user["role"] == "super":
        buttons.append([InlineKeyboardButton("⏰ Muddat", callback_data="taskedit:deadline")])
    buttons.append(kb.back_button(f"task_view:{task_id}"))

    await query.edit_message_text(
        f"✏️ Vazifa #{task_id}: <b>{t['name']}</b>\n\nNimani tahrirlamoqchisiz?",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return TASK_EDIT_FIELD


async def task_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    field = query.data.split(":")[1]
    context.user_data["edit_task_field"] = field
    if field == "deadline":
        await query.edit_message_text(
            "⏰ <b>Yangi muddat tanlang:</b>",
            parse_mode="HTML",
            reply_markup=cal.today_calendar(),
        )
    else:
        prompts = {"name": "📝 Yangi nom kiriting:", "description": "📄 Yangi tavsif kiriting:"}
        await query.edit_message_text(prompts.get(field, "Yangi qiymat:"))
    return TASK_EDIT_VALUE


async def task_edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task_id = context.user_data["edit_task_id"]
    field = context.user_data["edit_task_field"]
    caller_id = update.effective_user.id

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        if query.data.startswith("cal_nav:"):
            _, year, month = query.data.split(":")
            await query.edit_message_reply_markup(cal.build_calendar(int(year), int(month)))
            return TASK_EDIT_VALUE
        value = cal.parse_cal_data(query.data)
        await db.update_task(task_id, **{field: value})
        await db.add_log(caller_id, f"Vazifa tahrirlandi: #{task_id} {field}")
        await query.edit_message_text(
            f"✅ Vazifa #{task_id} yangilandi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👁 Ko'rish", callback_data=f"task_view:{task_id}")],
                kb.menu_button(),
            ])
        )
        return ConversationHandler.END

    value = update.message.text.strip()
    await db.update_task(task_id, **{field: value})
    await db.add_log(caller_id, f"Vazifa tahrirlandi: #{task_id} {field}")
    await update.message.reply_text(
        f"✅ Vazifa #{task_id} yangilandi.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 Ko'rish", callback_data=f"task_view:{task_id}")],
            kb.menu_button(),
        ])
    )
    return ConversationHandler.END


# ─── REMINDER SET ───────────────────────────────────────────────

@any_role
async def reminder_set_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))
    tasks = await db.get_tasks_by_user(db_user["id"])
    active = [t for t in tasks if t["status"] == "faol"]
    if not active:
        await query.edit_message_text("📁 Faol vazifalaringiz yo'q.", reply_markup=InlineKeyboardMarkup([kb.menu_button()]))
        return ConversationHandler.END
    await query.edit_message_text(
        "🔔 Eslatma o'rnatish uchun vazifani tanlang:",
        reply_markup=kb.task_list_kb(active, "menu"),
    )
    return REMINDER_TASK_ID


async def reminder_task_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    task_id = int(query.data.split(":")[1])
    context.user_data["reminder_task_id"] = task_id
    await query.edit_message_text("📅 Eslatma sanasi va vaqtini kiriting (YYYY-MM-DD HH:MM):")
    return REMINDER_DATE


async def reminder_date_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import re
    text = update.message.text.strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", text):
        await update.message.reply_text("❗ Format: 2025-12-31 09:00:")
        return REMINDER_DATE
    task_id = context.user_data["reminder_task_id"]
    await db.create_reminder(task_id, text.replace(" ", "T") + ":00")
    await update.message.reply_text(
        f"🔔 Eslatma o'rnatildi: {text}",
        reply_markup=InlineKeyboardMarkup([kb.menu_button()])
    )
    return ConversationHandler.END


# ─── PERSONAL TASK CREATION ─────────────────────────────────────

@any_role
async def personal_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👤 <b>Shaxsiy vazifa qo'shish</b>\n\nVazifa nomini kiriting:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Bekor qilish", callback_data="menu")
        ]]),
    )
    return PTASK_NAME


async def ptask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not name:
        await update.message.reply_text("❗ Nom bo'sh bo'lmasin, qayta kiriting:")
        return PTASK_NAME
    context.user_data["ptask_name"] = name
    await update.message.reply_text(
        "📄 Tavsif kiriting yoki o'tkazib yuboring:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data="ptask_skip_desc")
        ]]),
    )
    return PTASK_DESC


async def ptask_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import date as _date
    today = _date.today()
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data["ptask_desc"] = ""
        msg = update.callback_query.message
        await msg.edit_text(
            "📅 Muddat (deadline) tanlang:",
            reply_markup=cal.build_calendar(today.year, today.month),
        )
    else:
        context.user_data["ptask_desc"] = update.message.text.strip()
        await update.message.reply_text(
            "📅 Muddat (deadline) tanlang:",
            reply_markup=cal.build_calendar(today.year, today.month),
        )
    return PTASK_DEADLINE


async def ptask_deadline_nav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, yyyy, mm = query.data.split(":")
    await query.edit_message_reply_markup(cal.build_calendar(int(yyyy), int(mm)))
    return PTASK_DEADLINE


async def ptask_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, yyyy, mm, dd = query.data.split(":")
    deadline = f"{yyyy}-{mm}-{dd}"
    db_user = context.user_data.get("db_user") or dict(await db.get_user(update.effective_user.id))

    name = context.user_data["ptask_name"]
    desc = context.user_data.get("ptask_desc", "")
    dep_id = db_user.get("dep_id") or "personal"
    user_id = db_user["id"]

    task_id = await db.create_task(
        name, desc, dep_id, user_id, user_id, deadline,
        task_type="personal"
    )
    await db.add_log(user_id, f"Shaxsiy vazifa qo'shildi: #{task_id} {name}")

    for k in ("ptask_name", "ptask_desc"):
        context.user_data.pop(k, None)

    await query.edit_message_text(
        f"✅ <b>Shaxsiy vazifa #{task_id} qo'shildi!</b>\n👤 {name}\n⏰ Muddat: {deadline}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👁 Ko'rish", callback_data=f"task_view:{task_id}")],
            kb.menu_button(),
        ]),
    )
    return ConversationHandler.END


# ─── CONVERSATION HANDLERS ───────────────────────────────────────

def get_task_create_conv():
    return ConversationHandler(
        entry_points=[CQH(task_create_start, pattern="^task_create$")],
        states={
            TASK_TYPE:      [CQH(task_type_sel, pattern="^tasktype:")],
            TASK_SEL_PROJ:  [CQH(task_sel_proj, pattern="^taskproj:")],
            TASK_SEL_USER:  [CQH(task_sel_user, pattern="^taskuser:")],
            TASK_NAME:      [MessageHandler(filters.TEXT & ~filters.COMMAND, task_name)],
            TASK_DESC:      [MessageHandler(filters.TEXT & ~filters.COMMAND, task_desc)],
            TASK_DEADLINE: [
                CQH(task_deadline_nav, pattern="^cal_nav:"),
                CQH(task_deadline, pattern="^cal:"),
                CQH(cancel_conv, pattern="^cal_ignore$"),
            ],
            TASK_SEL_DEPS: [
                CQH(task_dep_toggle, pattern="^dep_toggle:"),
                CQH(task_dep_sel_done, pattern="^dep_sel_done$"),
            ],
            TASK_WORK_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_work_desc)],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )


def get_task_edit_conv():
    return ConversationHandler(
        entry_points=[CQH(task_edit_start, pattern="^task_edit:")],
        states={
            TASK_EDIT_FIELD: [CQH(task_edit_field, pattern="^taskedit:")],
            TASK_EDIT_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, task_edit_value),
                CQH(task_edit_value, pattern="^cal_nav:"),
                CQH(task_edit_value, pattern="^cal:"),
            ],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )


def get_reminder_conv():
    return ConversationHandler(
        entry_points=[CQH(reminder_set_start, pattern="^reminder_set$")],
        states={
            REMINDER_TASK_ID: [CQH(reminder_task_selected, pattern="^task_view:")],
            REMINDER_DATE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, reminder_date_set)],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )


def get_personal_task_conv():
    return ConversationHandler(
        entry_points=[CQH(personal_task_start, pattern="^task_personal_create$")],
        states={
            PTASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ptask_name)],
            PTASK_DESC: [
                CQH(ptask_desc, pattern="^ptask_skip_desc$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ptask_desc),
            ],
            PTASK_DEADLINE: [
                CQH(ptask_deadline_nav, pattern="^cal_nav:"),
                CQH(ptask_deadline, pattern="^cal:"),
            ],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )
