from pydantic import BaseModel, ConfigDict


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    topic_id: int


class TopicCreate(BaseModel):
    name: str
    topic_id: int


class TopicUpdate(BaseModel):
    name: str | None = None
    topic_id: int | None = None
