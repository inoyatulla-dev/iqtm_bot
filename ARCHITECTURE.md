# IQTM Mini App — Arxitektura

> ICT Markaz jamoasini boshqarish uchun **Telegram Mini App**.
> Til: interfeys o'zbek (lotin). Ichki qiymatlar ingliz (toza kod uchun).

---

## 1. Asosiy tamoyil

**100% boshqaruv Mini App ichida.** Barcha CRUD (xodim, bo'lim, vazifa, loyiha, sozlamalar) web-ilovada.

Bot faqat:
- `/start` → 🚀 "Ilovani ochish" tugmasi
- Guruhga avtomatik e'lon yuborish
- Scheduler (eslatma, kechikkan vazifa, haftalik hisobot)

---

## 2. Komponentlar

```
Telegram
  ├── Mini App (WebView)  → Frontend (React)
  └── Bot (/start)        → Bot (python-telegram-bot)
                │                    │
                ▼                    ▼
        Frontend ──REST(JSON)──► Backend (FastAPI)
                                     │
                            ┌────────┼────────┐
                         services  notifications
                            │          │ (guruh + shaxsiy)
                       repositories     │
                            │           └──► Bot API
                          models
                            │
                          DB (SQLite → PostgreSQL)
```

Bot va Backend **bitta Python kodbazasi** — umumiy DB va notification kodi.

---

## 3. Texnologiyalar

| Qatlam | Texnologiya |
|--------|-------------|
| Frontend | React + TypeScript + Vite |
| TMA SDK | `@telegram-apps/sdk-react` |
| UI | `@telegram-apps/telegram-ui` |
| Kanban | `@dnd-kit` |
| Backend | FastAPI (async) |
| ORM | SQLAlchemy 2.0 async + Alembic |
| DB | SQLite (dev) → PostgreSQL (prod) |
| Bot | python-telegram-bot |
| Scheduler | APScheduler |
| Auth | Telegram initData (HMAC) → JWT |

---

## 4. Rollar

| Rol | Ichki kod | Qamrov |
|-----|-----------|--------|
| Boshliq | `boss` | Hammasini ko'radi, vazifa beradi, barcha sozlama |
| Xodim | `worker` | Faqat o'z vazifalari |

Bo'limlar — rangli yorliq (label), rol emas.

---

## 5. Vazifa holatlari (Kanban ustunlari)

| Ichki | UI | Ustun |
|-------|-----|-------|
| `new` | 🆕 Yangi | 1 |
| `in_progress` | 🔄 Jarayonda | 2 |
| `review` | 🔍 Tekshiruvda | 3 |
| `done` | ✅ Bajarildi | 4 |

**Kechikkan** — alohida holat emas, hisoblanadi: `deadline < bugun AND status != done`.

---

## 6. Papka tuzilmasi

```
iqtm_bot/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI + bot (webhook) birga
│   │   ├── config.py          # markaziy sozlama
│   │   ├── core/
│   │   │   ├── constants.py    # Enum: Role, TaskStatus, ...
│   │   │   ├── security.py     # initData + JWT
│   │   │   └── permissions.py  # markaziy ruxsat
│   │   ├── db/                # engine, session, seed
│   │   ├── models/            # SQLAlchemy modellar
│   │   ├── schemas/           # Pydantic (request/response)
│   │   ├── repositories/      # DB so'rovlar
│   │   ├── services/          # biznes-logika
│   │   ├── api/               # REST routerlar
│   │   ├── notifications.py   # guruh + shaxsiy xabar
│   │   └── bot/               # /start, scheduler
│   ├── alembic/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/        # TaskCard, Column, ...
│   │   ├── pages/             # Board, Users, Stats, Settings
│   │   ├── hooks/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
└── ARCHITECTURE.md
```

---

## 7. Xavfsizlik oqimi

```
Mini App → initData (har so'rovda)
   → Backend: bot_token bilan HMAC-SHA256 tekshiradi
   → JWT beradi
   → har endpoint: permissions.py orqali rol tekshiriladi
```

---

## 8. Migratsiya fazalari

| Faza | Ish |
|------|-----|
| 0 | Tuzilma, config, requirements |
| 1 | Backend yadro: modellar, DB, repo |
| 2 | Auth + permissions |
| 3 | API endpointlar |
| 4 | Frontend: Kanban + CRUD |
| 5 | Bot: /start tugma, guruh, scheduler |
| 6 | Loyihalar, reyting, grafiklar |
