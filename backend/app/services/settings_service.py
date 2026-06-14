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
    "overdue", "weekly", "reminder", "application", "birthday",
]

# Fayl/ombor va brend sozlamalari — standart qiymatlar
DEFAULT_MAX_FILE_MB = 10
DEFAULT_STORAGE_LIMIT_GB = 3
DEFAULT_LOGO_PATH = "/logo.png"
DEFAULT_LOGO_SIZE = 40
DEFAULT_ORG_NAME = ""
DEFAULT_TIMEZONE = "Asia/Tashkent"

# Sozlamalarda tanlash mumkin bo'lgan vaqt zonalari
AVAILABLE_TIMEZONES = [
    "Asia/Tashkent",
    "Asia/Almaty",
    "Asia/Bishkek",
    "Asia/Dushanbe",
    "Asia/Ashgabat",
    "Asia/Yekaterinburg",
    "Europe/Moscow",
    "Asia/Dubai",
    "Europe/Istanbul",
    "UTC",
]

# Xabar shablonlari — har bir voqea uchun tahrirlanadigan matn ({var} qoliplari bilan)
TEMPLATE_EVENTS = ROUTE_EVENTS

DEFAULT_TEMPLATES: dict[str, str] = {
    "new_task": (
        "📌 <b>Yangi vazifa #{id}</b>\n"
        "🏢 {department}\n"
        "📝 {name}\n"
        "👤 Mas'ul: {assignee}\n"
        "⏰ Muddat: {deadline}\n"
        "📄 {description}"
    ),
    "status_change": (
        "📌 <b>Vazifa holati o'zgardi</b>\n"
        "🏢 {department}\n"
        "📝 #{id} {name}\n"
        "➡️ {status}\n"
        "👤 O'zgartirdi: {actor}"
    ),
    "done": (
        "✅ <b>Vazifa tasdiqlandi #{id}</b>\n"
        "🏢 {department}\n"
        "📝 {name}\n"
        "👤 Bajaruvchi: {assignee}\n"
        "📣 Qo'ygan: {creator}\n"
        "🔎 Tekshirdi: {checker}\n"
        "💬 {comment}"
    ),
    "reminder": (
        "🔔 <b>Vazifa eslatmasi!</b>\n"
        "📝 #{id}: {name}\n"
        "⏰ Muddat: {deadline}"
    ),
    "overdue": (
        "🚨 <b>Kechikkan vazifalar — {date}</b>\n\n"
        "Jami: {count} ta"
    ),
    "weekly": (
        "📈 <b>Haftalik hisobot — {date}</b>\n\n"
        "Jami: {total} | ✅ {done} | {percent}%"
    ),
    "application": (
        "🔔 <b>Yangi ariza!</b>\n\n"
        "👤 {name}\n"
        "🆔 <code>{id}</code>\n"
        "📛 @{username}\n\n"
        "Ilovada tasdiqlang."
    ),
    "birthday": (
        "🎉🎂 <b>Tug'ilgan kun tabriklari!</b>\n\n"
        "Bugun {name}ning tug'ilgan kuni — tabriklaymiz! 🎁"
    ),
}


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def render_template(template: str, **values) -> str:
    """`{var}` qoliplarini almashtiradi; noma'lum qolip bo'lsa xato bermaydi."""
    return template.format_map(_SafeDict(**values))


async def get_template(session, event: str) -> str:
    """Adminning shablon matnini o'qiydi, bo'lmasa standart matn."""
    val = await get_setting(session, f"tpl_{event}")
    return val or DEFAULT_TEMPLATES.get(event, "")


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


async def get_max_file_mb(session) -> int:
    val = await get_setting(session, "max_file_mb")
    return int(val) if val and val.isdigit() else DEFAULT_MAX_FILE_MB


async def get_storage_limit_gb(session) -> int:
    val = await get_setting(session, "storage_limit_gb")
    return int(val) if val and val.isdigit() else DEFAULT_STORAGE_LIMIT_GB


async def get_archive_channel_id(session) -> int | None:
    val = await get_setting(session, "archive_channel_id")
    try:
        return int(val) if val else None
    except ValueError:
        return None


async def get_logo_path(session) -> str:
    return await get_setting(session, "logo_path") or DEFAULT_LOGO_PATH


async def get_logo_size(session) -> int:
    val = await get_setting(session, "logo_size")
    return int(val) if val and val.isdigit() else DEFAULT_LOGO_SIZE


async def get_logo_doc_path(session) -> str:
    """Hujjatlar (PDF/DOCX) uchun logotip — bo'sh bo'lsa standart logo ishlatiladi."""
    return await get_setting(session, "logo_doc_path") or ""


async def get_org_name(session) -> str:
    return await get_setting(session, "org_name") or DEFAULT_ORG_NAME


async def get_timezone(session) -> str:
    val = await get_setting(session, "timezone")
    return val if val in AVAILABLE_TIMEZONES else DEFAULT_TIMEZONE


def with_cache_bust(path: str) -> str:
    """Yuklangan fayl URL'iga `?v=<mtime>` qo'shadi — brauzer keshini chetlab o'tish uchun."""
    if not path or not path.startswith("/uploads/"):
        return path
    from app.services.upload_service import resolve_path

    try:
        mtime = int(resolve_path(path).stat().st_mtime)
        return f"{path}?v={mtime}"
    except OSError:
        return path
