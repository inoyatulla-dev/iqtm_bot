from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Comment(Base):
    """Vazifa ostidagi izoh — tekshirish jarayonida boshliq va xodim yozishadi."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    # Izoh kimga atalgan (DM yuboriladi); NULL — umumiy
    target_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), default=None
    )
    # Reply — qaysi izohga javob
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("comments.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
