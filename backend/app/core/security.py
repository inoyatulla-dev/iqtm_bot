"""Telegram initData tekshiruvi (HMAC) va JWT token.

Oqim:
  Mini App → initData → /auth/telegram → tekshiriladi → JWT beriladi
  Keyingi so'rovlar → Authorization: Bearer <JWT>
"""
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl

import jwt

from app.config import settings

# initData necha soniyagacha amal qiladi (eskirgan ma'lumotni rad etish)
INIT_DATA_MAX_AGE = 24 * 3600  # 24 soat


def validate_init_data(init_data: str) -> dict:
    """Telegram WebApp initData ni tekshiradi va parse qiladi.

    Qaytaradi: parse qilingan ma'lumot (user dict bilan).
    Xato bo'lsa: ValueError.
    """
    if not init_data:
        raise ValueError("initData bo'sh")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("hash topilmadi")

    # data_check_string: kalitlar alifbo tartibida, key=value, \n bilan birlashtirilgan
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(
        b"WebAppData", settings.bot_token.encode(), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("initData imzosi noto'g'ri")

    # Eskirganligini tekshirish
    auth_date = int(parsed.get("auth_date", "0"))
    if auth_date and (time.time() - auth_date) > INIT_DATA_MAX_AGE:
        raise ValueError("initData eskirgan")

    # user JSON sifatida keladi
    if "user" in parsed:
        parsed["user"] = json.loads(parsed["user"])

    return parsed


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """JWT ni ochadi. Xato bo'lsa: ValueError."""
    try:
        return jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as e:
        raise ValueError(f"Token noto'g'ri: {e}")
