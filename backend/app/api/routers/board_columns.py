"""Doska ustunlari API — CRUD va tartiblash (faqat boshliq), ro'yxat (hamma)."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import BossUser, CurrentUser, SessionDep
from app.models import BoardColumn, Task
from app.schemas.board_column import (
    BoardColumnCreate,
    BoardColumnOut,
    BoardColumnReorder,
    BoardColumnUpdate,
)
from app.services import board_service

router = APIRouter(prefix="/board-columns", tags=["board-columns"])


@router.get("", response_model=list[BoardColumnOut])
async def list_columns(_: CurrentUser, session: SessionDep):
    return await board_service.list_columns(session)


@router.post("", response_model=BoardColumnOut, status_code=status.HTTP_201_CREATED)
async def create_column(body: BoardColumnCreate, _: BossUser, session: SessionDep):
    if await board_service.get_column(session, body.key):
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu kalit bilan ustun mavjud")
    max_seq = await session.scalar(select(func.max(BoardColumn.seq))) or 0
    col = BoardColumn(**body.model_dump(), seq=max_seq + 1)
    session.add(col)
    await session.flush()
    return col


@router.patch("/{key}", response_model=BoardColumnOut)
async def update_column(
    key: str, body: BoardColumnUpdate, _: BossUser, session: SessionDep
):
    col = await _get_or_404(session, key)
    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(col, field, value)
    return col


@router.post("/{key}/make-initial", response_model=BoardColumnOut)
async def make_initial(key: str, _: BossUser, session: SessionDep):
    """Boshlang'ich ustunni belgilash — yangi vazifalar shu yerda paydo bo'ladi."""
    col = await _get_or_404(session, key)
    for c in await board_service.list_columns(session):
        c.is_initial = c.key == key
    return col


@router.put("/reorder", response_model=list[BoardColumnOut])
async def reorder_columns(body: BoardColumnReorder, _: BossUser, session: SessionDep):
    columns = {c.key: c for c in await board_service.list_columns(session)}
    if set(body.keys) != set(columns):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Kalitlar ro'yxati to'liq emas")
    for i, key in enumerate(body.keys, start=1):
        columns[key].seq = i
    await session.flush()
    return await board_service.list_columns(session)


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(key: str, _: BossUser, session: SessionDep):
    col = await _get_or_404(session, key)
    count = await session.scalar(
        select(func.count()).select_from(Task).where(Task.status == key)
    )
    if count:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Bu ustunda {count} ta vazifa bor — avval ularni boshqa ustunga o'tkazing",
        )
    if col.is_initial:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Boshlang'ich ustunni o'chirib bo'lmaydi — avval boshqasini boshlang'ich qiling",
        )
    await session.delete(col)


async def _get_or_404(session: SessionDep, key: str) -> BoardColumn:
    col = await board_service.get_column(session, key)
    if not col:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ustun topilmadi")
    return col
