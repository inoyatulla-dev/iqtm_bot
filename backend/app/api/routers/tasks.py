"""Vazifalar API — doska, yaratish, tahrirlash, holat, izohlar, o'chirish."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep
from app.core import permissions
from app.core.constants import TaskType
from app.models import Comment, Log, Task, User
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.task import TaskCreate, TaskOut, TaskStatusUpdate, TaskUpdate
from app.services import board_service, task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
async def list_tasks(user: CurrentUser, session: SessionDep):
    """Doska uchun barcha (mos) vazifalar."""
    tasks = await task_service.get_board_tasks(session, user)
    done_keys = await board_service.get_done_keys(session)
    return [_to_out(t, done_keys) for t in tasks]


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, user: CurrentUser, session: SessionDep):
    task = await _get_or_404(session, task_id)
    if not permissions.can_view_task(user, task):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
    done_keys = await board_service.get_done_keys(session)
    return _to_out(task, done_keys)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(body: TaskCreate, user: CurrentUser, session: SessionDep):
    # Boshliq oddiy vazifa beradi; xodim faqat shaxsiy
    if body.type == TaskType.PERSONAL:
        body.masul_id = user.id
        body.dep_id = body.dep_id or user.dep_id
    elif not permissions.can_create_task(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Vazifa berish faqat boshliq uchun")

    task = await task_service.create_task(session, body, created_by=user.id)
    done_keys = await board_service.get_done_keys(session)
    return _to_out(task, done_keys)


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
    done_keys = await board_service.get_done_keys(session)
    return _to_out(task, done_keys)


@router.patch("/{task_id}/status", response_model=TaskOut)
async def update_status(
    task_id: int, body: TaskStatusUpdate, user: CurrentUser, session: SessionDep
):
    task = await _get_or_404(session, task_id)
    column = await board_service.get_column(session, body.status)
    if not column:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ustun topilmadi")
    if not permissions.can_change_status(user, task, column):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Holatni o'zgartirishga ruxsat yo'q")
    await task_service.change_status(session, task, column, user)
    done_keys = await board_service.get_done_keys(session)
    return _to_out(task, done_keys)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, user: CurrentUser, session: SessionDep):
    task = await _get_or_404(session, task_id)
    if not permissions.can_delete_task(user, task):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "O'chirishga ruxsat yo'q")
    session.add(Log(user_id=user.id, action=f"Vazifa o'chirildi: #{task.id}"))
    await session.delete(task)


# ── Izohlar ──────────────────────────────────────────────
@router.get("/{task_id}/comments", response_model=list[CommentOut])
async def list_comments(task_id: int, user: CurrentUser, session: SessionDep):
    task = await _get_or_404(session, task_id)
    if not permissions.can_view_task(user, task):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
    result = await session.execute(
        select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
    )
    comments = list(result.scalars().all())
    names = await _author_names(session, {c.user_id for c in comments})
    return [_comment_out(c, names) for c in comments]


@router.post(
    "/{task_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED
)
async def add_comment(
    task_id: int, body: CommentCreate, user: CurrentUser, session: SessionDep
):
    task = await _get_or_404(session, task_id)
    if not permissions.can_view_task(user, task):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
    text = body.text.strip()
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Izoh bo'sh bo'lishi mumkin emas")
    comment = Comment(task_id=task_id, user_id=user.id, text=text)
    session.add(comment)
    await session.flush()
    await task_service.notify_comment(session, task, user, text)
    return _comment_out(comment, {user.id: user.name})


# ── helpers ──────────────────────────────────────────────
async def _get_or_404(session: SessionDep, task_id: int) -> Task:
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vazifa topilmadi")
    return task


def _to_out(task: Task, done_keys: set[str]) -> TaskOut:
    out = TaskOut.model_validate(task)
    out.is_overdue = board_service.is_overdue(task, done_keys)
    return out


async def _author_names(session: SessionDep, user_ids: set[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    result = await session.execute(select(User.id, User.name).where(User.id.in_(user_ids)))
    return dict(result.all())


def _comment_out(comment: Comment, names: dict[int, str]) -> CommentOut:
    out = CommentOut.model_validate(comment)
    out.user_name = names.get(comment.user_id, "—")
    return out
