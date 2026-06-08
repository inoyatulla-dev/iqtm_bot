"""Enum ustunlari uchun yordamchi — qiymat (value) bo'yicha saqlaydi.

native_enum=False → SQLite va PostgreSQL'da VARCHAR + CHECK sifatida ishlaydi.
values_callable → 'worker' saqlanadi, 'WORKER' emas (toza API uchun).
"""
from sqlalchemy import Enum as SAEnum


def EnumCol(enum_cls, length: int = 20):
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        values_callable=lambda e: [m.value for m in e],
    )
