# V3 — Rol bo'yicha cheklovlar, profil tahriri, loyiha detali, monitoring eksport

## Qarorlar
- Xodimlar tab: faqat boss + worker (observer ko'rmaydi)
- Hisobot eksport (Telegram'ga): boss + observer (DashboardUser)
- Mavzular (Topics): Settings'da qo'lda qo'shish UI

## A. Backend — permissions / observer read-only
- `permissions.py`: `can_create_task`/`can_edit_task`/`can_change_status`/`can_delete_task` —
  observer uchun har doim `False` (aniq tekshiruv qo'shiladi)
- `task_service.get_board_tasks`: observer ham boss kabi barcha tasklarni ko'radi
  (`user.role not in (BOSS, OBSERVER)` bo'lsa filtr)

## B. Backend — Arizalar (observer uchun bo'lim shart emas)
- Hech narsa o'zgarmaydi (frontend-only) — `approve(role, dep_id)` `dep_id=None` bilan
  chaqiriladi observer tanlanganda

## C. Backend — Xodimlar ko'rinishi va profil tahriri
- `GET /users` → `CurrentUser` (BossUser emas), lekin `status_filter=pending` faqat boss
  ko'rsin (yoki worker uchun status_filter ignore qilinadi — soddalik uchun: worker
  faqat status_filter berilmagan so'rovda `active` userlarni oladi)
- `UserUpdate` schema: `birthday: date | None = None` qo'shiladi (admin profil
  tahririda tug'ilgan kunni o'zgartirish uchun)

## D. Backend — Loyihalar: worker filtri
- `GET /projects` — worker uchun faqat o'zi ishtirok etgan (masul_id == user.id
  task'i bor) loyihalar
- `GET /projects/{id}` — worker uchun `tasks` faqat o'ziniki bilan filtrlanadi;
  agar loyihada umuman ishi yo'q bo'lsa 403

## E. Backend — Monitoring: davr (period) + eksport
- `GET /stats/dashboard?period=week|month|year` — `new_in_period`/`closed_in_period`
  (nomlari period'ga qarab frontendda label o'zgaradi)
- `DashboardOut`: `new_this_month`/`closed_this_month` → `new_in_period`/`closed_in_period`
  ga nomlanadi (yoki ikkalasi ham saqlanadi — period bo'yicha hisoblanadi)
- Yangi: `POST /reports/send/{period}.{fmt}` (`DashboardUser`) — hisobotni generatsiya
  qilib so'rovchi foydalanuvchining shaxsiy Telegram chatiga `send_document` orqali yuboradi
- `notifications.py`: `send_document_bytes(chat_id, filename, data, caption)` qo'shiladi
- `reports.py`: xlsx olib tashlanadi (`_FORMATS`dan, `build_xlsx` funksiyasi va
  `report_export.py`dan ham o'chiriladi)

## F. Backend — Statistika: davr
- `StatusCounts`/`/stats/me`, `/stats/global`, `/stats/rating` — `period` query param
  qo'shiladi, `done_in_period` qo'shiladi (xodim samaradorlik grafigi uchun)

## G. Backend — PDF qayta yozish (rasmiy hisobot)
- `report_service.collect_report_data`: loyihalar ro'yxati (status, percent, tasklar
  done/in_progress/planned guruhlangan) qo'shiladi
- `report_export.build_pdf`: loyihalar bo'limi (progress + status bo'yicha tasklar)
  qo'shiladi, tartibli formatlash
- `build_docx`: xuddi shunday loyihalar bo'limi qo'shiladi

## H. Frontend — Doska
- `TaskCard.tsx`: `masul_emoji` badge olib tashlanadi
- `BoardPage.tsx`: observer uchun FAB (`+`) yashiriladi, `moveTask` no-op
- `TaskForm.tsx`: observer uchun attachments-upload va comment-input yashiriladi

## I. Frontend — Arizalar
- `ArizalarPage.tsx`: rol="observer" tanlanganda dept-sheet o'tkazib yuborilib,
  to'g'ridan-to'g'ri `approve("observer", null)`

## J. Frontend — Xodimlar
- `Layout.tsx`: `users` tab — boss + worker (observer'da yo'q)
- `UsersPage.tsx`:
  - worker uchun: invite tugmasi yo'q, karta bosilsa faqat profil ko'rinishi (read-only sheet)
  - boss uchun: karta bosilsa profil + "✏️ Tahrirlash" (forma: ism, familiya, rol,
    bo'lim, tug'ilgan kun) + block/delete mavjud actionlar

## K. Frontend — Loyihalar
- `ProjectsPage.tsx`: karta bosilsa detail Sheet (info + progress + tasks)
  - boss: tahrirlash + ish qo'shish (mavjud create formani detailga ko'chirish/qo'shish)
  - observer: faqat ko'rish
  - worker: faqat o'zi qatnashgan loyihalar, faqat o'z tasklari

## L. Frontend — Monitoring
- Davr tugmalari (Hafta/Oy/Yil) — `statsApi.dashboard(period)`
- Eksport bloki: davr + PDF/DOCX tugmalari, generatsiya paytida loading,
  natija "✅ Hisobot tayyor — Telegram chatingizga yuborildi"
- `reportsApi.send(period, fmt)` qo'shiladi

## M. Frontend — Statistika
- Davr tugmalari qo'shiladi
- Xodimlar samaradorlik grafigi (CSS bar chart, `done_in_period`)
- Observer'da `stats` tab yashiriladi (Layout.tsx)
- Eksport bloki StatsPage'dan olib tashlanadi (Monitoring'ga ko'chgan)
- Excel tugmasi/format olib tashlanadi

## N. Frontend — Settings: Mavzular UI
- Yangi komponent `TopicsSection.tsx`: ro'yxat + qo'shish/tahrirlash/o'chirish
  (`topicsApi`, i18n tayyor `settings.topics.*`)
- `SettingsPage.tsx` menyusiga "🧵 Mavzular" qo'shiladi (faqat boss)

## Tartib
1. Backend: A → B(yo'q) → C → D → E → F → G
2. Frontend: H → I → J → K → L → M → N
3. `npm run build`, backend import tekshiruvi
4. Deploy — foydalanuvchi o'zi qiladi
