from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Role, UserStatus
from app.db.base import Base
from app.db.types import EnumCol


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user id
    name: Mapped[str] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255), default=None)
    role: Mapped[Role] = mapped_column(EnumCol(Role), default=Role.WORKER)
    dep_id: Mapped[str | None] = mapped_column(
        ForeignKey("departments.id"), default=None
    )
    status: Mapped[UserStatus] = mapped_column(EnumCol(UserStatus), default=UserStatus.PENDING)
    lang: Mapped[str] = mapped_column(String(2), default="uz")
    photo: Mapped[str | None] = mapped_column(String(255), default=None)
    birthday: Mapped[date | None] = mapped_column(Date, default=None)
    custom_emoji: Mapped[str | None] = mapped_column(String(8), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    department: Mapped["Department"] = relationship(  # noqa: F821
        back_populates="members", foreign_keys=[dep_id]
    )
