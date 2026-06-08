"""Bot handlerlari — yengil. Asosiy ish Mini App ichida."""
import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    WebAppInfo,
)
from telegram.ext import ContextTypes

from app.config import settings

logger = logging.getLogger(__name__)


def _open_app_kb() -> InlineKeyboardMarkup | None:
    if not settings.webapp_url:
        return None
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🚀 Ilovani ochish", web_app=WebAppInfo(url=settings.webapp_url))]]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = _open_app_kb()
    text = (
        "🤖 <b>IQTM Workspace</b>\n\n"
        "ICT Markaz jamoasini boshqarish ilovasi.\n"
        "Quyidagi tugma orqali ilovani oching 👇"
    )
    if not kb:
        text = (
            "🤖 <b>IQTM Workspace</b>\n\n"
            "⚠️ Ilova manzili (WEBAPP_URL) sozlanmagan. "
            "Administrator sozlamasini kutib turing."
        )
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=kb)


async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruhda yuborilsa — guruh ID ni DB ga saqlaydi va mavzu ID ni ko'rsatadi."""
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("Bu komandani guruhda yuboring.")
        return
    thread_id = update.message.message_thread_id

    # Guruh ID ni DB ga avtomatik saqlash
    from app.db.base import SessionFactory
    from app.services.settings_service import set_setting

    async with SessionFactory() as session:
        await set_setting(session, "group_chat_id", str(chat.id))
        await session.commit()

    await update.message.reply_text(
        f"✅ Guruh ID saqlandi: <code>{chat.id}</code>\n"
        f"🧵 Bu mavzu (topic) ID: <code>{thread_id or 'yo‘q'}</code>\n\n"
        "Topic ID larni ilova → Sozlama bo'limiga kiriting.",
        parse_mode="HTML",
    )
