import calendar
from datetime import date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

MONTHS_UZ = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
]
DAYS_UZ = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]


def build_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    pm = month - 1 or 12
    py = year - 1 if month == 1 else year
    nm = month % 12 + 1
    ny = year + 1 if month == 12 else year

    rows = []
    rows.append([
        InlineKeyboardButton("◀️", callback_data=f"cal_nav:{py}:{pm}"),
        InlineKeyboardButton(f"📅 {MONTHS_UZ[month - 1]} {year}", callback_data="cal_ignore"),
        InlineKeyboardButton("▶️", callback_data=f"cal_nav:{ny}:{nm}"),
    ])
    rows.append([InlineKeyboardButton(d, callback_data="cal_ignore") for d in DAYS_UZ])

    today = date.today()
    for week in calendar.monthcalendar(year, month):
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="cal_ignore"))
            else:
                label = str(day)
                if year == today.year and month == today.month and day == today.day:
                    label = f"·{day}·"
                row.append(InlineKeyboardButton(label, callback_data=f"cal:{year}:{month:02d}:{day:02d}"))
        rows.append(row)

    rows.append([InlineKeyboardButton("— Muddat yo'q —", callback_data="cal:none")])
    return InlineKeyboardMarkup(rows)


def today_calendar() -> InlineKeyboardMarkup:
    d = date.today()
    return build_calendar(d.year, d.month)


def parse_cal_data(data: str):
    """'cal:YYYY:MM:DD' → 'YYYY-MM-DD' yoki None."""
    if data == "cal:none":
        return None
    parts = data.split(":")
    return f"{parts[1]}-{parts[2]}-{parts[3]}"
