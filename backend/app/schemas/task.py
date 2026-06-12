from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.constants import TaskType


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    dep_id: str | None = None
    masul_id: int | None = None
    masul_name: str | None = None
    created_by: int
    deadline: datetime | None = None
    status: str
    type: TaskType
    project_id: int | None = None
    is_overdue: bool = False
    attachments_count: int = 0
    created_at: datetime | None = None


class TaskCreate(BaseModel):
    name: str
    description: str | None = None
    dep_id: str | None = None
    masul_id: int | None = None
    deadline: datetime | None = None
    type: TaskType = TaskType.STANDALONE


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    dep_id: str | None = None
    masul_id: int | None = None
    deadline: datetime | None = None


class TaskStatusUpdate(BaseModel):
    status: str
