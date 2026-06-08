"""Vazifalar API — doska, yaratish, tahrirlash, holat, o'chirish."""
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.core import permissions
from app.core.constants import TaskType
from app.models import Log, Task
from app.schemas.task import TaskCreate, TaskOut, TaskStatusUpdate, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
async def list_tasks(user: CurrentUser, session: SessionDep):
    """Doska uchun barcha (mos) vazifalar."""
    tasks = await task_service.get_board_tasks(session, user)
    return [_to_out(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, user: CurrentUser, session: SessionDep):
    task = await _get_or_404(session, task_id)
    if not permissions.can_view_task(user, task):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
    return _to_out(task)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(body: TaskCreate, user: CurrentUser, session: SessionDep):
    # Boshliq oddiy vazifa beradi; xodim faqat shaxsiy
    if body.type == TaskType.PERSONAL:
        body.masul_id = user.id
        body.dep_id = body.dep_id or user.dep_id
    elif not permissions.can_create_task(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Vazifa berish faqat boshliq uchun")

    task = await task_service.create_task(session, body, created_by=user.id)
    return _to_out(task)


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int, body: TaskUpdate, user: CurrentUser, session: SessionDep
):
    task = await _get_or_404(session, task_id)
    if not permissions.can_edit_task(user, task):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tahrirlashga ruxsat yo'q")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    session.add(Log(user_id=user.id, action=f"Vazifa tahrirlandi: #{task.id}"))
    return _to_out(task)


@router.patch("/{task_id}/status", response_model=TaskOut)
async def update_status(
    task_id: int, body: TaskStatusUpdate, user: CurrentUser, session: SessionDep
):
    task = await _get_or_404(session, task_id)
    if not permissions.can_change_status(user, task):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Holatni o'zgartirishga ruxsat yo'q")
    await task_service.change_status(session, task, body.status, user)
    return _to_out(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, user: CurrentUser, session: SessionDep):
    task = await _get_or_404(session, task_id)
    if not permissions.can_delete_task(user, task):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "O'chirishga ruxsat yo'q")
    session.add(Log(user_id=user.id, action=f"Vazifa o'chirildi: #{task.id}"))
    await session.delete(task)


# ── helpers ──────────────────────────────────────────────
async def _get_or_404(session: SessionDep, task_id: int) -> Task:
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vazifa topilmadi")
    return task


def _to_out(task: Task) -> TaskOut:
    out = TaskOut.model_validate(task)
    out.is_overdue = task.is_overdue
    return out
