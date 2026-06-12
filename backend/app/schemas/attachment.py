from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    uploaded_by: int
    uploader_name: str | None = None
    file_name: str
    mime_type: str | None = None
    size: int
    url: str | None = None
    created_at: datetime | None = None
