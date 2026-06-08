from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Topic(Base):
    """Admin nomlagan forum-mavzu — bildirishnomalarni yo'naltirish uchun."""

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64))       # "Vazifalar", "Hisobotlar", ...
    topic_id: Mapped[int] = mapped_column(Integer)      # Telegram forum mavzu ID
