"""Telegram Mini App autentifikatsiyasi."""
import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep
from app.core.constants import Role, UserStatus
from app.core.security import create_access_token, validate_init_data
from app.models import User
from app.schemas.auth import AuthRequest, AuthResponse
from app.schemas.user import UserOut
from app import notifications as notify

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=AuthResponse)
async def auth_telegram(body: AuthRequest, session: SessionDep):
    try:
        data = validate_init_data(body.init_data)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"initData xato: {e}")

    tg_user = data.get("user")
    if not tg_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Foydalanuvchi ma'lumoti yo'q")

    uid = int(tg_user["id"])
    name = (
        f"{tg_user.get('first_name', '')} {tg_user.get('last_name', '')}".strip()
        or "Foydalanuvchi"
    )
    username = tg_user.get("username")

    user = await session.get(User, uid)
    if not user:
        # Yangi — pending sifatida saqlanadi, boshliqlarga xabar
        user = User(
            id=uid, name=name, username=username,
            role=Role.WORKER, status=UserStatus.PENDING,
        )
        session.add(user)
        await session.flush()
        await _notify_bosses(session, user)
    else:
        # Ism/username yangilanadi
        user.name = name
        user.username = username

    token = create_access_token(user.id, user.role.value)
    return AuthResponse(token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser):
    return user


async def _notify_bosses(session, new_user: User) -> None:
    result = await session.execute(
        select(User).where(User.role == Role.BOSS, User.status == UserStatus.ACTIVE)
    )
    text = (
        f"🔔 <b>Yangi ariza!</b>\n\n"
        f"👤 {new_user.name}\n"
        f"🆔 <code>{new_user.id}</code>\n"
        f"📛 @{new_user.username or '—'}\n\n"
        f"Ilovada tasdiqlang."
    )
    for boss in result.scalars().all():
        await notify.send_dm(boss.id, text)
