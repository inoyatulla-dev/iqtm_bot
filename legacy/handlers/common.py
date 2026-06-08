from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
import db
import keyboards as kb


# ─── SHARED CANCEL (barcha ConversationHandler fallback uchun) ───

async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ConversationHandler ni bekor qilish va menyuga qaytish."""
    if update.callback_query:
        await update.callback_query.answer()
    db_user = await db.get_user(update.effective_user.id) if update.effective_user else None
    role = db_user["role"] if db_user and db_user["status"] == "faol" else None
    if role == "super":
        menu = kb.super_menu_kb()
    elif role == "admin":
        menu = kb.admin_menu_kb()
    else:
        menu = kb.worker_menu_kb()

    text = "🏠 Asosiy menyu:"
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=menu)
        elif update.message:
            await update.message.reply_text(text, reply_markup=menu)
    except Exception:
        pass
    return ConversationHandler.END


# ─── /start ─────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = await db.get_user(user.id)

    # Noma'lum foydalanuvchi → pending saqlab, super admin ga xabar
    if not db_user:
        now = datetime.now().isoformat()
        await db.create_user(user.id, user.full_name, user.username or "", "worker", None)
        await db.update_user(user.id, status="pending")

        supers = await db.get_users_by_role("super")
        for sup in supers:
            try:
                await context.bot.send_message(
                    chat_id=sup["id"],
                    text=(
                        f"🔔 <b>Yangi ariza!</b>\n\n"
                        f"👤 <b>{user.full_name}</b>\n"
                        f"🆔 <code>{user.id}</code>\n"
                        f"📛 @{user.username or '—'}"
                    ),
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ Qabul", callback_data=f"approve_user:{user.id}"),
                        InlineKeyboardButton("❌ Rad", callback_data=f"reject_user:{user.id}"),
                    ]]),
                )
            except Exception:
                pass

        await update.message.reply_text(
            "👋 Salom! Sizning arizangiz yuborildi.\n"
            "Administrator tasdiqlagunicha kuting. ⏳"
        )
        return

    if db_user["status"] == "pending":
        await update.message.reply_text(
            "⏳ Arizangiz ko'rib chiqilmoqda. Biroz kuting."
        )
        return

    if db_user["status"] == "bloklangan":
        await update.message.reply_text("🚫 Kirishingiz bloklangan.")
        return

    role = db_user["role"]
    name = db_user["name"]

    if role == "super":
        pending = await db.get_pending_users()
        menu = kb.super_menu_kb(len(pending))
        greeting = f"👑 Xush kelibsiz, <b>{name}</b>!\nSiz Super Admin sifatida kirdingiz."
    elif role == "admin":
        menu = kb.admin_menu_kb()
        greeting = f"🔑 Xush kelibsiz, <b>{name}</b>!\nSiz Bo'lim mas'uli sifatida kirdingiz."
    else:
        menu = kb.worker_menu_kb()
        greeting = f"👋 Xush kelibsiz, <b>{name}</b>!\nSiz xodim sifatida kirdingiz."

    await update.message.reply_text(
        f"🤖 <b>IQTM Workspace</b>\n\n{greeting}",
        parse_mode="HTML",
        reply_markup=menu,
    )


# ─── /menu ──────────────────────────────────────────────────────

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = await db.get_user(user.id)
    if not db_user or db_user["status"] != "faol":
        await update.message.reply_text("🚫 Sizga ruxsat berilmagan.")
        return
    role = db_user["role"]
    menu = kb.super_menu_kb() if role == "super" else (
        kb.admin_menu_kb() if role == "admin" else kb.worker_menu_kb()
    )
    await update.message.reply_text("🏠 Asosiy menyu:", reply_markup=menu)


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db_user = await db.get_user(update.effective_user.id)
    if not db_user or db_user["status"] != "faol":
        await query.edit_message_text("🚫 Sizga ruxsat berilmagan.")
        return
    role = db_user["role"]
    if role == "super":
        pending = await db.get_pending_users()
        menu = kb.super_menu_kb(len(pending))
    elif role == "admin":
        menu = kb.admin_menu_kb()
    else:
        menu = kb.worker_menu_kb()
    await query.edit_message_text("🏠 Asosiy menyu:", reply_markup=menu)


# ─── /yordam ────────────────────────────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "❓ <b>IQTM Workspace — Yordam</b>\n\n"
        "Bu bot ICT Markaz jamoasini boshqarish uchun.\n\n"
        "<b>Komandalar:</b>\n"
        "/start — Boshlash / menyuga qaytish\n"
        "/menu — Asosiy menyu\n"
        "/yordam — Yordam\n"
        "/set_group — Guruh ID ni avtomatik aniqlash (guruhda)\n"
        "/topic_aniqla — Forum mavzu ID ni aniqlash\n\n"
        "Barcha amallar tugmalar orqali bajariladi."
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([kb.menu_button()])
        )
    else:
        await update.message.reply_text(text, parse_mode="HTML")


# ─── /set_group ─────────────────────────────────────────────────

async def set_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruhda ishlatilganda, shu guruh ID sini saqlaydi."""
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "Bu komanda guruhda yuboring.\n"
            "Bot admin bo'lgan guruhga boring va /set_group yuboring."
        )
        return

    # Faqat super admin yoki guruh administratori
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    db_user = await db.get_user(user_id)
    if not db_user or db_user["role"] != "super":
        return  # jimgina o'tkazib yuborish

    await db.save_setting("group_chat_id", str(chat_id))
    await db.add_log(user_id, f"Guruh ID saqlandi: {chat_id}")

    try:
        await update.message.reply_text(
            f"✅ Guruh ID saqlandi: <code>{chat_id}</code>\n"
            "Endi bot shu guruhga e'lonlar yuboradi.",
            parse_mode="HTML",
        )
    except Exception:
        pass


# ─── SUB-MENYU HANDLERLARI ──────────────────────────────────────

async def task_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📋 <b>Vazifalar</b>", parse_mode="HTML",
        reply_markup=kb.task_submenu_kb(),
    )


async def proj_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📁 <b>Loyihalar</b>", parse_mode="HTML",
        reply_markup=kb.proj_submenu_kb(),
    )


async def group_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    pending = await db.get_pending_users()
    count = len(pending) if pending else 0
    await q.edit_message_text(
        "👥 <b>Guruh sozlamalari</b>", parse_mode="HTML",
        reply_markup=kb.group_settings_submenu_kb(count),
    )


async def stats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "📊 <b>Statistika</b>", parse_mode="HTML",
        reply_markup=kb.stats_submenu_kb(),
    )


async def bot_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "⚙️ <b>Bot sozlamalari</b>", parse_mode="HTML",
        reply_markup=kb.bot_settings_submenu_kb(),
    )


# ─── /topic_aniqla ──────────────────────────────────────────────

async def topic_detect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Guruhda (forum mavzusida yoki oddiy guruhda) ishlatiladi.
    - chat_id ni avtomatik saqlaydi
    - thread_id ni ko'rsatadi va bo'limga biriktirish tugmasini chiqaradi
    """
    if not update.message:
        return

    chat = update.effective_chat
    msg = update.message

    # Private chatda faqat yo'riqnoma
    if chat.type == "private":
        await msg.reply_text(
            "📡 <b>Topic ID aniqlash</b>\n\n"
            "Bu komanda <b>guruhda</b> ishlatilsin:\n"
            "1. Bot admin bo'lgan forum-guruhga boring\n"
            "2. Kerakli mavzuga kiring\n"
            "3. <code>/topic_aniqla</code> yuboring",
            parse_mode="HTML",
        )
        return

    chat_id = chat.id
    thread_id = msg.message_thread_id  # None bo'lishi mumkin (General yoki oddiy guruh)

    # GROUP_CHAT_ID ni avtomatik saqlash
    saved_gid = await db.get_setting("group_chat_id")
    if not saved_gid or saved_gid == "0":
        await db.save_setting("group_chat_id", str(chat_id))
        gid_msg = f"✅ Guruh ID saqlandi: <code>{chat_id}</code>"
    else:
        gid_msg = f"📡 Guruh ID: <code>{chat_id}</code>"

    if not thread_id:
        await msg.reply_text(
            f"{gid_msg}\n\n"
            "⚠️ Bu mavzu (topic) emas yoki 'General' bo'limdasiz.\n"
            "Forum mavzusiga kiring va qayta yuboring.",
            parse_mode="HTML",
        )
        return

    # Super admin bo'lsa — 4 ta kanal uchun biriktirish tugmalari
    db_user = await db.get_user(update.effective_user.id) if update.effective_user else None
    if db_user and db_user["role"] == "super":
        CHANNELS = [
            ("topic_elonlar",   "📣 E'lonlar"),
            ("topic_vazifalar", "📋 Vazifalar"),
            ("topic_reja",      "📅 Reja/Deadline"),
            ("topic_hisobotlar","📊 Hisobotlar"),
        ]
        buttons = []
        for key, label in CHANNELS:
            cur = await db.get_setting(key)
            linked = " ✅" if cur and cur == str(thread_id) else ""
            buttons.append([InlineKeyboardButton(
                f"{label}{linked}",
                callback_data=f"link_group_topic:{key}:{thread_id}",
            )])

        # Bo'limlar — har biri uchun ham topic biriktirish
        deps = await db.get_all_departments()
        if deps:
            buttons.append([InlineKeyboardButton("── Bo'limlar ──", callback_data="noop")])
            for dep in deps:
                cur_t = dep["topic_id"]
                linked = " ✅" if cur_t and str(cur_t) == str(thread_id) else ""
                buttons.append([InlineKeyboardButton(
                    f"{dep['emoji']} {dep['name']}{linked}",
                    callback_data=f"link_topic:{dep['id']}:{thread_id}",
                )])

        await msg.reply_text(
            f"{gid_msg}\n"
            f"🧵 Mavzu ID: <b>{thread_id}</b>\n\n"
            "Bu mavzuni qaysi kanalga yoki bo'limga ulash?",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    else:
        await msg.reply_text(
            f"{gid_msg}\n"
            f"🧵 Mavzu (topic) ID: <code>{thread_id}</code>",
            parse_mode="HTML",
        )
