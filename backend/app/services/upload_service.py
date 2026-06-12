"""Yuklangan fayllarni saqlash — profil rasmi, brend logotipi, vazifa biriktirmalari."""
from pathlib import Path

from fastapi import UploadFile

UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


async def save_file(file: UploadFile, subdir: str, filename: str) -> tuple[str, int]:
    """Faylni uploads/{subdir}/{filename} ga saqlaydi.

    Qaytaradi: (/uploads/... ommaviy yo'l, fayl hajmi baytlarda)
    """
    dest_dir = UPLOADS_DIR / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    content = await file.read()
    dest.write_bytes(content)
    return f"/uploads/{subdir}/{filename}", len(content)


def file_extension(filename: str | None, default: str = ".jpg") -> str:
    ext = Path(filename or "").suffix.lower()
    return ext or default


def resolve_path(public_path: str) -> Path:
    """`/uploads/...` ommaviy yo'lni diskdagi haqiqiy faylga aylantiradi."""
    return UPLOADS_DIR.parent / public_path.lstrip("/")


def delete_file(public_path: str) -> None:
    path = resolve_path(public_path)
    path.unlink(missing_ok=True)
