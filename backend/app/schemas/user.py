from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.core.constants import Role, UserStatus


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str | None = None
    role: Role
    dep_id: str | None = None
    status: UserStatus
    lang: str = "uz"
    photo: str | None = None
    birthday: date | None = None
    birthday_in_days: int | None = None
    custom_emoji: str | None = None
    created_at: datetime | None = None


def user_out_with_birthday(user) -> "UserOut":
    """UserOut + birthdayga qancha kun qolganini hisoblaydi."""
    out = UserOut.model_validate(user)
    if user.birthday:
        today = date.today()
        try:
            next_bday = user.birthday.replace(year=today.year)
        except ValueError:  # 29-fevral, kabisa bo'lmagan yil
            next_bday = user.birthday.replace(year=today.year, month=3, day=1)
        if next_bday < today:
            next_bday = next_bday.replace(year=next_bday.year + 1)
        out.birthday_in_days = (next_bday - today).days
    return out


class UserCreate(BaseModel):
    id: int                      # Telegram user id
    name: str
    username: str | None = None
    role: Role = Role.WORKER
    dep_id: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    role: Role | None = None
    dep_id: str | None = None
    status: UserStatus | None = None
    birthday: date | None = None
