from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.constants import Role, UserStatus


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str | None = None
    role: Role
    dep_id: str | None = None
    status: UserStatus
    created_at: datetime | None = None


class UserCreate(BaseModel):
    id: int                      # Telegram user id
    name: str
    username: str | None = None
    role: Role = Role.WORKER
    dep_id: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    role: Role | None = None
    dep_id: str | None = None
    status: UserStatus | None = None
