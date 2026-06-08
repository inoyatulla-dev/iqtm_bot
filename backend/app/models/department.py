from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # qisqa kod: el, ds
    name: Mapped[str] = mapped_column(String(255))
    emoji: Mapped[str] = mapped_column(String(16), default="🏢")
    color: Mapped[str] = mapped_column(String(16), default="#2481cc")  # doska rangi
    topic_id: Mapped[int | None] = mapped_column(default=None)  # forum mavzu ID

    members: Mapped[list["User"]] = relationship(  # noqa: F821
        back_populates="department",
        foreign_keys="User.dep_id",
        viewonly=True,
    )
