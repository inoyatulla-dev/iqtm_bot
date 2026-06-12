"""SQLite bazadan zaxira nusxa olish — ma'lumotlar hech qachon yo'qolmasligi uchun."""
import logging
import shutil
from datetime import datetime
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

BACKUP_DIR = Path(__file__).resolve().parents[2] / "backups"
KEEP_LAST = 7


def _db_path() -> Path | None:
    """`sqlite+aiosqlite:///./iqtm.db` ko'rinishidagi URL'dan fayl yo'lini oladi."""
    url = settings.database_url
    if "sqlite" not in url:
        return None  # PostgreSQL kabi serverli baza — alohida backup kerak
    path = url.split("///")[-1]
    return (Path(__file__).resolve().parents[2] / path).resolve()


def backup_database() -> Path | None:
    """Baza faylini `backend/backups/iqtm_<timestamp>.db` ga nusxalaydi.

    Oxirgi `KEEP_LAST` ta nusxa saqlanadi, eskilari o'chiriladi.
    """
    src = _db_path()
    if not src or not src.exists():
        logger.warning("Baza fayli topilmadi — zaxira o'tkazib yuborildi: %s", src)
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"{src.stem}_{stamp}{src.suffix}"
    shutil.copy2(src, dest)
    logger.info("Baza zaxira nusxasi yaratildi: %s", dest)

    backups = sorted(BACKUP_DIR.glob(f"{src.stem}_*{src.suffix}"))
    for old in backups[:-KEEP_LAST]:
        old.unlink(missing_ok=True)

    return dest
