from pydantic import BaseModel, Field


class SettingsOut(BaseModel):
    group_chat_id: str = ""
    routes: dict[str, int | None] = Field(default_factory=dict)
    templates: dict[str, str] = Field(default_factory=dict)
    max_file_mb: int = 10
    storage_limit_gb: int = 3
    archive_channel_id: str = ""
    logo_path: str = "/logo.png"
    logo_size: int = 40
    logo_doc_path: str = ""
    org_name: str = ""
    timezone: str = "Asia/Tashkent"


class BrandingOut(BaseModel):
    logo_path: str = "/logo.png"
    logo_size: int = 40
    timezone: str = "Asia/Tashkent"


class SettingsUpdate(BaseModel):
    group_chat_id: str | None = None
    routes: dict[str, int | None] | None = None
    templates: dict[str, str] | None = None
    max_file_mb: int | None = None
    storage_limit_gb: int | None = None
    archive_channel_id: str | None = None
    logo_path: str | None = None
    logo_size: int | None = None
    org_name: str | None = None
    timezone: str | None = None
