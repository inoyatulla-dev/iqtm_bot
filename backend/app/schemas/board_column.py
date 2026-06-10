from pydantic import BaseModel, ConfigDict


class BoardColumnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    name: str
    emoji: str
    color: str
    seq: int
    is_initial: bool
    is_done: bool
    notify: bool = True


class BoardColumnCreate(BaseModel):
    key: str
    name: str
    emoji: str = "📋"
    color: str = "#64748b"
    is_done: bool = False
    notify: bool = True


class BoardColumnUpdate(BaseModel):
    name: str | None = None
    emoji: str | None = None
    color: str | None = None
    is_done: bool | None = None
    notify: bool | None = None


class BoardColumnReorder(BaseModel):
    keys: list[str]  # yangi tartibdagi kalitlar ro'yxati
