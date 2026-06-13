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


class DeptProgress(BaseModel):
    dep_id: str
    name: str
    emoji: str
    color: str
    total: int
    done: int
    percent: int


class DistributionSlice(BaseModel):
    key: str
    label: str
    color: str
    percent: int


class DashboardOut(BaseModel):
    total: int = 0
    done: int = 0
    in_progress: int = 0
    overdue: int = 0
    new_this_month: int = 0
    closed_this_month: int = 0
    departments: list[DeptProgress] = Field(default_factory=list)
    distribution: list[DistributionSlice] = Field(default_factory=list)
