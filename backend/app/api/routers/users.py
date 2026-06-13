"""Xodimlar API — CRUD, tasdiqlash, bloklash (faqat boshliq)."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app import notifications as notify
from app.api.deps import BossUser, CurrentUser, SessionDep
from app.core.constants import Role, UserStatus
from app.models import Log, User
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(
    user: CurrentUser, session: SessionDep, status_filter: UserStatus | None = None
):
    stmt = select(User).order_by(User.name)
    if user.role == Role.BOSS:
        if status_filter:
            stmt = stmt.where(User.status == status_filter)
    else:
        # Xodim/kuzatuvchi faqat faol foydalanuvchilarni ko'radi
        stmt = stmt.where(User.status == UserStatus.ACTIVE)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreate, boss: BossUser, session: SessionDep):
    if await session.get(User, body.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu foydalanuvchi mavjud")
    user = User(
        id=body.id, name=body.name, username=body.username,
        role=body.role, dep_id=body.dep_id, status=UserStatus.ACTIVE,
    )
    session.add(user)
    session.add(Log(user_id=boss.id, action=f"Xodim qo'shildi: {body.id}"))
    await session.flush()
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int, body: UserUpdate, boss: BossUser, session: SessionDep
):
    user = await _get_or_404(session, user_id)
    data = body.model_dump(exclude_unset=True)

    # Oxirgi boshliqni pasaytirishdan himoya
    if user.role == Role.BOSS and data.get("role") == Role.WORKER:
        await _guard_last_boss(session, user_id)

    for field, value in data.items():
        setattr(user, field, value)
    session.add(Log(user_id=boss.id, action=f"Xodim tahrirlandi: {user_id}"))
    return user


@router.post("/{user_id}/approve", response_model=UserOut)
async def approve_user(
    user_id: int, boss: BossUser, session: SessionDep,
    role: Role = Role.WORKER, dep_id: str | None = None,
):
    user = await _get_or_404(session, user_id)
    was_pending = user.status == UserStatus.PENDING
    user.status = UserStatus.ACTIVE
    user.role = role
    user.dep_id = dep_id
    session.add(Log(user_id=boss.id, action=f"Ariza tasdiqlandi: {user_id}"))
    if was_pending:
        await notify.send_dm(
            user.id,
            "🎉 <b>Arizangiz tasdiqlandi!</b>\n"
            "Ilovani qayta oching — endi to'liq foydalanishingiz mumkin.",
        )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, boss: BossUser, session: SessionDep):
    if user_id == boss.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "O'zingizni o'chira olmaysiz")
    user = await _get_or_404(session, user_id)
    if user.role == Role.BOSS:
        await _guard_last_boss(session, user_id)
    session.add(Log(user_id=boss.id, action=f"Xodim o'chirildi: {user_id}"))
    await session.delete(user)


# ── helpers ──────────────────────────────────────────────
async def _get_or_404(session: SessionDep, user_id: int) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foydalanuvchi topilmadi")
    return user


async def _guard_last_boss(session: SessionDep, user_id: int) -> None:
    result = await session.execute(
        select(User).where(User.role == Role.BOSS, User.status == UserStatus.ACTIVE)
    )
    bosses = [b.id for b in result.scalars().all()]
    if bosses == [user_id]:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Oxirgi boshliqni o'chirib/pasaytirib bo'lmaydi"
        )
