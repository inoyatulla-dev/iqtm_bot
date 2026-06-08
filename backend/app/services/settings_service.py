"""Sozlamalar (key/value) — guruh va topic ID lari shu yerda saqlanadi."""
from app.config import settings as env_settings
from app.db.base import SessionFactory
from app.models import Setting

# Bot /set_group orqali ham, ilova orqali ham sozlanadigan kalitlar
KNOWN_KEYS = ["group_chat_id", "topic_tasks", "topic_reports"]


async def get_setting(session, key: str, default=None):
    row = await session.get(Setting, key)
    return row.value if row else default


async def set_setting(session, key: str, value: str):
    row = await session.get(Setting, key)
    if row:
        row.value = value
    else:
        session.add(Setting(key=key, value=value))


async def get_group_chat_id() -> int:
    """Guruh ID — DB'dan, bo'lmasa .env dan."""
    async with SessionFactory() as session:
        val = await get_setting(session, "group_chat_id")
    if val:
        try:
            return int(val)
        except ValueError:
            pass
    return env_settings.group_chat_id


async def get_topic(key: str) -> int | None:
    async with SessionFactory() as session:
        val = await get_setting(session, key)
    if val and str(val).lstrip("-").isdigit():
        return int(val)
    return None
