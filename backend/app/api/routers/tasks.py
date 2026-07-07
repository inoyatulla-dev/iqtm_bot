"""Vazifalar API — doska, yaratish, tahrirlash, holat, izohlar, biriktirmalar, o'chirish."""
import io
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import delete, func, select

from app import notifications as notify
from app.api.deps import CurrentUser, SessionDep
from app.core import permissions
from app.core.constants import TaskType
from app.models import Attachment, Comment, Log, Project, Task, TaskAssignee, User
from app.schemas.attachment import AttachmentOut
from app.schemas.comment import CommentCreate, CommentOut
from app.schemas.task import AssigneeOut, TaskCreate, TaskOut, TaskStatusUpdate, TaskUpdate
from app.services import board_service, settings_service, task_service
from app.services.upload_service import delete_file, file_extension, save_file

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
async def list_tasks(user: CurrentUser, session: SessionDep):
    """Doska uchun barcha (mos) vazifalar."""
    tasks = await task_service.get_board_tasks(session, user)
    done_keys = await board_service.get_done_keys(session)
    return await _to_out_batch(session, tasks, done_keys)


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: int, user: CurrentUser, session: SessionDep):
    task = await _get_or_404(session, task_id)
    if not permissions.can_view_task(user, task, task.assignee_ids):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
    done_keys = await board_service.get_done_keys(session)
    return (await _to_out_batch(session, [task], done_keys))[0]


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(body: TaskCreate, user: CurrentUser, session: SessionDep):
    # Boshliq oddiy vazifa beradi; xodim faqat shaxsiy
    if body.type == TaskType.PERSONAL:
        if not permissions.can_create_personal_task(user):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Kuzatuvchi vazifa qo'sha olmaydi")
        body.masul_id = user.id
        body.dep_id = body.dep_id or user.dep_id
    elif not permissions.can_create_task(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Vazifa berish faqat boshliq uchun")

    task = await task_service.create_task(session, body, created_by=user.id)
    done_keys = await board_service.get_done_keys(session)
    return (await _to_out_batch(session, [task], done_keys))[0]


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int, body: TaskUpdate, user: CurrentUser, session: SessionDep
):
    task = await _get_or_404(session, task_id)
    if not permissions.can_edit_task(user, task):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tahrirlashga ruxsat yo'q")
    data = body.model_dump(exclude_unset=True)
    assignee_ids = data.pop("assignee_ids", None)
    masul_in = "masul_id" in data
    masul_val = data.pop("masul_id", None)
    for field, value in data.items():
        setattr(task, field, value)
    if assignee_ids is not None or masul_in:
        old_ids = set(task.assignee_ids)
        new_ids = await task_service.set_assignees(
            session, task, masul_val if masul_in else task.masul_id, assignee_ids
        )
        await task_service.reassign_notify(session, task, set(new_ids) - old_ids)
    session.add(Log(user_id=user.id, action=f"Vazifa tahrirlandi: #{task.id}"))
    done_keys = await board_service.get_done_keys(session)
    return (await _to_out_batch(session, [task], done_keys))[0]


@router.patch("/{task_id}/status", response_model=TaskOut)
async def update_status(
    task_id: int, body: TaskStatusUpdate, user: CurrentUser, session: SessionDep
):
    task = await _get_or_404(session, task_id)
    column = await board_service.get_column(session, body.status)
    if not column:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ustun topilmadi")
    if not permissions.can_change_status(user, task, column, task.assignee_ids):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Holatni o'zgartirishga ruxsat yo'q")
    await task_service.change_status(session, task, column, user)
    done_keys = await board_service.get_done_keys(session)
    return (await _to_out_batch(session, [task], done_keys))[0]


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, user: CurrentUser, session: SessionDep):
    task = await _get_or_404(session, task_id)
    if not permissions.can_delete_task(user, task):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "O'chirishga ruxsat yo'q")
    session.add(Log(user_id=user.id, action=f"Vazifa o'chirildi: #{task.id}"))
    await session.execute(
        delete(TaskAssignee).where(TaskAssignee.task_id == task.id)
    )
    await session.delete(task)


# ── Izohlar ──────────────────────────────────────────────
@router.get("/{task_id}/comments", response_model=list[CommentOut])
async def list_comments(task_id: int, user: CurrentUser, session: SessionDep):
    task = await _get_or_404(session, task_id)
    if not permissions.can_view_task(user, task, task.assignee_ids):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
    result = await session.execute(
        select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
    )
    comments = list(result.scalars().all())
    ids = {c.user_id for c in comments} | {c.target_user_id for c in comments if c.target_user_id}
    info = await _author_info(session, ids)
    texts = {c.id: c.text for c in comments}
    return [_comment_out(c, info, texts) for c in comments]


@router.post(
    "/{task_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED
)
async def add_comment(
    task_id: int, body: CommentCreate, user: CurrentUser, session: SessionDep
):
    task = await _get_or_404(session, task_id)
    if not permissions.can_view_task(user, task, task.assignee_ids):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
    text = body.text.strip()
    if not text:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Izoh bo'sh bo'lishi mumkin emas")
    parent_text = ""
    if body.parent_id:
        parent = await session.get(Comment, body.parent_id)
        if parent and parent.task_id == task_id:
            parent_text = parent.text
    comment = Comment(
        task_id=task_id, user_id=user.id, text=text,
        target_user_id=body.target_user_id, parent_id=body.parent_id,
    )
    session.add(comment)
    await session.flush()
    await task_service.notify_comment(session, task, user, text, body.target_user_id)
    info = await _author_info(session, {user.id, body.target_user_id} - {None})
    texts = {body.parent_id: parent_text} if body.parent_id else {}
    return _comment_out(comment, info, texts)


# ── Biriktirmalar (fayllar) ──────────────────────────────
@router.get("/{task_id}/attachments", response_model=list[AttachmentOut])
async def list_attachments(task_id: int, user: CurrentUser, session: SessionDep):
    task = await _get_or_404(session, task_id)
    if not permissions.can_view_task(user, task, task.assignee_ids):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
    result = await session.execute(
        select(Attachment).where(Attachment.task_id == task_id).order_by(Attachment.created_at)
    )
    attachments = list(result.scalars().all())
    names = await _author_names(session, {a.uploaded_by for a in attachments})
    return [_attachment_out(a, names) for a in attachments]


@router.post(
    "/{task_id}/attachments", response_model=AttachmentOut, status_code=status.HTTP_201_CREATED
)
async def upload_attachment(
    task_id: int, user: CurrentUser, session: SessionDep, file: UploadFile = File(...)
):
    task = await _get_or_404(session, task_id)
    if not permissions.can_view_task(user, task, task.assignee_ids):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")

    max_mb = await settings_service.get_max_file_mb(session)
    ext = file_extension(file.filename, default="")
    stored_name = f"{uuid.uuid4().hex}{ext}"
    path, size = await save_file(file, f"attachments/{task_id}", stored_name)
    if size > max_mb * 1024 * 1024:
        delete_file(path)
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Fayl hajmi {max_mb}MB dan oshmasligi kerak"
        )

    attachment = Attachment(
        task_id=task_id,
        uploaded_by=user.id,
        file_name=file.filename or stored_name,
        mime_type=file.content_type,
        size=size,
        file_path=path,
    )
    session.add(attachment)
    await session.flush()
    names = await _author_names(session, {user.id})
    return _attachment_out(attachment, names)


@router.delete("/{task_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    task_id: int, attachment_id: int, user: CurrentUser, session: SessionDep
):
    task = await _get_or_404(session, task_id)
    if not permissions.can_view_task(user, task, task.assignee_ids):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
    attachment = await session.get(Attachment, attachment_id)
    if not attachment or attachment.task_id != task_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fayl topilmadi")
    if not (permissions.is_boss(user) or attachment.uploaded_by == user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "O'chirishga ruxsat yo'q")
    if attachment.file_path:
        delete_file(attachment.file_path)
    await session.delete(attachment)


@router.get("/{task_id}/attachments/{attachment_id}/download")
async def download_attachment(
    task_id: int, attachment_id: int, user: CurrentUser, session: SessionDep
):
    """Faylni yuklab olish — mahalliy bo'lsa /uploads ga yo'naltiradi,
    arxivlangan bo'lsa Telegramdan oqim sifatida uzatadi."""
    task = await _get_or_404(session, task_id)
    if not permissions.can_view_task(user, task, task.assignee_ids):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat yo'q")
    attachment = await session.get(Attachment, attachment_id)
    if not attachment or attachment.task_id != task_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fayl topilmadi")

    if attachment.file_path:
        return RedirectResponse(attachment.file_path)

    if not attachment.telegram_file_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fayl topilmadi")
    data = await notify.download_telegram_file(attachment.telegram_file_id)
    if data is None:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Faylni yuklab olishda xato")
    return StreamingResponse(
        io.BytesIO(data),
        media_type=attachment.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{attachment.file_name}"'},
    )


# ── helpers ──────────────────────────────────────────────
async def _get_or_404(session: SessionDep, task_id: int) -> Task:
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Vazifa topilmadi")
    # Ruxsat tekshiruvlari uchun — barcha biriktirilgan xodimlar (faqat asosiy mas'ul emas)
    result = await session.execute(
        select(TaskAssignee.user_id).where(TaskAssignee.task_id == task_id)
    )
    task.assignee_ids = set(result.scalars().all())
    return task


async def _to_out_batch(
    session: SessionDep, tasks: list[Task], done_keys: set[str]
) -> list[TaskOut]:
    task_ids = [t.id for t in tasks]

    # Har bir vazifaning mas'ullari (assignees)
    assignees_by_task: dict[int, list[int]] = {}
    if task_ids:
        rows = await session.execute(
            select(TaskAssignee.task_id, TaskAssignee.user_id).where(
                TaskAssignee.task_id.in_(task_ids)
            )
        )
        for tid, uid in rows.all():
            assignees_by_task.setdefault(tid, []).append(uid)

    user_ids = {t.masul_id for t in tasks if t.masul_id}
    for ids in assignees_by_task.values():
        user_ids.update(ids)
    info = await _author_info(session, user_ids)

    project_ids = {t.project_id for t in tasks if t.project_id}
    project_names = await _project_names(session, project_ids)

    counts: dict[int, int] = {}
    comment_counts: dict[int, int] = {}
    if task_ids:
        result = await session.execute(
            select(Attachment.task_id, func.count())
            .where(Attachment.task_id.in_(task_ids))
            .group_by(Attachment.task_id)
        )
        counts = dict(result.all())
        result = await session.execute(
            select(Comment.task_id, func.count())
            .where(Comment.task_id.in_(task_ids))
            .group_by(Comment.task_id)
        )
        comment_counts = dict(result.all())

    out_list = []
    for task in tasks:
        out = TaskOut.model_validate(task)
        out.is_overdue = board_service.is_overdue(task, done_keys)
        out.is_archived = board_service.is_archived(task, done_keys)
        masul_info = info.get(task.masul_id) if task.masul_id else None
        out.masul_name = masul_info[0] if masul_info else None
        out.masul_photo = masul_info[1] if masul_info else None
        out.masul_emoji = masul_info[2] if masul_info else None

        # Assignees — asosiy mas'ul birinchi bo'lsin
        ids = assignees_by_task.get(task.id, [])
        if task.masul_id and task.masul_id in ids:
            ids = [task.masul_id] + [i for i in ids if i != task.masul_id]
        out.assignees = [
            AssigneeOut(id=i, name=info[i][0], photo=info[i][1], emoji=info[i][2])
            for i in ids if i in info
        ]

        out.project_name = project_names.get(task.project_id) if task.project_id else None
        out.attachments_count = counts.get(task.id, 0)
        out.comments_count = comment_counts.get(task.id, 0)
        out_list.append(out)
    return out_list


async def _project_names(session: SessionDep, project_ids: set[int]) -> dict[int, str]:
    if not project_ids:
        return {}
    result = await session.execute(
        select(Project.id, Project.name).where(Project.id.in_(project_ids))
    )
    return dict(result.all())


async def _author_names(session: SessionDep, user_ids: set[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    result = await session.execute(select(User.id, User.name).where(User.id.in_(user_ids)))
    return dict(result.all())


async def _author_info(
    session: SessionDep, user_ids: set[int]
) -> dict[int, tuple[str, str | None, str | None]]:
    if not user_ids:
        return {}
    result = await session.execute(
        select(User.id, User.name, User.photo, User.custom_emoji).where(User.id.in_(user_ids))
    )
    return {uid: (name, photo, emoji) for uid, name, photo, emoji in result.all()}


def _comment_out(
    comment: Comment,
    info: dict[int, tuple[str, str | None, str | None]],
    texts: dict[int, str] | None = None,
) -> CommentOut:
    out = CommentOut.model_validate(comment)
    author = info.get(comment.user_id)
    out.user_name = author[0] if author else "—"
    out.user_photo = author[1] if author else None
    if comment.target_user_id:
        target = info.get(comment.target_user_id)
        out.target_name = target[0] if target else None
    if comment.parent_id and texts:
        rt = texts.get(comment.parent_id, "")
        out.reply_to = (rt[:60] + "…") if len(rt) > 60 else rt
    return out


def _attachment_out(attachment: Attachment, names: dict[int, str]) -> AttachmentOut:
    out = AttachmentOut.model_validate(attachment)
    out.uploader_name = names.get(attachment.uploaded_by, "—")
    out.url = attachment.file_path
    return out
