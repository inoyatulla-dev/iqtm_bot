from pydantic import BaseModel, ConfigDict


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    emoji: str
    color: str
    topic_id: int | None = None


class DepartmentCreate(BaseModel):
    id: str
    name: str
    emoji: str = "🏢"
    color: str = "#2481cc"


class DepartmentUpdate(BaseModel):
    name: str | None = None
    emoji: str | None = None
    color: str | None = None
    topic_id: int | None = None
