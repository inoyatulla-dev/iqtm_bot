from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BoardColumn(Base):
    """Kanban doskasi ustuni — admin qo'shadi/nomlaydi/tartiblaydi."""

    __tablename__ = "board_columns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(32), unique=True)  # "new", "in_progress", ...
    name: Mapped[str] = mapped_column(String(64))
    emoji: Mapped[str] = mapped_column(String(8), default="📋")
    color: Mapped[str] = mapped_column(String(16), default="#64748b")
    seq: Mapped[int] = mapped_column(Integer, default=1)

    # Yangi vazifalar shu ustunda boshlanadi
    is_initial: Mapped[bool] = mapped_column(Boolean, default=False)
    # "Yakuniy/tasdiqlangan" ustun — faqat boshliq o'tkaza oladi (statistikada "bajarilgan" sanaladi)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    # Vazifa shu ustunga tushganda guruhga/xodimga xabar yuborilsinmi
    notify: Mapped[bool] = mapped_column(Boolean, default=True)
