"""Bot handlerlari — yengil. Asosiy ish Mini App ichida."""
import logging
from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.ext import ContextTypes

from app.config import settings

logger = logging.getLogger(__name__)

# ── Bot matnlari (3 til) ────────────────────────────────
WELCOME = {
    "uz": "🤖 <b>IQTM Workspace</b>\n\nInnovatsiyalarni qo'llab-quvvatlash va tijoratlashtirish markazi jamoasini boshqarish ilovasi.\nQuyidagi tugma orqali oching 👇",
    "ru": "🤖 <b>IQTM Workspace</b>\n\nПриложение для управления командой Центра поддержки инноваций и коммерциализации.\nОткройте по кнопке ниже 👇",
    "en": "🤖 <b>IQTM Workspace</b>\n\nInnovation Support and Commercialization Center team management app.\nOpen it with the button below 👇",
}
OPEN_BTN = {"uz": "🚀 Ilovani ochish", "ru": "🚀 Открыть приложение", "en": "🚀 Open app"}
NO_URL = {
    "uz": "⚠️ Ilova manzili sozlanmagan. Administrator bilan bog'laning.",
    "ru": "⚠️ Адрес приложения не настроен. Свяжитесь с администратором.",
    "en": "⚠️ App URL is not configured. Contact the administrator.",
}
CHOOSE = "🌐 Tilni tanlang / Выберите язык / Choose language:"


def _lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang:uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"),
        ]
    ])


def _open_kb(lang: str) -> InlineKeyboardMarkup | None:
    if not settings.webapp_url:
        return None
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(OPEN_BTN[lang], web_app=WebAppInfo(url=settings.webapp_url))]]
    )


async def _save_lang(user, lang: str):
    """Foydalanuvchi tilini DB ga saqlash (yangi bo'lsa pending yaratish)."""
    from app.core.constants import UserStatus
    from app.db.base import SessionFactory
    from app.models import User

    async with SessionFactory() as session:
        db_user = await session.get(User, user.id)
        if db_user:
            db_user.lang = lang
        else:
            name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Foydalanuvchi"
            session.add(User(
                id=user.id, name=name, username=user.username,
                status=UserStatus.PENDING, lang=lang,
                created_at=datetime.now(),
            ))
        await session.commit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Til tanlash tugmalarini ko'rsatadi."""
    await update.message.reply_text(CHOOSE, reply_markup=_lang_kb())


async def lang_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split(":")[1]
    await _save_lang(query.from_user, lang)

    kb = _open_kb(lang)
    text = WELCOME[lang] if kb else NO_URL[lang]
    await query.edit_message_text(text, parse_mode="HTML", reply_markup=kb)


async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruhda yuborilsa — guruh ID ni DB ga saqlaydi va mavzu ID ni ko'rsatadi."""
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("Bu komandani guruhda yuboring.")
        return
    thread_id = update.message.message_thread_id
    thread_label = str(thread_id) if thread_id else "yo'q"

    from app.db.base import SessionFactory
    from app.services.settings_service import set_setting

    async with SessionFactory() as session:
        await set_setting(session, "group_chat_id", str(chat.id))
        await session.commit()

    await update.message.reply_text(
        f"✅ Guruh ID saqlandi: <code>{chat.id}</code>\n"
        f"🧵 Bu mavzu (topic) ID: <code>{thread_label}</code>\n\n"
        "Topic ID larni ilova → Sozlama bo'limiga kiriting.",
        parse_mode="HTML",
    )
