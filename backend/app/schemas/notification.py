from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    task_id: int | None = None
    task_name: str | None = None
    text: str
    is_read: bool
    created_at: datetime
