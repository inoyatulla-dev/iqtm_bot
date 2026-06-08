from pydantic import BaseModel


class StatusCounts(BaseModel):
    new: int = 0
    in_progress: int = 0
    review: int = 0
    done: int = 0
    overdue: int = 0
    total: int = 0


class RatingRow(BaseModel):
    user_id: int
    name: str
    done: int
    active: int
    overdue: int
