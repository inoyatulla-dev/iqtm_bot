from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Attachment(Base):
    """Vazifaga biriktirilgan fayl.

    Fayl serverda (uploads/) yoki — ombor to'lganda — Telegram arxiv
    kanalida (telegram_chat_id + telegram_message_id) saqlanadi.
    """

    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    uploaded_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))

    file_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(128), default=None)
    size: Mapped[int] = mapped_column(Integer, default=0)

    # Serverda saqlanganda — nisbiy yo'l (uploads/...); arxivlangan bo'lsa — NULL
    file_path: Mapped[str | None] = mapped_column(String(512), default=None)
    # Telegram arxiv kanalidagi xabar (fayl serverdan o'chirilgan bo'lsa)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    telegram_message_id: Mapped[int | None] = mapped_column(Integer, default=None)
    telegram_file_id: Mapped[str | None] = mapped_column(String(255), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
