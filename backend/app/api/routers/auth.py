"""Telegram Mini App autentifikatsiyasi."""
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import select

from app.api.deps import CurrentUser, CurrentUserAny, SessionDep
from app.core.constants import Role, UserStatus
from app.core.security import create_access_token, validate_init_data
from app.models import User
from app.schemas.auth import AuthRequest, AuthResponse, LangUpdate, ProfileUpdate
from app.schemas.user import UserOut, user_out_with_birthday
from app.services import settings_service
from app.services.upload_service import file_extension, save_file, IMAGE_EXTENSIONS
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
        # Username Telegram'dan sinxronlanadi; ismni esa foydalanuvchi
        # ro'yxatdan o'tish formasi/Sozlamada o'zi belgilaydi — qayta yozilmaydi
        user.username = username

    token = create_access_token(user.id, user.role.value)
    return AuthResponse(token=token, user=user_out_with_birthday(user))


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser):
    return user_out_with_birthday(user)


@router.post("/profile", response_model=UserOut)
async def update_profile(
    body: ProfileUpdate, user: CurrentUserAny, session: SessionDep
):
    """Ro'yxatdan o'tish formasi — Ism/Familiya/Tug'ilgan kun (pending bo'lsa ham ishlaydi)."""
    name = f"{body.first_name.strip()} {body.last_name.strip()}".strip()
    if len(name) < 3:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ism kamida 3 harf bo'lsin")
    user.name = name
    if body.birthday is not None:
        user.birthday = body.birthday
    if body.custom_emoji is not None:
        user.custom_emoji = body.custom_emoji
    return user_out_with_birthday(user)


@router.post("/photo", response_model=UserOut)
async def upload_photo(
    user: CurrentUserAny, session: SessionDep, file: UploadFile = File(...)
):
    ext = file_extension(file.filename)
    if ext not in IMAGE_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Faqat rasm fayllari (jpg, png, webp, gif)")
    path, _ = await save_file(file, "avatars", f"{user.id}{ext}")
    user.photo = path
    return user_out_with_birthday(user)


@router.post("/lang", response_model=UserOut)
async def set_lang(body: LangUpdate, user: CurrentUserAny, session: SessionDep):
    if body.lang not in ("uz", "ru", "en"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Til noto'g'ri")
    user.lang = body.lang
    return user_out_with_birthday(user)


async def _notify_bosses(session, new_user: User) -> None:
    result = await session.execute(
        select(User).where(User.role == Role.BOSS, User.status == UserStatus.ACTIVE)
    )
    tpl = await settings_service.get_template(session, "application")
    text = settings_service.render_template(
        tpl,
        name=new_user.name,
        id=new_user.id,
        username=new_user.username or "—",
    )
    for boss in result.scalars().all():
        await notify.send_dm(boss.id, text)

    topic_id = await settings_service.get_routed_topic(session, "application")
    if topic_id:
        await notify.send_to_group(text, topic_id)
