"""Bot/guruh sozlamalari va voqea→mavzu yo'naltirishlari — faqat boshliq."""
from fastapi import APIRouter

from app.api.deps import BossUser, SessionDep
from app.config import settings as env_settings
from app.schemas.settings import SettingsOut, SettingsUpdate
from app.services.settings_service import (
    ROUTE_EVENTS,
    get_route,
    get_setting,
    set_setting,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
async def get_settings(_: BossUser, session: SessionDep):
    out = SettingsOut(group_chat_id=await get_setting(session, "group_chat_id") or "")
    # group_chat_id bo'sh bo'lsa — .env dan ko'rsatamiz
    if not out.group_chat_id and env_settings.group_chat_id:
        out.group_chat_id = str(env_settings.group_chat_id)
    for event in ROUTE_EVENTS:
        out.routes[event] = await get_route(session, event)
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
    await session.flush()
    return await get_settings(_, session)
