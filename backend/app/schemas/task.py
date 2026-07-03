from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.constants import TaskType


class AssigneeOut(BaseModel):
    id: int
    name: str
    photo: str | None = None
    emoji: str | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    dep_id: str | None = None
    masul_id: int | None = None
    masul_name: str | None = None
    masul_photo: str | None = None
    masul_emoji: str | None = None
    assignees: list[AssigneeOut] = []
    created_by: int
    deadline: datetime | None = None
    status: str
    type: TaskType
    project_id: int | None = None
    project_name: str | None = None
    is_overdue: bool = False
    is_archived: bool = False
    attachments_count: int = 0
    comments_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    done_at: datetime | None = None


class TaskCreate(BaseModel):
    name: str
    description: str | None = None
    dep_id: str | None = None
    masul_id: int | None = None
    assignee_ids: list[int] | None = None
    deadline: datetime | None = None
    type: TaskType = TaskType.STANDALONE
    project_id: int | None = None


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    dep_id: str | None = None
    masul_id: int | None = None
    assignee_ids: list[int] | None = None
    deadline: datetime | None = None
    project_id: int | None = None


class TaskStatusUpdate(BaseModel):
    status: str
