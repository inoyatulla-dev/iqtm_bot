"""Telegram orqali xabar yuborish — guruhga (forum mavzu) va shaxsiy.

Past darajali: faqat yuboradi. Matn tayyorlash servislarda.
Xato yuz bersa — log qiladi, lekin API ni to'xtatmaydi.
"""
import logging

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
    if not bot or not settings.group_chat_id:
        return
    kwargs = {
        "chat_id": settings.group_chat_id,
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
