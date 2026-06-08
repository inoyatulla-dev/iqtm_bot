import os
import random
import string
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters, CallbackQueryHandler as CQH,
)
import db
import keyboards as kb
from decorators import role_required
from handlers.common import cancel_conv

_pending_super_transfer: dict[int, dict] = {}


# ─── ROLE MANAGE ────────────────────────────────────────────

_ROLE_INFO = {
    "super": {
        "icon": "👑", "name": "Super Admin",
        "perms": [
            "• Barcha xodimlar va bo'limlarni boshqarish",
            "• Ko'p bo'limli (qulflangan muddatli) vazifalar",
            "• Loyihalar va bosqichlar yaratish",
            "• Rollarni o'zgartirish",
            "• To'liq statistika va hisobotlar",
            "• Bot sozlamalari",
        ],
    },
    "admin": {
        "icon": "🔑", "name": "Bo'lim mas'uli",
        "perms": [
            "• O'z bo'limi vazifalarini boshqarish",
            "• Xodim tayinlash va kuzatish",
            "• Oddiy vazifalar yaratish",
            "• Bo'lim statistikasi va hisoboti",
        ],
    },
    "worker": {
        "icon": "👤", "name": "Xodim",
        "perms": [
            "• O'ziga biriktirilgan vazifalarni ko'rish",
            "• Vazifa holatini yangilash",
            "• Eslatma o'rnatish",
        ],
    },
}


@role_required("super")
async def role_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    all_users = await db.get_all_users()
    counts = {"super": 0, "admin": 0, "worker": 0}
    for u in all_users:
        if u["role"] in counts:
            counts[u["role"]] += 1

    lines = ["👑 <b>Rollar va imkoniyatlar</b>\n"]
    for rk, info in _ROLE_INFO.items():
        lines.append(f"{info['icon']} <b>{info['name']}</b> — {counts[rk]} nafar")
        lines.extend(f"  {p}" for p in info["perms"])
        lines.append("")

    buttons = [
        [InlineKeyboardButton(f"👑 Super Admin ({counts['super']})",  callback_data="role_users:super")],
        [InlineKeyboardButton(f"🔑 Bo'lim mas'uli ({counts['admin']})", callback_data="role_users:admin")],
        [InlineKeyboardButton(f"👤 Xodimlar ({counts['worker']})",    callback_data="role_users:worker")],
        kb.menu_button(),
    ]
    await query.edit_message_text(
        "\n".join(lines), parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@role_required("super")
async def role_view_by_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tanlangan rolga ega xodimlar ro'yxati."""
    query = update.callback_query
    await query.answer()
    role_type = query.data.split(":")[1]
    info = _ROLE_INFO.get(role_type, {"icon": "👤", "name": role_type})
    all_users = await db.get_all_users()
    users = [u for u in all_users if u["role"] == role_type]

    if not users:
        await query.edit_message_text(
            f"{info['icon']} <b>{info['name']}</b>\n\nHech kim yo'q.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([kb.back_button("role_manage")]),
        )
        return

    buttons = []
    for u in users:
        dep_text = ""
        if u["dep_id"]:
            dep = await db.get_department(u["dep_id"])
            dep_text = f" | {dep['emoji']} {dep['name']}" if dep else ""
        si = "✅" if u["status"] == "faol" else "🚫"
        buttons.append([InlineKeyboardButton(
            f"{si} {u['name']}{dep_text}",
            callback_data=f"user_view:{u['id']}",
        )])
    buttons.append(kb.back_button("role_manage"))

    await query.edit_message_text(
        f"{info['icon']} <b>{info['name']}</b> — {len(users)} nafar:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ─── SET ROLE ────────────────────────────────────────────────

@role_required("super")
async def user_setrole_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    u = await db.get_user(user_id)
    if not u:
        await query.edit_message_text("❌ Xodim topilmadi.")
        return
    await query.edit_message_text(
        f"👑 Rol o'zgartirish: <b>{u['name']}</b>\n\nYangi rolni tanlang:",
        parse_mode="HTML",
        reply_markup=kb.role_select_kb(user_id),
    )


@role_required("super")
async def user_setrole(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    target_id = int(parts[1])
    new_role = parts[2]
    caller_id = update.effective_user.id

    u = await db.get_user(target_id)
    if not u:
        await query.edit_message_text("❌ Xodim topilmadi.")
        return

    if u["role"] == "super" and new_role != "super":
        cnt = await db.count_supers()
        if cnt <= 1:
            await query.answer("🚫 Yagona Super Adminni pasaytirib bo'lmaydi.", show_alert=True)
            return

    if new_role == "super" and u["role"] != "super":
        password = os.getenv("SUPER_TRANSFER_PASSWORD", "")
        if password:
            _pending_super_transfer[caller_id] = {"target_id": target_id, "password": password}
        else:
            code = "".join(random.choices(string.digits, k=6))
            _pending_super_transfer[caller_id] = {"target_id": target_id, "code": code}
            await query.edit_message_text(
                f"🔐 <b>{u['name']}</b> ni Super Admin qilish uchun\n"
                f"Tasodifiy kod: <code>{code}</code>\n\n"
                "Kodni quyida yuboring:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([kb.back_button(f"user_role:{target_id}")]),
            )
            context.user_data["awaiting_super_code"] = True
            return

        await query.edit_message_text(
            f"🔐 <b>{u['name']}</b> ni Super Admin qilish uchun\n"
            "Xavfsizlik parolini yuboring:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([kb.back_button(f"user_role:{target_id}")]),
        )
        context.user_data["awaiting_super_code"] = True
        return

    await _apply_role_change(caller_id, target_id, new_role, u, query)


async def _apply_role_change(caller_id, target_id, new_role, u, reply_obj):
    dep_id = u["dep_id"] if new_role != "super" else None
    await db.update_user(target_id, role=new_role, dep_id=dep_id)
    if new_role != "admin":
        await db.update_department_admin_clear(target_id)
    await db.add_log(caller_id, f"Rol o'zgartirildi: {u['name']} -> {new_role}")
    await reply_obj.edit_message_text(
        f"✅ <b>{u['name']}</b> roli: <b>{new_role}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👁 Ko'rish", callback_data=f"user_view:{target_id}")],
            kb.menu_button(),
        ])
    )


async def super_code_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_super_code"):
        return
    caller_id = update.effective_user.id
    pending = _pending_super_transfer.get(caller_id)
    if not pending:
        context.user_data.pop("awaiting_super_code", None)
        return

    entered = update.message.text.strip()
    expected = pending.get("password") or pending.get("code")

    if entered != expected:
        await update.message.reply_text(
            "❌ Noto'g'ri kod. Amal bekor qilindi.",
            reply_markup=InlineKeyboardMarkup([kb.menu_button()])
        )
        _pending_super_transfer.pop(caller_id, None)
        context.user_data.pop("awaiting_super_code", None)
        return

    target_id = pending["target_id"]
    u = await db.get_user(target_id)
    await db.update_user(target_id, role="super", dep_id=None)
    await db.add_log(caller_id, f"Super Admin tayinlandi: {u['name']}")
    _pending_super_transfer.pop(caller_id, None)
    context.user_data.pop("awaiting_super_code", None)

    await update.message.reply_text(
        f"✅ <b>{u['name']}</b> endi Super Admin!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("👁 Ko'rish", callback_data=f"user_view:{target_id}")],
            kb.menu_button(),
        ])
    )


# ─── PENDING USERS ───────────────────────────────────────────

@role_required("super")
async def pending_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    users = await db.get_pending_users()
    await query.edit_message_text(
        f"🔔 <b>Kutayotgan xodimlar</b> ({len(users)} ta):\n\n"
        "Xodimni tanlang va rolini belgilang:",
        parse_mode="HTML",
        reply_markup=kb.pending_list_kb(users),
    )


@role_required("super")
async def approve_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    u = await db.get_user(user_id)
    if not u:
        await query.edit_message_text("❌ Foydalanuvchi topilmadi.")
        return
    await query.edit_message_text(
        f"👤 <b>{u['name']}</b>\n"
        f"🆔 <code>{u['id']}</code>\n"
        f"📛 @{u['username'] or '—'}\n\n"
        "Rol tanlang:",
        parse_mode="HTML",
        reply_markup=kb.approve_role_kb(user_id),
    )


@role_required("super")
async def approve_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    user_id = int(parts[1])
    role = parts[2]
    caller_id = update.effective_user.id

    if role == "super":
        u = await db.get_user(user_id)
        await db.update_user(user_id, role="super", dep_id=None, status="faol")
        await db.add_log(caller_id, f"Pending user tasdiqlandi (super): {u['name']}")
        await query.edit_message_text(
            f"✅ <b>{u['name']}</b> Super Admin sifatida qabul qilindi!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [kb.InlineKeyboardButton("🔔 Kutayotganlar", callback_data="pending_list")],
                kb.menu_button(),
            ])
        )
        # Xodimga xabar
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Sizning arizangiz tasdiqlandi! /start bosing."
            )
        except Exception:
            pass
        return

    # worker/admin uchun bo'lim tanlash
    deps = await db.get_all_departments()
    await query.edit_message_text(
        f"🏢 <b>Bo'lim tanlang</b> (rol: {role}):",
        parse_mode="HTML",
        reply_markup=kb.approve_dep_kb(user_id, role, deps),
    )


@role_required("super")
async def approve_dep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    user_id = int(parts[1])
    role = parts[2]
    dep_id = parts[3]
    caller_id = update.effective_user.id

    u = await db.get_user(user_id)
    if not u:
        await query.edit_message_text("❌ Topilmadi.")
        return

    await db.update_user(user_id, role=role, dep_id=dep_id, status="faol")
    if role == "admin":
        await db.update_department(dep_id, admin_id=user_id)
    await db.add_log(caller_id, f"Pending user tasdiqlandi: {u['name']} ({role}, {dep_id})")

    dep = await db.get_department(dep_id)
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Sizning arizangiz tasdiqlandi! /start bosing."
        )
    except Exception:
        pass

    await query.edit_message_text(
        f"✅ <b>{u['name']}</b> qabul qilindi!\n"
        f"Rol: {role} | Bo'lim: {dep['emoji']} {dep['name']}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("🔔 Kutayotganlar", callback_data="pending_list")],
            kb.menu_button(),
        ])
    )


@role_required("super")
async def reject_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    caller_id = update.effective_user.id
    u = await db.get_user(user_id)
    await db.delete_user(user_id)
    await db.add_log(caller_id, f"Pending user rad etildi: ID:{user_id}")
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Sizning arizangiz rad etildi."
        )
    except Exception:
        pass
    await query.edit_message_text(
        f"❌ {u['name'] if u else user_id} rad etildi.",
        reply_markup=InlineKeyboardMarkup([
            [kb.InlineKeyboardButton("🔔 Kutayotganlar", callback_data="pending_list")],
            kb.menu_button(),
        ])
    )


# ─── GROUP MEMBERS ────────────────────────────────────────────

@role_required("super")
async def group_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    group_id_str = await db.get_setting("group_chat_id") or os.getenv("GROUP_CHAT_ID", "0")
    group_id = int(group_id_str or 0)

    # DB dagi barcha foydalanuvchilar (pending + faol + bloklangan)
    all_db_users = await db.get_all_users()
    db_ids = {u["id"] for u in all_db_users}

    # Guruh adminlari (Telegram API) — tizimda yo'qlarini ajratamiz
    admins_new = []
    admin_count = 0
    if group_id:
        try:
            admins = await context.bot.get_chat_administrators(group_id)
            for admin in admins:
                u = admin.user
                if u.is_bot:
                    continue
                admin_count += 1
                context.bot_data[f"gm_{u.id}"] = {
                    "id": u.id,
                    "name": u.full_name,
                    "username": u.username or "",
                }
                if u.id not in db_ids:
                    admins_new.append(admin)
        except Exception:
            pass

    active = sum(1 for u in all_db_users if u["status"] == "faol")
    pending = sum(1 for u in all_db_users if u["status"] == "pending")

    text = (
        f"👥 <b>A'zolar boshqaruvi</b>\n\n"
        f"📊 Tizimda: {active} faol, {pending} kutayotgan\n"
        f"👮 Guruh adminlari: {admin_count} ta"
        + (f" ({len(admins_new)} yangi)" if admins_new else "")
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=kb.group_members_kb(admins_new, all_db_users),
    )


@role_required("super")
async def invite_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from urllib.parse import quote
    query = update.callback_query
    await query.answer()
    bot_username = context.bot.username
    link = f"https://t.me/{bot_username}"
    back_cb = "user_list" if query.data == "invite_link" else "group_members"

    share_msg = (
        "🏢 IQTM Workspace tizimiga taklif!\n\n"
        "Ariza qoldirish uchun quyidagi havolaga kiring va "
        "«▶️ Start» tugmasini bosing:\n\n"
        f"👉 {link}\n\n"
        "Arizangiz ko'rib chiqilgach, tizimga kirish huquqi beriladi. ✅"
    )
    share_url = f"https://t.me/share/url?url={quote(link)}&text={quote(share_msg)}"

    text = (
        "🔗 <b>Yangi xodim qo'shish — havola orqali</b>\n\n"
        "Xodimga yuboriladigan havola:\n\n"
        f"<code>{link}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Jarayon:</b>\n"
        "1️⃣ Xodim havolaga bosadi — bot ochiladi\n"
        "2️⃣ <b>Start</b> tugmasini bosadi → ariza yuboriladi\n"
        "3️⃣ Sizga tasdiqlash bildirishnomasi keladi\n"
        "4️⃣ Rol va bo'lim belgilaysiz\n"
        "5️⃣ Xodim tizimga kiradi ✅\n\n"
        "<i>Yangi arizalar «Kutayotganlar» bo'limida ko'rinadi.</i>"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📨 Havolani ulashish", url=share_url)],
            [InlineKeyboardButton("🔗 Havolani ochish",   url=link)],
            [InlineKeyboardButton("◀️ Orqaga", callback_data=back_cb)],
            kb.menu_button(),
        ]),
    )


@role_required("super")
async def gm_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruh admin sini xodim sifatida qo'shish — rol tanlash."""
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split(":")[1])
    caller_id = update.effective_user.id

    # Bot_data dan olish
    gm_data = context.bot_data.get(f"gm_{user_id}", {})
    name = gm_data.get("name", str(user_id))
    username = gm_data.get("username", "")

    await query.edit_message_text(
        f"➕ <b>{name}</b>\n"
        f"🆔 <code>{user_id}</code>  @{username or '—'}\n\n"
        "Rol tanlang:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👤 Xodim", callback_data=f"gm_role:{user_id}:worker")],
            [InlineKeyboardButton("🔑 Mas'ul", callback_data=f"gm_role:{user_id}:admin")],
            [InlineKeyboardButton("👑 Super", callback_data=f"gm_role:{user_id}:super")],
            kb.back_button("group_members"),
        ])
    )


@role_required("super")
async def gm_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    user_id = int(parts[1])
    role = parts[2]
    caller_id = update.effective_user.id

    gm_data = context.bot_data.get(f"gm_{user_id}", {})
    name = gm_data.get("name", str(user_id))
    username = gm_data.get("username", "")

    if role == "super":
        await db.create_user(user_id, name, username, "super", None)
        await db.add_log(caller_id, f"Guruh admini qo'shildi (super): {name}")
        await query.edit_message_text(
            f"✅ <b>{name}</b> Super Admin sifatida qo'shildi!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 Guruh a'zolari", callback_data="group_members")],
                kb.menu_button(),
            ])
        )
        return

    deps = await db.get_all_departments()
    await query.edit_message_text(
        f"🏢 <b>{name}</b> uchun bo'lim tanlang (rol: {role}):",
        parse_mode="HTML",
        reply_markup=kb.approve_dep_kb(user_id, role, deps),
    )


@role_required("super")
async def gm_dep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """gm_add uchun dep tanlash — approve_dep bilan birlashtirilgan."""
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    user_id = int(parts[1])
    role = parts[2]
    dep_id = parts[3]
    caller_id = update.effective_user.id

    gm_data = context.bot_data.get(f"gm_{user_id}", {})
    name = gm_data.get("name", str(user_id))
    username = gm_data.get("username", "")

    existing = await db.get_user(user_id)
    if existing:
        await db.update_user(user_id, role=role, dep_id=dep_id, status="faol")
    else:
        await db.create_user(user_id, name, username, role, dep_id)

    if role == "admin":
        await db.update_department(dep_id, admin_id=user_id)

    await db.add_log(caller_id, f"Guruh admini qo'shildi: {name} ({role}, {dep_id})")
    dep = await db.get_department(dep_id)

    await query.edit_message_text(
        f"✅ <b>{name}</b> qo'shildi!\n"
        f"Rol: {role} | Bo'lim: {dep['emoji']} {dep['name']}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Guruh a'zolari", callback_data="group_members")],
            kb.menu_button(),
        ])
    )


# ─── LINK TOPIC (guruhdan bir marta bosib biriktirish) ────────

@role_required("super")
async def link_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruhda /topic_aniqla dan kelib chiqqan bo'limga biriktirish."""
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    dep_id = parts[1]
    thread_id = int(parts[2])
    caller_id = update.effective_user.id

    await db.update_department(dep_id, topic_id=thread_id)
    await db.add_log(caller_id, f"Topic biriktirildi: dep={dep_id}, topic={thread_id}")
    dep = await db.get_department(dep_id)

    await query.edit_message_text(
        f"✅ <b>{dep['emoji']} {dep['name']}</b> bo'limiga\n"
        f"mavzu ID <code>{thread_id}</code> biriktirildi!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.menu_button()]),
    )


# ─── LINK GROUP TOPIC (from /topic_aniqla) ───────────────────

@role_required("super")
async def link_group_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split(":")
    key, thread_id = parts[1], parts[2]

    label_map = {
        "topic_elonlar":   "📣 E'lonlar",
        "topic_vazifalar": "📋 Vazifalar",
        "topic_reja":      "📅 Reja/Deadline",
        "topic_hisobotlar":"📊 Hisobotlar",
    }
    label = label_map.get(key, key)

    await db.save_setting(key, thread_id)
    await db.add_log(query.from_user.id, f"Group topic ulandi: {key}={thread_id}")

    await query.edit_message_text(
        f"✅ <b>{label}</b> uchun\n"
        f"mavzu ID <code>{thread_id}</code> saqlandi!\n\n"
        "Boshqa mavzuga ham <code>/topic_aniqla</code> yuboring.",
        parse_mode="HTML",
    )


# ─── SETTINGS ────────────────────────────────────────────────

@role_required("super")
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group_id = await db.get_setting("group_chat_id") or os.getenv("GROUP_CHAT_ID", "")
    group_text = f"<code>{group_id}</code>" if group_id and group_id != "0" else "❌ ulanmagan"
    await query.edit_message_text(
        f"⚙️ <b>Sozlamalar</b>\n\n"
        f"📡 Guruh ID: {group_text}",
        parse_mode="HTML",
        reply_markup=kb.settings_kb(),
    )


# ─── TOPIC SETTINGS ──────────────────────────────────────────

_TOPIC_SET = 50  # ConversationHandler state

_TOPIC_LABELS = {
    "topic_elonlar":   "📣 E'lonlar",
    "topic_vazifalar": "📋 Vazifalar",
    "topic_reja":      "📅 Reja/Deadline",
    "topic_hisobotlar":"📊 Hisobotlar",
}


async def _load_topics() -> dict:
    return {k: await db.get_setting(k) for k in _TOPIC_LABELS}


@role_required("super")
async def topic_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    topics = await _load_topics()
    deps = await db.get_all_departments()
    await query.edit_message_text(
        "🧵 <b>Topic sozlash</b>\n\n"
        "Kanal yoki bo'lim tugmasini bosib topic ID kiriting.\n"
        "ID ni bilish: mavzuga kiring → <code>/topic_aniqla</code>:",
        parse_mode="HTML",
        reply_markup=kb.topic_settings_kb(topics, deps),
    )


@role_required("super")
async def topic_set_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.split(":", 1)[1]
    context.user_data["topic_set_key"] = key
    label = _TOPIC_LABELS.get(key, key)
    cur = await db.get_setting(key)
    cur_text = f"Hozirgi: <code>{cur}</code>" if cur else "Hozirgi: ❌ sozlanmagan"
    await query.edit_message_text(
        f"🧵 <b>{label}</b>\n\n"
        f"{cur_text}\n\n"
        "Yangi topic ID raqamini kiriting\n"
        "<i>(mavzuga kiring → /topic_aniqla → raqamni ko'chiring)</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("◀️ Orqaga", callback_data="topic_settings"),
        ]]),
    )
    return _TOPIC_SET


async def topic_set_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    key = context.user_data.get("topic_set_key", "")
    if not text.lstrip("-").isdigit():
        await update.message.reply_text("❌ Faqat raqam kiriting (masalan: 12 yoki -100123):")
        return _TOPIC_SET
    await db.save_setting(key, text)
    await db.add_log(update.effective_user.id, f"Topic sozlandi: {key}={text}")
    label = _TOPIC_LABELS.get(key, key)
    topics = await _load_topics()
    deps = await db.get_all_departments()
    await update.message.reply_text(
        f"✅ <b>{label}</b> uchun topic ID saqlandi: <code>{text}</code>",
        parse_mode="HTML",
        reply_markup=kb.topic_settings_kb(topics, deps),
    )
    return ConversationHandler.END


def get_topic_set_conv():
    return ConversationHandler(
        entry_points=[CQH(topic_set_start, pattern="^topic_set:")],
        states={_TOPIC_SET: [MessageHandler(filters.TEXT & ~filters.COMMAND, topic_set_save)]},
        fallbacks=[
            CQH(topic_settings, pattern="^topic_settings$"),
            CommandHandler("menu", cancel_conv),
        ],
        per_chat=True,
        per_user=True,
    )


@role_required("super")
async def topic_auto_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    group_id = await db.get_setting("group_chat_id") or os.getenv("GROUP_CHAT_ID", "")
    gid_text = f"<code>{group_id}</code>" if group_id and group_id not in ("0", "") else "❌ ulanmagan"
    await query.edit_message_text(
        "🔗 <b>Auto aniqlash yo'riqnomasi</b>\n\n"
        "<b>1-usul (tavsiya):</b>\n"
        "• Bot admin bo'lgan forum-guruhga boring\n"
        "• Kerakli mavzuga (topic) kiring\n"
        "• <code>/topic_aniqla</code> yuboring\n"
        "• Bot mavzu ID sini ko'rsatadi va biriktirish tugmasini chiqaradi\n\n"
        "<b>2-usul (qo'lda):</b>\n"
        "• Telegram Desktop da forum mavzusiga kiring\n"
        "• URL dagi oxirgi raqam = topic ID\n"
        "• Topic sozlash → bo'limni tanlang → raqamni kiriting\n\n"
        "<b>3-usul (guruh adminlari):</b>\n"
        "• Guruhning ixtiyoriy mavzusida <code>/topic_aniqla@BotName</code> yuboring\n\n"
        f"📡 Guruh ID: {gid_text}\n\n"
        "⚠️ <b>Bot javob bermasa:</b>\n"
        "• Bot guruhda admin emasmi?\n"
        "• Guruhda Topics (Forumlar) yoqilganmi?\n"
        "• Botni guruhdan chiqarib qayta qo'shing",
        parse_mode="HTML",
        reply_markup=kb.InlineKeyboardMarkup([kb.back_button("topic_settings")]),
    )


@role_required("super")
async def settings_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔗 <b>Guruhni ulash</b>\n\n"
        "Bot admin bo'lgan guruhga boring va quyidagi komandasini yuboring:\n\n"
        "<code>/set_group</code>\n\n"
        "Bot guruh ID sini avtomatik saqlab oladi.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([kb.back_button("settings")]),
    )


@role_required("super")
async def backup_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db_path = "bot.db"
    if not os.path.exists(db_path):
        await query.answer("bot.db topilmadi.", show_alert=True)
        return
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open(db_path, "rb"),
        filename="backup_bot.db",
        caption="💾 IQTM Workspace backup",
    )
    await query.edit_message_text(
        "✅ Backup yuborildi.",
        reply_markup=InlineKeyboardMarkup([kb.back_button("settings")])
    )
