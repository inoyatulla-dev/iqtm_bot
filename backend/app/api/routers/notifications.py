"""Ilova ichi bildirishnomalar API."""
from fastapi import APIRouter, status

from app.api.deps import CurrentUser, SessionDep
from app.schemas.notification import NotificationOut
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
async def list_notifications(user: CurrentUser, session: SessionDep):
    rows = await notification_service.list_for_user(session, user.id)
    out = []
    for n, task_name in rows:
        item = NotificationOut.model_validate(n)
        item.task_name = task_name
        out.append(item)
    return out


@router.get("/unread-count")
async def get_unread_count(user: CurrentUser, session: SessionDep):
    return {"count": await notification_service.unread_count(session, user.id)}


@router.post("/{notif_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(notif_id: int, user: CurrentUser, session: SessionDep):
    await notification_service.mark_read(session, user.id, notif_id)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(user: CurrentUser, session: SessionDep):
    await notification_service.mark_all_read(session, user.id)
