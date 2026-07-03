from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import TaskType
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

    deadline: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    # Doska ustuni kaliti — BoardColumn.key (moslashtiriladigan, qattiq enum emas)
    status: Mapped[str] = mapped_column(
        String(32), ForeignKey("board_columns.key"), default="new"
    )
    type: Mapped[TaskType] = mapped_column(EnumCol(TaskType), default=TaskType.STANDALONE)

    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id"), default=None
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    # "Yakuniy" ustunga o'tgan vaqt — shundan 24 soat o'tgach vazifa arxivga ko'chadi
    done_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
