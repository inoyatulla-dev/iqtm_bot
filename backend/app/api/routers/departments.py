"""Bo'limlar API — CRUD (faqat boshliq), ro'yxat (hamma)."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import BossUser, CurrentUser, SessionDep
from app.models import Department, User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
)

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentOut])
async def list_departments(_: CurrentUser, session: SessionDep):
    result = await session.execute(select(Department).order_by(Department.id))
    return list(result.scalars().all())


@router.post("", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
async def create_department(body: DepartmentCreate, _: BossUser, session: SessionDep):
    if await session.get(Department, body.id):
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu bo'lim kodi mavjud")
    dep = Department(**body.model_dump())
    session.add(dep)
    await session.flush()
    return dep


@router.patch("/{dep_id}", response_model=DepartmentOut)
async def update_department(
    dep_id: str, body: DepartmentUpdate, _: BossUser, session: SessionDep
):
    dep = await _get_or_404(session, dep_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(dep, field, value)
    return dep


@router.delete("/{dep_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(dep_id: str, _: BossUser, session: SessionDep):
    dep = await _get_or_404(session, dep_id)
    # Ichida xodim bo'lsa — o'chirishni rad etish
    count = await session.scalar(
        select(func.count()).select_from(User).where(User.dep_id == dep_id)
    )
    if count:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Bo'limda {count} ta xodim bor — avval ularni boshqa bo'limga o'tkazing",
        )
    await session.delete(dep)


async def _get_or_404(session: SessionDep, dep_id: str) -> Department:
    dep = await session.get(Department, dep_id)
    if not dep:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bo'lim topilmadi")
    return dep
