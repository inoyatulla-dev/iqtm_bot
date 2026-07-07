"""Jadvallarni yaratish va boshlang'ich ma'lumotlar."""
import logging

from sqlalchemy import select

from app.config import settings
from app.core.constants import Role, UserStatus
from app.db.base import Base, SessionFactory, engine
from app.models import BoardColumn, Department, User

logger = logging.getLogger(__name__)

DEFAULT_DEPARTMENTS = [
    ("el", "Elektronika", "🔌", "#f59e0b"),
    ("ds", "Dasturlash", "💻", "#3b82f6"),
    ("kn", "Konstruktor", "📐", "#8b5cf6"),
    ("us", "Ustaxona", "🔧", "#10b981"),
    ("bo", "Bo'yash", "🎨", "#ef4444"),
]

# (key, name, emoji, color, seq, is_initial, is_done)
DEFAULT_BOARD_COLUMNS = [
    ("new", "Yangi", "🆕", "#64748b", 1, True, False),
    ("in_progress", "Jarayonda", "🔄", "#f59e0b", 2, False, False),
    ("review", "Tekshiruvda", "🔍", "#8b5cf6", 3, False, False),
    ("done", "Bajarildi", "✅", "#10b981", 4, False, True),
]

# Eski sxemada vazifa holati qattiq enum (CHECK) edi — uni BoardColumn'ga ko'chiramiz
_TASK_COLUMNS = (
    "id, name, description, dep_id, masul_id, created_by, deadline, "
    "status, type, project_id, created_at, updated_at"
)


async def _migrate_task_status(conn) -> None:
    """Eski 'tasks.status' CHECK cheklovidan qutilish — jadvalni qayta qurish.

    SQLite ALTER TABLE konstraintni olib tashlay olmaydi, shuning uchun:
    eski jadval boshqa nomga ko'chiriladi → yangi sxema yaratiladi (create_all
    orqali) → ma'lumot ko'chiriladi → eskisi o'chiriladi.
    """
    result = await conn.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'"
    )
    row = result.first()
    if not row or not row[0]:
        return  # jadval hali yo'q — create_all yangi sxemani yaratadi
    if "status in (" not in row[0].lower():
        return  # allaqachon yangi sxema (CHECK status... yo'q)

    logger.info("Eski 'tasks' sxemasi aniqlandi — 'status' ustuni qayta quriladi...")
    await conn.exec_driver_sql("ALTER TABLE tasks RENAME TO tasks_old")


async def _finish_task_migration(conn) -> None:
    result = await conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks_old'"
    )
    if not result.first():
        return
    await conn.exec_driver_sql(
        f"INSERT INTO tasks ({_TASK_COLUMNS}) SELECT {_TASK_COLUMNS} FROM tasks_old"
    )
    await conn.exec_driver_sql("DROP TABLE tasks_old")
    logger.info("'tasks' jadvali muvaffaqiyatli ko'chirildi.")


async def init_models() -> None:
    """Jadvallarni yaratish + yengil migratsiyalar."""
    async with engine.begin() as conn:
        await _migrate_task_status(conn)
        await conn.run_sync(Base.metadata.create_all)
        await _finish_task_migration(conn)
        # Migratsiya: yangi ustunlarni qo'shish (mavjud bazada bo'lmasa)
        for stmt in [
            "ALTER TABLE users ADD COLUMN lang VARCHAR(2) DEFAULT 'uz'",
            "ALTER TABLE board_columns ADD COLUMN notify BOOLEAN DEFAULT 1",
            "ALTER TABLE comments ADD COLUMN target_user_id BIGINT",
            "ALTER TABLE comments ADD COLUMN parent_id INTEGER",
            "ALTER TABLE users ADD COLUMN photo VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN birthday DATE",
            "ALTER TABLE users ADD COLUMN custom_emoji VARCHAR(8)",
            "ALTER TABLE projects ADD COLUMN deadline DATE",
            "ALTER TABLE users ADD COLUMN login VARCHAR(32)",
            "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)",
            "ALTER TABLE tasks ADD COLUMN done_at DATETIME",
            "ALTER TABLE notifications ADD COLUMN is_archived BOOLEAN DEFAULT 0",
        ]:
            try:
                await conn.exec_driver_sql(stmt)
            except Exception:
                pass  # ustun allaqachon mavjud
        try:
            await conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_login ON users(login)"
            )
        except Exception:
            pass
        # done_at endi qo'shildi — allaqachon "yakuniy" ustundagi eski vazifalar uchun
        # updated_at asosida bir martalik to'ldirish (aks holda hech qachon arxivlanmaydi)
        try:
            await conn.exec_driver_sql(
                "UPDATE tasks SET done_at = updated_at "
                "WHERE done_at IS NULL "
                "AND status IN (SELECT key FROM board_columns WHERE is_done = 1)"
            )
        except Exception:
            pass
        await _fix_utc_timestamps(conn)
    logger.info("Jadvallar tayyor.")


# created_at/updated_at avval SQLite "func.now()" (UTC) bilan to'ldirilgan,
# endi Python datetime.now() (server vaqti, Asia/Tashkent, UTC+5) ishlatiladi —
# eski yozuvlarni bir martalik +5 soatga surish bilan moslashtiramiz.
_TZ_FIX_COLUMNS = {
    "users": ["created_at"],
    "comments": ["created_at"],
    "attachments": ["created_at"],
    "logs": ["created_at"],
    "projects": ["created_at"],
    "tasks": ["created_at", "updated_at"],
}


async def _fix_utc_timestamps(conn) -> None:
    result = await conn.exec_driver_sql(
        "SELECT value FROM settings WHERE key='_tz_fix_applied'"
    )
    if result.first():
        return
    for table, cols in _TZ_FIX_COLUMNS.items():
        for col in cols:
            await conn.exec_driver_sql(
                f"UPDATE {table} SET {col} = datetime({col}, '+5 hours') "
                f"WHERE {col} IS NOT NULL"
            )
    await conn.exec_driver_sql(
        "INSERT INTO settings (key, value) VALUES ('_tz_fix_applied', '1')"
    )
    logger.info("Eski created_at/updated_at qiymatlari +5 soatga surildi (UTC -> Tashkent).")


async def seed_data() -> None:
    """Bo'limlar, doska ustunlari va boshliq (owner) — agar mavjud bo'lmasa."""
    async with SessionFactory() as session:
        # Bo'limlar
        for dep_id, name, emoji, color in DEFAULT_DEPARTMENTS:
            exists = await session.get(Department, dep_id)
            if not exists:
                session.add(
                    Department(id=dep_id, name=name, emoji=emoji, color=color)
                )

        # Doska ustunlari
        for key, name, emoji, color, seq, is_initial, is_done in DEFAULT_BOARD_COLUMNS:
            exists = await session.scalar(
                select(BoardColumn).where(BoardColumn.key == key)
            )
            if not exists:
                session.add(
                    BoardColumn(
                        key=key, name=name, emoji=emoji, color=color,
                        seq=seq, is_initial=is_initial, is_done=is_done,
                    )
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
