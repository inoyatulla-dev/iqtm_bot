# IQTM Workspace — Telegram Mini App

ICT Markaz jamoasini boshqarish uchun **Telegram Mini App**.
Topshiriqlar doskasi (Kanban), xodimlar, bo'limlar va statistika — hammasi ilovada.

> Arxitektura: [ARCHITECTURE.md](ARCHITECTURE.md) · Eski bot kodi: [legacy/](legacy/)

---

## Tuzilma

```
iqtm_bot/
├── backend/     FastAPI API + bot + scheduler (Python)
├── frontend/    React + TypeScript Mini App
├── docs/        qo'llanmalar
└── legacy/      eski bot kodi (faqat ma'lumot uchun)
```

---

## 1. Backend (FastAPI)

```bash
cd backend
py -3.11 -m venv .venv
.venv\Scripts\activate           # Windows
pip install -r requirements.txt

copy .env.example .env           # va to'ldiring (BOT_TOKEN, OWNER_ID, ...)

# API serverni ishga tushirish
uvicorn app.main:app --reload --port 8000
```

API hujjati: http://localhost:8000/docs

### Botni ishga tushirish (alohida terminal)

```bash
cd backend
.venv\Scripts\activate
python -m app.bot.run
```

Bot faqat `/start` (ilova tugmasi), guruh xabarlari va eslatma uchun.

---

## 2. Frontend (Mini App)

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

Dev rejimda `/api` so'rovlari avtomatik `localhost:8000` ga yo'naltiriladi.

> Telegram tashqarisida (oddiy brauzer) sinash uchun `.env` ga
> `VITE_DEV_INIT_DATA=<haqiqiy initData>` qo'ying.

### Build (deploy uchun)

```bash
npm run build                    # dist/ hosil bo'ladi
```

---

## 3. Sozlash (.env — backend)

| Kalit | Izoh |
|-------|------|
| `BOT_TOKEN` | @BotFather tokeni |
| `GROUP_CHAT_ID` | forum-guruh ID (manfiy) |
| `OWNER_ID` | birinchi boshliq Telegram ID |
| `WEBAPP_URL` | Mini App HTTPS manzili (@BotFather'da ham sozlanadi) |
| `JWT_SECRET` | tasodifiy uzun satr |
| `DATABASE_URL` | SQLite (dev) yoki PostgreSQL (prod) |

---

## 4. Deploy (qisqacha)

1. Frontend `npm run build` → statik fayllar HTTPS bilan beriladi.
2. Backend `uvicorn` (yoki gunicorn+uvicorn) HTTPS orqasida.
3. @BotFather → bot uchun **Web App URL** = `WEBAPP_URL`.
4. Bot alohida jarayon: `python -m app.bot.run`.

---

## Rollar

| Rol | Imkoniyat |
|-----|-----------|
| **Boshliq** | Hamma narsa: vazifa berish, xodim/bo'lim CRUD, statistika |
| **Xodim** | O'z doskasi, shaxsiy vazifa, shaxsiy statistika |
