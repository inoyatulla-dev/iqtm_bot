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
    """Guruhda yuborilsa — guruh va mavzu ID larini ko'rsatadi (sozlash uchun)."""
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("Bu komandani guruhda yuboring.")
        return
    thread_id = update.message.message_thread_id
    await update.message.reply_text(
        f"📡 Guruh ID: <code>{chat.id}</code>\n"
        f"🧵 Mavzu (topic) ID: <code>{thread_id or 'yo‘q'}</code>\n\n"
        "Bularni ilovaning sozlamalariga yoki .env ga kiriting.",
        parse_mode="HTML",
    )
