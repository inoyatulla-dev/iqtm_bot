from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ProjectStatus, StageStatus
from app.db.base import Base
from app.db.types import EnumCol


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[ProjectStatus] = mapped_column(EnumCol(ProjectStatus), default=ProjectStatus.ACTIVE)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deadline: Mapped[date | None] = mapped_column(Date, default=None)

    stages: Mapped[list["ProjectStage"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectStage.seq, ProjectStage.id",
    )


class ProjectStage(Base):
    __tablename__ = "project_stages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    seq: Mapped[int] = mapped_column(Integer, default=1)  # navbat (bir xil = parallel)
    dep_id: Mapped[str | None] = mapped_column(ForeignKey("departments.id"), default=None)
    description: Mapped[str] = mapped_column(Text)
    masul_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), default=None
    )
    deadline: Mapped[date | None] = mapped_column(Date, default=None)
    status: Mapped[StageStatus] = mapped_column(EnumCol(StageStatus), default=StageStatus.WAIT)

    project: Mapped["Project"] = relationship(back_populates="stages")
