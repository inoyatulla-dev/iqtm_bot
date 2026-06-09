"""Sozlamalar (key/value) — guruh ID va voqea→mavzu yo'naltirishlari shu yerda saqlanadi."""
from app.config import settings as env_settings
from app.db.base import SessionFactory
from app.models import Setting, Topic

# Bot /set_group orqali ham, ilova orqali ham sozlanadigan kalitlar
KNOWN_KEYS = ["group_chat_id"]

# Har bir voqea turi — admin uni nomlangan mavzuga (Topic) yo'naltira oladi.
# Saqlash kaliti: f"route_{event}", qiymati — Topic.id (DB primary key)
ROUTE_EVENTS = [
    "new_task", "status_change", "done",
    "overdue", "weekly", "reminder", "application",
]


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


async def get_route(session, event: str) -> int | None:
    """`route_<event>` sozlamasidagi Topic.id'ni o'qiydi (frontend dropdown uchun)."""
    val = await get_setting(session, f"route_{event}")
    return int(val) if val and val.isdigit() else None


async def get_routed_topic(session, event: str) -> int | None:
    """`route_<event>` → to'g'ridan-to'g'ri Telegram forum-mavzu ID."""
    return await get_route(session, event)
