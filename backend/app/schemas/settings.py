from pydantic import BaseModel, Field


class SettingsOut(BaseModel):
    group_chat_id: str = ""
    routes: dict[str, int | None] = Field(default_factory=dict)


class SettingsUpdate(BaseModel):
    group_chat_id: str | None = None
    routes: dict[str, int | None] | None = None
