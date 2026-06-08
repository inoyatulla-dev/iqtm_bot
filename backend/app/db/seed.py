"""Jadvallarni yaratish va boshlang'ich ma'lumotlar."""
import logging

from sqlalchemy import select

from app.config import settings
from app.core.constants import Role, UserStatus
from app.db.base import Base, SessionFactory, engine
from app.models import Department, User

logger = logging.getLogger(__name__)

DEFAULT_DEPARTMENTS = [
    ("el", "Elektronika", "🔌", "#f59e0b"),
    ("ds", "Dasturlash", "💻", "#3b82f6"),
    ("kn", "Konstruktor", "📐", "#8b5cf6"),
    ("us", "Ustaxona", "🔧", "#10b981"),
    ("bo", "Bo'yash", "🎨", "#ef4444"),
]


async def init_models() -> None:
    """Dev rejim uchun jadvallarni yaratish (prod'da Alembic ishlatiladi)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Jadvallar tayyor.")


async def seed_data() -> None:
    """Bo'limlar va boshliq (owner) — agar mavjud bo'lmasa."""
    async with SessionFactory() as session:
        # Bo'limlar
        for dep_id, name, emoji, color in DEFAULT_DEPARTMENTS:
            exists = await session.get(Department, dep_id)
            if not exists:
                session.add(
                    Department(id=dep_id, name=name, emoji=emoji, color=color)
                )

        # Boshliq
        if settings.owner_id:
            owner = await session.get(User, settings.owner_id)
            if not owner:
                session.add(
                    User(
                        id=settings.owner_id,
                        name="Boshliq",
                        role=Role.BOSS,
                        status=UserStatus.ACTIVE,
                    )
                )
        await session.commit()
    logger.info("Boshlang'ich ma'lumotlar tayyor.")
