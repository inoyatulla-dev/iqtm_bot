from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.constants import ProjectStatus
from app.schemas.task import TaskOut


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    status: ProjectStatus
    created_by: int
    created_at: datetime | None = None
    task_count: int = 0
    done_count: int = 0
    percent: int = 0


class ProjectDetail(ProjectOut):
    tasks: list[TaskOut] = []


class ProjectTaskCreate(BaseModel):
    name: str
    masul_id: int | None = None
    dep_id: str | None = None


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    tasks: list[ProjectTaskCreate] = []


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
