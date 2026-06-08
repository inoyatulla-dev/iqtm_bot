from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.core.constants import TaskStatus, TaskType


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    dep_id: str | None = None
    masul_id: int | None = None
    created_by: int
    deadline: date | None = None
    status: TaskStatus
    type: TaskType
    project_id: int | None = None
    is_overdue: bool = False
    created_at: datetime | None = None


class TaskCreate(BaseModel):
    name: str
    description: str | None = None
    dep_id: str | None = None
    masul_id: int | None = None
    deadline: date | None = None
    type: TaskType = TaskType.STANDALONE


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    dep_id: str | None = None
    masul_id: int | None = None
    deadline: date | None = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus
