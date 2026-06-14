"""Bot/guruh sozlamalari va voqea→mavzu yo'naltirishlari — faqat boshliq."""
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import BossUser, SessionDep
from app.config import settings as env_settings
from app.schemas.settings import BrandingOut, SettingsOut, SettingsUpdate
from app.services.settings_service import (
    AVAILABLE_TIMEZONES,
    ROUTE_EVENTS,
    TEMPLATE_EVENTS,
    get_archive_channel_id,
    get_logo_doc_path,
    get_logo_path,
    get_logo_size,
    get_max_file_mb,
    get_org_name,
    get_route,
    get_setting,
    get_storage_limit_gb,
    get_template,
    get_timezone,
    set_setting,
    with_cache_bust,
)
from app.services.upload_service import IMAGE_EXTENSIONS, file_extension, save_file

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/branding", response_model=BrandingOut)
async def get_branding(session: SessionDep):
    """Logotip va vaqt zonasi — barcha foydalanuvchilar (hatto tasdiqlanmagan) uchun ochiq."""
    return BrandingOut(
        logo_path=with_cache_bust(await get_logo_path(session)),
        logo_size=await get_logo_size(session),
        timezone=await get_timezone(session),
    )


@router.get("/timezones", response_model=list[str])
async def list_timezones():
    """Sozlamalarda tanlash mumkin bo'lgan vaqt zonalari ro'yxati."""
    return AVAILABLE_TIMEZONES


@router.get("", response_model=SettingsOut)
async def get_settings(_: BossUser, session: SessionDep):
    out = SettingsOut(group_chat_id=await get_setting(session, "group_chat_id") or "")
    # group_chat_id bo'sh bo'lsa — .env dan ko'rsatamiz
    if not out.group_chat_id and env_settings.group_chat_id:
        out.group_chat_id = str(env_settings.group_chat_id)
    for event in ROUTE_EVENTS:
        out.routes[event] = await get_route(session, event)
    for event in TEMPLATE_EVENTS:
        out.templates[event] = await get_template(session, event)
    out.max_file_mb = await get_max_file_mb(session)
    out.storage_limit_gb = await get_storage_limit_gb(session)
    archive_id = await get_archive_channel_id(session)
    out.archive_channel_id = str(archive_id) if archive_id else ""
    out.logo_path = with_cache_bust(await get_logo_path(session))
    out.logo_size = await get_logo_size(session)
    out.logo_doc_path = with_cache_bust(await get_logo_doc_path(session))
    out.org_name = await get_org_name(session)
    out.timezone = await get_timezone(session)
    return out


@router.put("", response_model=SettingsOut)
async def update_settings(body: SettingsUpdate, _: BossUser, session: SessionDep):
    if body.group_chat_id is not None:
        await set_setting(session, "group_chat_id", body.group_chat_id)
    if body.routes is not None:
        for event, topic_pk in body.routes.items():
            if event not in ROUTE_EVENTS:
                continue
            await set_setting(session, f"route_{event}", str(topic_pk) if topic_pk else "")
    if body.templates is not None:
        for event, text in body.templates.items():
            if event not in TEMPLATE_EVENTS:
                continue
            await set_setting(session, f"tpl_{event}", text.strip())
    if body.max_file_mb is not None:
        await set_setting(session, "max_file_mb", str(body.max_file_mb))
    if body.storage_limit_gb is not None:
        await set_setting(session, "storage_limit_gb", str(body.storage_limit_gb))
    if body.archive_channel_id is not None:
        await set_setting(session, "archive_channel_id", body.archive_channel_id)
    if body.logo_path is not None:
        await set_setting(session, "logo_path", body.logo_path)
    if body.logo_size is not None:
        await set_setting(session, "logo_size", str(body.logo_size))
    if body.org_name is not None:
        await set_setting(session, "org_name", body.org_name.strip())
    if body.timezone is not None:
        if body.timezone not in AVAILABLE_TIMEZONES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Noma'lum vaqt zonasi")
        await set_setting(session, "timezone", body.timezone)
    await session.flush()
    return await get_settings(_, session)


@router.post("/logo", response_model=SettingsOut)
async def upload_logo(boss: BossUser, session: SessionDep, file: UploadFile = File(...)):
    """Dumaloq logotip — mini-ilova sarlavhasida ishlatiladi."""
    ext = file_extension(file.filename, default=".png")
    if ext not in IMAGE_EXTENSIONS and ext != ".svg":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Faqat rasm fayllari (jpg, png, webp, svg)")
    path, _ = await save_file(file, "branding", f"logo{ext}")
    await set_setting(session, "logo_path", path)
    await session.flush()
    return await get_settings(boss, session)


@router.post("/logo-doc", response_model=SettingsOut)
async def upload_logo_doc(boss: BossUser, session: SessionDep, file: UploadFile = File(...)):
    """Original logotip — PDF/DOCX hisobotlarda ishlatiladi."""
    ext = file_extension(file.filename, default=".png")
    if ext not in IMAGE_EXTENSIONS and ext != ".svg":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Faqat rasm fayllari (jpg, png, webp, svg)")
    path, _ = await save_file(file, "branding", f"logo_doc{ext}")
    await set_setting(session, "logo_doc_path", path)
    await session.flush()
    return await get_settings(boss, session)
