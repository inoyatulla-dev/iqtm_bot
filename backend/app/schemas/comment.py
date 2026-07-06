from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_id: int
    user_name: str = "—"          # _comment_out() to'ldiradi
    user_photo: str | None = None  # _comment_out() to'ldiradi
    text: str
    target_user_id: int | None = None
    target_name: str | None = None  # _comment_out() to'ldiradi
    parent_id: int | None = None
    reply_to: str | None = None     # ota-izoh matni (qisqa), _comment_out() to'ldiradi
    created_at: datetime | None = None


class CommentCreate(BaseModel):
    text: str
    target_user_id: int | None = None
    parent_id: int | None = None
