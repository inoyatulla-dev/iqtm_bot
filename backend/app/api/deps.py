"""FastAPI dependency'lar — session, joriy foydalanuvchi, ruxsat."""
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import permissions
from app.core.constants import UserStatus
from app.core.security import decode_access_token
from app.db.base import get_session
from app.models import User

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Avtorizatsiya talab qilinadi"
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))

    user = await session.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Foydalanuvchi topilmadi")
    if user.status == UserStatus.BLOCKED:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Kirishingiz bloklangan")
    if user.status == UserStatus.PENDING:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Arizangiz hali tasdiqlanmagan"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_boss(user: CurrentUser) -> User:
    if not permissions.is_boss(user):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Bu amal faqat boshliq uchun"
        )
    return user


BossUser = Annotated[User, Depends(require_boss)]
