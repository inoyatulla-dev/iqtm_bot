from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import TaskStatus, TaskType
from app.db.base import Base
from app.db.types import EnumCol


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)

    dep_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.id"), default=None
    )
    masul_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), default=None
    )
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))

    deadline: Mapped[date | None] = mapped_column(Date, default=None)
    status: Mapped[TaskStatus] = mapped_column(EnumCol(TaskStatus), default=TaskStatus.NEW)
    type: Mapped[TaskType] = mapped_column(EnumCol(TaskType), default=TaskType.STANDALONE)

    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id"), default=None
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    @property
    def is_overdue(self) -> bool:
        """Kechikkan: muddat o'tgan va hali bajarilmagan."""
        return (
            self.deadline is not None
            and self.status != TaskStatus.DONE
            and self.deadline < date.today()
        )
