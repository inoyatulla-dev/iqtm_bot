from pydantic import BaseModel, Field


class StatusCounts(BaseModel):
    counts: dict[str, int] = Field(default_factory=dict)
    overdue: int = 0
    total: int = 0


class RatingRow(BaseModel):
    user_id: int
    name: str
    done: int
    active: int
    overdue: int
