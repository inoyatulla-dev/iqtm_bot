from pydantic import BaseModel

from app.schemas.user import UserOut


class AuthRequest(BaseModel):
    init_data: str  # Telegram WebApp.initData (raw query string)


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class ProfileUpdate(BaseModel):
    first_name: str
    last_name: str = ""


class LangUpdate(BaseModel):
    lang: str  # uz | ru | en
