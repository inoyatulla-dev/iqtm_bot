from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler as CQH
import db
import keyboards as kb
from handlers.common import cancel_conv
from decorators import role_required

(
    DEP_ADD_ID, DEP_ADD_NAME, DEP_ADD_EMOJI,
    DEP_EDIT_NAME, DEP_EDIT_EMOJI,
    DEP_SET_TOPIC,
) = range(6)


def _fmt_dep(dep, user_count=0, task_count=0, admin=None):
    admin_text = f"{admin['name']} (@{admin['username'] or '—'})" if admin else "—"
    return (
        f"{dep['emoji']} <b>{dep['name']}</b>\n"
        f"🆔 ID: <code>{dep['id']}</code>\n"
        f"👑 Mas'ul: {admin_text}\n"
        f"👥 Xodimlar: {user_count}\n"
        f"📋 Vazifalar: {task_count}\n"
        f"📡 Topic ID: {dep['topic_id'] or '—'}"
    )


# ─── LIST ───────────────────────────────────────────────────

@role_required("super")
async def dep_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    deps = await db.get_all_departments()
    await query.edit_message_text(
        f"🏢 <b>Bo'limlar ro'yxati</b> ({len(deps)} ta):",
        parse_mode="HTML",
        reply_markup=kb.dep_list_kb(deps),
    )


# ─── VIEW ───────────────────────────────────────────────────

@role_required("super")
async def dep_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dep_id = query.data.split(":")[1]
    dep = await db.get_department(dep_id)
    if not dep:
        await query.edit_message_text("❌ Bo'lim topilmadi.")
        return
    users = await db.get_users_by_dep(dep_id)
    tasks = await db.get_tasks_by_dep(dep_id)
    admin = await db.get_user(dep["admin_id"]) if dep["admin_id"] else None
    await query.edit_message_text(
        _fmt_dep(dep, len(users), len(tasks), admin),
        parse_mode="HTML",
        reply_markup=kb.dep_actions_kb(dep_id),
    )


# ─── ADD ────────────────────────────────────────────────────

@role_required("super")
async def dep_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ <b>Yangi bo'lim qo'shish</b>\n\nBo'lim uchun qisqa <b>ID kod</b> kiriting\n(2-5 harf, masalan: it, hr, fin):",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.back_button("dep_list")]),
    )
    return DEP_ADD_ID


async def dep_add_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dep_id = update.message.text.strip().lower()
    if not dep_id.isalpha() or len(dep_id) > 5:
        await update.message.reply_text("❗ 2-5 ta lotin harfidan iborat kod kiriting:")
        return DEP_ADD_ID
    existing = await db.get_department(dep_id)
    if existing:
        await update.message.reply_text(f"❗ '{dep_id}' kodi allaqachon mavjud:")
        return DEP_ADD_ID
    context.user_data["new_dep_id"] = dep_id
    await update.message.reply_text("✏️ Bo'lim <b>nomini</b> kiriting:", parse_mode="HTML")
    return DEP_ADD_NAME


async def dep_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❗ Nom kamida 2 harf:")
        return DEP_ADD_NAME
    context.user_data["new_dep_name"] = name
    await update.message.reply_text("😊 <b>Emoji</b> kiriting (masalan: 💡):", parse_mode="HTML")
    return DEP_ADD_EMOJI


async def dep_add_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emoji = update.message.text.strip()
    dep_id = context.user_data["new_dep_id"]
    name = context.user_data["new_dep_name"]
    caller_id = update.effective_user.id
    await db.create_department(dep_id, name, emoji)
    await db.add_log(caller_id, f"Bo'lim qo'shildi: {name} ({dep_id})")
    await update.message.reply_text(
        f"✅ Bo'lim qo'shildi: {emoji} <b>{name}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("🏢 Bo'limlar", callback_data="dep_list")],
            kb.menu_button(),
        ])
    )
    for k in ["new_dep_id", "new_dep_name"]:
        context.user_data.pop(k, None)
    return ConversationHandler.END


# ─── EDIT ───────────────────────────────────────────────────

@role_required("super")
async def dep_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dep_id = query.data.split(":")[1]
    context.user_data["edit_dep_id"] = dep_id
    dep = await db.get_department(dep_id)
    await query.edit_message_text(
        f"✏️ Tahrirlash: {dep['emoji']} {dep['name']}\n\nYangi nom kiriting:",
        reply_markup=InlineKeyboardMarkup([kb.back_button(f"dep_view:{dep_id}")]),
    )
    return DEP_EDIT_NAME


async def dep_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❗ Nom kamida 2 harf:")
        return DEP_EDIT_NAME
    context.user_data["edit_dep_name"] = name
    await update.message.reply_text("😊 Yangi emoji kiriting:")
    return DEP_EDIT_EMOJI


async def dep_edit_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emoji = update.message.text.strip()
    dep_id = context.user_data["edit_dep_id"]
    name = context.user_data["edit_dep_name"]
    caller_id = update.effective_user.id
    await db.update_department(dep_id, name=name, emoji=emoji)
    await db.add_log(caller_id, f"Bo'lim tahrirlandi: {dep_id} -> {name}")
    await update.message.reply_text(
        f"✅ Bo'lim yangilandi: {emoji} <b>{name}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("🏢 Bo'limlar", callback_data="dep_list")],
        ])
    )
    return ConversationHandler.END


# ─── SET ADMIN ──────────────────────────────────────────────

@role_required("super")
async def dep_set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dep_id = query.data.split(":")[1]
    context.user_data["dep_set_admin_id"] = dep_id
    users = await db.get_users_by_dep(dep_id)
    if not users:
        await query.answer("Bu bo'limda xodim yo'q.", show_alert=True)
        return
    await query.edit_message_text(
        "👑 Mas'ul xodimni tanlang:",
        reply_markup=kb.user_select_kb(users, "dep_admin_set", f"dep_view:{dep_id}"),
    )


@role_required("super")
async def dep_admin_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    user_id_str = parts[1]
    dep_id = context.user_data.get("dep_set_admin_id")
    caller_id = update.effective_user.id

    if user_id_str == "none" or not dep_id:
        await db.update_department(dep_id, admin_id=None)
    else:
        uid = int(user_id_str)
        await db.update_department(dep_id, admin_id=uid)
        await db.update_user(uid, role="admin", dep_id=dep_id)
        await db.add_log(caller_id, f"Bo'lim mas'uli tayinlandi: dep={dep_id}, user={uid}")

    dep = await db.get_department(dep_id)
    await query.edit_message_text(
        f"✅ {dep['emoji']} {dep['name']} mas'uli yangilandi.",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("🏢 Bo'limlar", callback_data="dep_list")],
            kb.menu_button(),
        ])
    )


# ─── SET TOPIC ──────────────────────────────────────────────

@role_required("super")
async def dep_set_topic_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dep_id = query.data.split(":")[1]
    context.user_data["dep_set_topic_id"] = dep_id
    dep = await db.get_department(dep_id)
    await query.edit_message_text(
        f"📡 {dep['emoji']} <b>{dep['name']}</b> uchun forum mavzu ID sini kiriting:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.back_button(f"dep_view:{dep_id}")]),
    )
    return DEP_SET_TOPIC


async def dep_set_topic_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❗ Faqat raqam kiriting:")
        return DEP_SET_TOPIC
    dep_id = context.user_data["dep_set_topic_id"]
    caller_id = update.effective_user.id
    await db.update_department(dep_id, topic_id=int(text))
    await db.add_log(caller_id, f"Topic ID o'rnatildi: dep={dep_id}, topic={text}")
    dep = await db.get_department(dep_id)
    await update.message.reply_text(
        f"✅ {dep['emoji']} {dep['name']} uchun topic ID = {text}",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("🏢 Bo'limlar", callback_data="dep_list")],
        ])
    )
    return ConversationHandler.END


# ─── DELETE ─────────────────────────────────────────────────

@role_required("super")
async def dep_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dep_id = query.data.split(":")[1]
    dep = await db.get_department(dep_id)
    if not dep:
        await query.edit_message_text("❌ Bo'lim topilmadi.")
        return
    has_users = await db.dep_has_users(dep_id)
    if has_users:
        await query.edit_message_text(
            f"🚫 <b>{dep['name']}</b> bo'limida xodimlar bor.\n"
            "Avval ularni boshqa bo'limga ko'chiring.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([kb.back_button(f"dep_view:{dep_id}")]),
        )
        return
    await query.edit_message_text(
        f"⚠️ <b>{dep['emoji']} {dep['name']}</b> bo'limini o'chirishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=kb.confirm_kb(f"dep_del:{dep_id}", f"dep_view:{dep_id}"),
    )


@role_required("super")
async def dep_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dep_id = query.data.split(":")[1]
    caller_id = update.effective_user.id
    dep = await db.get_department(dep_id)
    if not dep:
        await query.edit_message_text("❌ Bo'lim topilmadi.")
        return
    await db.delete_department(dep_id)
    await db.add_log(caller_id, f"Bo'lim o'chirildi: {dep['name']} ({dep_id})")
    await query.edit_message_text(
        f"🗑 <b>{dep['emoji']} {dep['name']}</b> o'chirildi.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("🏢 Bo'limlar", callback_data="dep_list")],
            kb.menu_button(),
        ])
    )


# ─── CONVERSATION HANDLERS ───────────────────────────────────

def get_dep_add_conv():
    return ConversationHandler(
        entry_points=[CQH(dep_add_start, pattern="^dep_add$")],
        states={
            DEP_ADD_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, dep_add_id)],
            DEP_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, dep_add_name)],
            DEP_ADD_EMOJI: [MessageHandler(filters.TEXT & ~filters.COMMAND, dep_add_emoji)],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )


def get_dep_edit_conv():
    return ConversationHandler(
        entry_points=[CQH(dep_edit_start, pattern="^dep_edit:")],
        states={
            DEP_EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, dep_edit_name)],
            DEP_EDIT_EMOJI: [MessageHandler(filters.TEXT & ~filters.COMMAND, dep_edit_emoji)],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )


def get_dep_set_topic_conv():
    return ConversationHandler(
        entry_points=[CQH(dep_set_topic_start, pattern="^dep_set_topic:")],
        states={
            DEP_SET_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, dep_set_topic_value)],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )
