from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import db
import keyboards as kb
from handlers.common import cancel_conv
from decorators import role_required

# ConversationHandler states
(
    USER_ADD_ID, USER_ADD_NAME, USER_ADD_USERNAME,
    USER_ADD_ROLE, USER_ADD_DEP,
    USER_EDIT_NAME, USER_EDIT_USERNAME,
) = range(7)


def _fmt_user(u, dep=None):
    role_names = {"super": "👑 Super Admin", "admin": "🔑 Bo'lim mas'uli", "worker": "👤 Xodim"}
    status_icon = "✅ Faol" if u["status"] == "faol" else "🚫 Bloklangan"
    dep_text = f"{dep['emoji']} {dep['name']}" if dep else "—"
    return (
        f"👤 <b>{u['name']}</b>\n"
        f"🆔 ID: <code>{u['id']}</code>\n"
        f"📛 Username: @{u['username'] or '—'}\n"
        f"🎭 Rol: {role_names.get(u['role'], u['role'])}\n"
        f"🏢 Bo'lim: {dep_text}\n"
        f"📌 Holat: {status_icon}\n"
        f"📅 Qo'shilgan: {u['created_at'][:10]}"
    )


# ─── LIST ───────────────────────────────────────────────────

@role_required("super")
async def user_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    users = await db.get_all_users()
    if not users:
        await query.edit_message_text(
            "👥 Hozircha xodimlar yo'q.",
            reply_markup=InlineKeyboardMarkup([
                [kb.InlineKeyboardButton("➕ Yangi xodim", callback_data="user_add")],
                kb.menu_button(),
            ])
        )
        return
    await query.edit_message_text(
        f"👥 <b>Xodimlar ro'yxati</b> ({len(users)} ta):",
        parse_mode="HTML",
        reply_markup=kb.user_list_kb(users),
    )


# ─── VIEW ───────────────────────────────────────────────────

@role_required("super")
async def user_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    u = await db.get_user(user_id)
    if not u:
        await query.edit_message_text("❌ Xodim topilmadi.", reply_markup=InlineKeyboardMarkup([kb.back_button("user_list")]))
        return
    dep = await db.get_department(u["dep_id"]) if u["dep_id"] else None
    await query.edit_message_text(
        _fmt_user(u, dep),
        parse_mode="HTML",
        reply_markup=kb.user_actions_kb(user_id, u["role"], u["status"]),
    )


# ─── ADD (conversation) ─────────────────────────────────────

@role_required("super")
async def user_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "➕ <b>Yangi xodim qo'shish</b>\n\n"
        "Xodimning Telegram <b>ID raqamini</b> yuboring:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.back_button("user_list")]),
    )
    return USER_ADD_ID


async def user_add_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❗ Raqam kiriting (faqat Telegram ID):")
        return USER_ADD_ID
    uid = int(text)
    existing = await db.get_user(uid)
    if existing:
        await update.message.reply_text(
            f"❗ Bu ID ({uid}) allaqachon ro'yxatda:\n{existing['name']}",
        )
        return USER_ADD_ID
    context.user_data["new_user_id"] = uid
    await update.message.reply_text("✏️ Xodimning <b>to'liq ismini</b> kiriting:", parse_mode="HTML")
    return USER_ADD_NAME


async def user_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❗ Ism kamida 2 harf bo'lishi kerak:")
        return USER_ADD_NAME
    context.user_data["new_user_name"] = name
    await update.message.reply_text(
        "📛 <b>Username</b>ni kiriting (@siz ko'rsatmasdan) yoki — qoldirish uchun <code>-</code>:",
        parse_mode="HTML",
    )
    return USER_ADD_USERNAME


async def user_add_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lstrip("@")
    if username == "-":
        username = ""
    context.user_data["new_user_username"] = username
    buttons = [
        [kb.InlineKeyboardButton("👤 Worker", callback_data="newrole:worker")],
        [kb.InlineKeyboardButton("🔑 Admin", callback_data="newrole:admin")],
        [kb.InlineKeyboardButton("👑 Super", callback_data="newrole:super")],
    ]
    await update.message.reply_text(
        "🎭 <b>Rol tanlang:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return USER_ADD_ROLE


async def user_add_role_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    role = query.data.split(":")[1]
    context.user_data["new_user_role"] = role

    if role == "super":
        await _finish_add_user(query, context, dep_id=None)
        return ConversationHandler.END

    deps = await db.get_all_departments()
    if not deps:
        await query.edit_message_text("❗ Avval bo'lim yarating.")
        return ConversationHandler.END

    await query.edit_message_text(
        "🏢 <b>Bo'lim tanlang:</b>",
        parse_mode="HTML",
        reply_markup=kb.dep_select_kb(deps, "newdep"),
    )
    return USER_ADD_DEP


async def user_add_dep_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dep_id = query.data.split(":")[1]
    await _finish_add_user(query, context, dep_id=dep_id)
    return ConversationHandler.END


async def _finish_add_user(query_or_msg, context, dep_id):
    uid = context.user_data["new_user_id"]
    name = context.user_data["new_user_name"]
    username = context.user_data["new_user_username"]
    role = context.user_data["new_user_role"]
    caller_id = query_or_msg.from_user.id

    await db.create_user(uid, name, username, role, dep_id)
    await db.add_log(caller_id, f"Xodim qo'shildi: {name} (ID:{uid}, rol:{role})")

    dep = await db.get_department(dep_id) if dep_id else None
    dep_text = f"{dep['emoji']} {dep['name']}" if dep else "—"
    text = (
        f"✅ <b>Xodim qo'shildi!</b>\n\n"
        f"👤 {name} | @{username or '—'}\n"
        f"🎭 Rol: {role}\n"
        f"🏢 Bo'lim: {dep_text}"
    )
    await query_or_msg.edit_message_text(
        text, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👥 Ro'yxatga qaytish", callback_data="user_list")],
            kb.menu_button(),
        ])
    )
    for key in ["new_user_id", "new_user_name", "new_user_username", "new_user_role"]:
        context.user_data.pop(key, None)


# ─── EDIT ───────────────────────────────────────────────────

@role_required("super")
async def user_edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    context.user_data["edit_user_id"] = user_id
    u = await db.get_user(user_id)
    await query.edit_message_text(
        f"✏️ <b>Tahrirlash</b>: {u['name']}\n\nYangi ismni kiriting:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.back_button(f"user_view:{user_id}")]),
    )
    return USER_EDIT_NAME


async def user_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        await update.message.reply_text("❗ Ism kamida 2 harf:")
        return USER_EDIT_NAME
    context.user_data["edit_user_name"] = name
    await update.message.reply_text(
        "📛 Yangi username kiriting (yoki <code>-</code>):",
        parse_mode="HTML",
    )
    return USER_EDIT_USERNAME


async def user_edit_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().lstrip("@")
    if username == "-":
        username = ""
    user_id = context.user_data["edit_user_id"]
    name = context.user_data["edit_user_name"]
    caller_id = update.effective_user.id
    await db.update_user(user_id, name=name, username=username)
    await db.add_log(caller_id, f"Xodim tahrirlandi: ID:{user_id} -> {name}")
    await update.message.reply_text(
        f"✅ Ma'lumotlar yangilandi.\n👤 {name} | @{username or '—'}",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👁 Ko'rish", callback_data=f"user_view:{user_id}")],
            kb.menu_button(),
        ])
    )
    return ConversationHandler.END


# ─── BLOCK / UNBLOCK ────────────────────────────────────────

@role_required("super")
async def user_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    caller_id = update.effective_user.id
    if user_id == caller_id:
        await query.answer("🚫 O'zingizni bloklashingiz mumkin emas.", show_alert=True)
        return
    await db.update_user(user_id, status="bloklangan")
    await db.add_log(caller_id, f"Xodim bloklandi: ID:{user_id}")
    await query.edit_message_text(
        "🚫 Xodim bloklandi.",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👁 Ko'rish", callback_data=f"user_view:{user_id}")],
            kb.menu_button(),
        ])
    )


@role_required("super")
async def user_unblock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    caller_id = update.effective_user.id
    await db.update_user(user_id, status="faol")
    await db.add_log(caller_id, f"Xodim faollashtirildi: ID:{user_id}")
    await query.edit_message_text(
        "✅ Xodim faollashtirildi.",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👁 Ko'rish", callback_data=f"user_view:{user_id}")],
            kb.menu_button(),
        ])
    )


# ─── DELETE ─────────────────────────────────────────────────

@role_required("super")
async def user_del_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    caller_id = update.effective_user.id
    if user_id == caller_id:
        await query.answer("🚫 O'zingizni o'chira olmaysiz.", show_alert=True)
        return
    u = await db.get_user(user_id)
    if not u:
        await query.edit_message_text("❌ Xodim topilmadi.")
        return
    if u["role"] == "super":
        cnt = await db.count_supers()
        if cnt <= 1:
            await query.answer("🚫 Yagona Super Adminni o'chirib bo'lmaydi.", show_alert=True)
            return
    await query.edit_message_text(
        f"⚠️ <b>{u['name']}</b> ni o'chirishni tasdiqlaysizmi?\n"
        "Barcha vazifalari ham o'chiriladi.",
        parse_mode="HTML",
        reply_markup=kb.confirm_kb(f"user_del:{user_id}", f"user_view:{user_id}"),
    )


@role_required("super")
async def user_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    caller_id = update.effective_user.id
    u = await db.get_user(user_id)
    if not u:
        await query.edit_message_text("❌ Xodim topilmadi.")
        return
    await db.delete_user(user_id)
    await db.add_log(caller_id, f"Xodim o'chirildi: {u['name']} (ID:{user_id})")
    await query.edit_message_text(
        f"🗑 <b>{u['name']}</b> o'chirildi.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👥 Xodimlar", callback_data="user_list")],
            kb.menu_button(),
        ])
    )


# ─── WORKERS VIEW (for admin) ────────────────────────────────

async def my_workers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db_user = context.user_data.get("db_user")
    if not db_user:
        db_user = dict(await db.get_user(update.effective_user.id))

    if db_user["role"] == "super":
        users = await db.get_all_users()
        title = "👥 Barcha xodimlar"
    else:
        if not db_user.get("dep_id"):
            await query.edit_message_text(
                "🚫 Sizga bo'lim biriktirilmagan.",
                reply_markup=InlineKeyboardMarkup([kb.menu_button()])
            )
            return
        users = await db.get_users_by_dep(db_user["dep_id"])
        dep = await db.get_department(db_user["dep_id"])
        title = f"👷 {dep['emoji']} {dep['name']} xodimlari"

    if not users:
        await query.edit_message_text(
            f"{title}\n\nXodimlar yo'q.",
            reply_markup=InlineKeyboardMarkup([kb.menu_button()])
        )
        return

    lines = []
    for u in users:
        icon = {"super": "👑", "admin": "🔑", "worker": "👤"}.get(u["role"], "👤")
        st = "✅" if u["status"] == "faol" else "🚫"
        lines.append(f"{st} {icon} {u['name']} (@{u['username'] or '—'})")

    await query.edit_message_text(
        f"<b>{title}</b> ({len(users)} ta):\n\n" + "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.menu_button()])
    )


# ─── CONVERSATION HANDLER ────────────────────────────────────

def get_user_add_conv():
    from telegram.ext import CallbackQueryHandler as CQH
    return ConversationHandler(
        entry_points=[CQH(user_add_start, pattern="^user_add$")],
        states={
            USER_ADD_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_add_id)],
            USER_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_add_name)],
            USER_ADD_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_add_username)],
            USER_ADD_ROLE: [CQH(user_add_role_cb, pattern="^newrole:")],
            USER_ADD_DEP: [CQH(user_add_dep_cb, pattern="^newdep:")],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )


def get_user_edit_conv():
    from telegram.ext import CallbackQueryHandler as CQH
    return ConversationHandler(
        entry_points=[CQH(user_edit_start, pattern="^user_edit:")],
        states={
            USER_EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_edit_name)],
            USER_EDIT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_edit_username)],
        },
        fallbacks=[CQH(cancel_conv, pattern="^menu$")],
        per_chat=True, per_user=True,
    )
