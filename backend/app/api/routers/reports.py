"""Statistik hisobotlarni PDF/DOCX formatida yuklab olish va Telegramga yuborish."""
import io

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app import notifications as notify
from app.api.deps import BossUser, DashboardUser, SessionDep
from app.services import report_service
from app.services.report_export import build_docx, build_pdf

router = APIRouter(prefix="/reports", tags=["reports"])

_FORMATS = {
    "pdf": (build_pdf, "application/pdf"),
    "docx": (build_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
}
_PERIODS = {"week", "month", "year"}


@router.get("/{period}.{fmt}")
async def download_report(period: str, fmt: str, _: BossUser, session: SessionDep):
    if period not in _PERIODS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Davr topilmadi")
    builder = _FORMATS.get(fmt)
    if not builder:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Format topilmadi")

    build_fn, media_type = builder
    data = await report_service.collect_report_data(session, period)
    content = build_fn(data)
    filename = f"hisobot_{period}_{data.end.isoformat()}.{fmt}"
    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/send/{period}.{fmt}")
async def send_report(period: str, fmt: str, user: DashboardUser, session: SessionDep):
    """Hisobotni generatsiya qilib so'rovchining shaxsiy Telegram chatiga yuboradi."""
    if period not in _PERIODS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Davr topilmadi")
    builder = _FORMATS.get(fmt)
    if not builder:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Format topilmadi")

    build_fn, _media_type = builder
    data = await report_service.collect_report_data(session, period)
    content = build_fn(data)
    filename = f"hisobot_{period}_{data.end.isoformat()}.{fmt}"
    ok = await notify.send_document_bytes(
        user.id, filename, content, caption=f"📊 {data.period_label} hisobot"
    )
    if not ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Telegramga yuborishda xato")
    return {"ok": True}
