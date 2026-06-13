"""Telegram orqali xabar yuborish — guruhga (forum mavzu) va shaxsiy.

Past darajali: faqat yuboradi. Matn tayyorlash servislarda.
Xato yuz bersa — log qiladi, lekin API ni to'xtatmaydi.
"""
import io
import logging
from pathlib import Path

from telegram import Bot
from telegram.constants import ParseMode

from app.config import settings

logger = logging.getLogger(__name__)

_bot: Bot | None = None


def get_bot() -> Bot | None:
    global _bot
    if not settings.bot_token:
        return None
    if _bot is None:
        _bot = Bot(token=settings.bot_token)
    return _bot


async def send_to_group(text: str, topic_id: int | None = None) -> None:
    bot = get_bot()
    if not bot:
        return
    # Guruh ID — DB sozlamasidan (bo'lmasa .env dan)
    from app.services.settings_service import get_group_chat_id

    group_id = await get_group_chat_id()
    if not group_id:
        return
    kwargs = {
        "chat_id": group_id,
        "text": text,
        "parse_mode": ParseMode.HTML,
    }
    if topic_id:
        kwargs["message_thread_id"] = topic_id
    try:
        await bot.send_message(**kwargs)
    except Exception as e:
        logger.warning("Guruhga xabar yuborilmadi: %s", e)


async def send_dm(user_id: int, text: str) -> None:
    bot = get_bot()
    if not bot:
        return
    try:
        await bot.send_message(
            chat_id=user_id, text=text, parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.warning("Shaxsiy xabar yuborilmadi (%s): %s", user_id, e)


async def send_document_to_archive(
    chat_id: int, path: Path, filename: str, caption: str = ""
) -> tuple[int, str] | None:
    """Faylni arxiv kanaliga yuboradi. Muvaffaqiyatli bo'lsa (message_id, file_id)."""
    bot = get_bot()
    if not bot:
        return None
    try:
        with open(path, "rb") as f:
            msg = await bot.send_document(
                chat_id=chat_id, document=f, filename=filename, caption=caption
            )
        if not msg.document:
            return None
        return msg.message_id, msg.document.file_id
    except Exception as e:
        logger.warning("Faylni arxivga yuklashda xato: %s", e)
        return None


async def send_document_bytes(
    chat_id: int, filename: str, data: bytes, caption: str = ""
) -> bool:
    """Xotiradagi faylni foydalanuvchi shaxsiy chatiga yuboradi."""
    bot = get_bot()
    if not bot:
        return False
    try:
        await bot.send_document(
            chat_id=chat_id,
            document=io.BytesIO(data),
            filename=filename,
            caption=caption,
        )
        return True
    except Exception as e:
        logger.warning("Hisobotni Telegramga yuborishda xato (%s): %s", chat_id, e)
        return False


async def download_telegram_file(file_id: str) -> bytes | None:
    """Arxivlangan faylni Telegram serveridan yuklab oladi."""
    bot = get_bot()
    if not bot:
        return None
    try:
        tg_file = await bot.get_file(file_id)
        data = await tg_file.download_as_bytearray()
        return bytes(data)
    except Exception as e:
        logger.warning("Faylni Telegramdan yuklab olishda xato: %s", e)
        return None
