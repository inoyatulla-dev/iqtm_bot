from datetime import date

from pydantic import BaseModel

from app.schemas.user import UserOut


class AuthRequest(BaseModel):
    init_data: str  # Telegram WebApp.initData (raw query string)


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class LoginRequest(BaseModel):
    login: str
    password: str


class CredentialsUpdate(BaseModel):
    login: str
    password: str


class ProfileUpdate(BaseModel):
    first_name: str
    last_name: str = ""
    birthday: date | None = None
    custom_emoji: str | None = None


class LangUpdate(BaseModel):
    lang: str  # uz | ru | en
