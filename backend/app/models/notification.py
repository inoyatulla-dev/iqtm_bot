from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notification(Base):
    """Ilova ichi bildirishnoma (Telegram DM bilan birga yuboriladi)."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(32))
    task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), default=None
    )
    text: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
