from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskAssignee(Base):
    """Vazifaga biriktirilgan xodimlar (ko'p mas'ul).

    `tasks.masul_id` — asosiy mas'ul (hisobot/KPI/bildirishnoma uchun saqlanadi);
    bu jadval esa vazifa ustida ishlaydigan barcha xodimlarni (shu jumladan
    asosiy mas'ulni) bog'laydi.
    """

    __tablename__ = "task_assignees"

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), primary_key=True
    )
