# IQTM Workspace — Telegram Bot

ICT Markaz jamoasini boshqarish uchun Telegram bot.

## O'rnatish

```bash
# 1. Virtual muhit
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 2. Kutubxonalar
pip install -r requirements.txt

# 3. .env faylini yaratish
copy .env.example .env
```

## .env sozlash

```
BOT_TOKEN=7xxxxxxxxxx:AAF...          # @BotFather dan olingan token
GROUP_CHAT_ID=-100xxxxxxxxxx          # Forum-guruh chat ID (manfiy)
OWNER_ID=123456789                    # Sizning Telegram ID ingiz
SUPER_TRANSFER_PASSWORD=secretpass    # Super Admin tayinlashda parol
```

## Ishga tushirish

```bash
python bot.py
```

## Guruh sozlash

1. Botni forum-guruhga qo'shing va **Admin** qiling (xabar yuborish, mavzu boshqarish).
2. Guruh `chat_id` ni aniqlang va `.env` ga yozing.
3. Har bo'lim uchun forum mavzusi yarating.
4. Har mavzuda `/topic_aniqla` komandasini yuboring — bot `topic_id` ni ko'rsatadi.
5. Sozlamalar → Bo'limlar → Bo'lim → Topic ID sozlash orqali kiritib qo'ying.

## Papka tuzilmasi

```
├── bot.py            — asosiy kirish nuqtasi
├── db.py             — SQLite CRUD
├── keyboards.py      — inline keyboard generatorlari
├── decorators.py     — @role_required xavfsizlik
├── group.py          — guruhga xabar yuborish
├── scheduler.py      — eslatma va haftalik hisobot
├── handlers/
│   ├── common.py     — /start, /menu
│   ├── users.py      — xodim CRUD
│   ├── departments.py — bo'lim CRUD
│   ├── tasks.py      — vazifa CRUD
│   ├── projects.py   — loyiha + bosqich CRUD
│   ├── stats.py      — statistika, reyting, hisobot
│   └── superadmin.py — rol boshqaruv, sozlamalar
├── .env.example
└── requirements.txt
```

## Rollar

| Rol | Huquqlar |
|-----|----------|
| **super** | Barcha imkoniyatlar |
| **admin** | O'z bo'limi: vazifa, statistika, reyting |
| **worker** | Faqat o'z vazifalari |
# iqtm_bot
