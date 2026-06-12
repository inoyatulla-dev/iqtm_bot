"""Saqlash hajmini nazorat qilish — limitdan oshganda eski fayllarni Telegram arxiv kanaliga ko'chiradi."""
import logging

from sqlalchemy import select

from app import notifications as notify
from app.db.base import SessionFactory
from app.models import Attachment
from app.services import settings_service
from app.services.upload_service import UPLOADS_DIR, delete_file, resolve_path

logger = logging.getLogger(__name__)

ATTACHMENTS_DIR = UPLOADS_DIR / "attachments"


def get_attachments_size() -> int:
    if not ATTACHMENTS_DIR.exists():
        return 0
    return sum(f.stat().st_size for f in ATTACHMENTS_DIR.rglob("*") if f.is_file())


async def archive_overflow_files() -> None:
    """Saqlash chegarasidan oshib ketgan eng eski fayllarni arxiv kanaliga ko'chiradi.

    Telegramga muvaffaqiyatli yuklangani tasdiqlangandan keyingina mahalliy
    nusxa o'chiriladi — ma'lumot yo'qolmasligi uchun.
    """
    async with SessionFactory() as session:
        limit_bytes = await settings_service.get_storage_limit_gb(session) * 1024**3
        archive_chat_id = await settings_service.get_archive_channel_id(session)
        if not archive_chat_id:
            return

        total = get_attachments_size()
        if total <= limit_bytes:
            return

        result = await session.execute(
            select(Attachment)
            .where(Attachment.file_path.is_not(None))
            .order_by(Attachment.created_at)
        )
        for attachment in result.scalars().all():
            if total <= limit_bytes:
                break
            path = resolve_path(attachment.file_path)
            if not path.exists():
                attachment.file_path = None
                continue

            size = path.stat().st_size
            sent = await notify.send_document_to_archive(
                archive_chat_id, path, attachment.file_name,
                caption=f"📎 {attachment.file_name} (vazifa #{attachment.task_id})",
            )
            if not sent:
                logger.warning("Faylni arxivlash muvaffaqiyatsiz: %s", attachment.file_path)
                continue

            message_id, file_id = sent
            old_path = attachment.file_path
            attachment.telegram_chat_id = archive_chat_id
            attachment.telegram_message_id = message_id
            attachment.telegram_file_id = file_id
            attachment.file_path = None
            await session.flush()

            delete_file(old_path)
            total -= size
            logger.info("Fayl arxivlandi: %s", old_path)
