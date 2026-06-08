from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    user_id: int
    user_name: str = "—"  # Comment ORM'da yo'q — _comment_out() tomonidan to'ldiriladi
    text: str
    created_at: datetime | None = None


class CommentCreate(BaseModel):
    text: str
