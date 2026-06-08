"""Bot/guruh sozlamalari — faqat boshliq."""
from fastapi import APIRouter

from app.api.deps import BossUser, SessionDep
from app.config import settings as env_settings
from app.schemas.settings import SettingsOut, SettingsUpdate
from app.services.settings_service import KNOWN_KEYS, get_setting, set_setting

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
async def get_settings(_: BossUser, session: SessionDep):
    out = SettingsOut()
    for key in KNOWN_KEYS:
        val = await get_setting(session, key)
        if val is not None:
            setattr(out, key, val)
    # group_chat_id bo'sh bo'lsa — .env dan ko'rsatamiz
    if not out.group_chat_id and env_settings.group_chat_id:
        out.group_chat_id = str(env_settings.group_chat_id)
    return out


@router.put("", response_model=SettingsOut)
async def update_settings(body: SettingsUpdate, _: BossUser, session: SessionDep):
    for key, value in body.model_dump(exclude_unset=True).items():
        await set_setting(session, key, value or "")
    await session.flush()
    return await get_settings(_, session)
