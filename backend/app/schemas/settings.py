from pydantic import BaseModel


class SettingsOut(BaseModel):
    group_chat_id: str = ""
    topic_tasks: str = ""
    topic_reports: str = ""


class SettingsUpdate(BaseModel):
    group_chat_id: str | None = None
    topic_tasks: str | None = None
    topic_reports: str | None = None
