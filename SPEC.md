# ICT Markaz — Telegram Boshqaruv Boti (SPEC)

> Bu hujjat Claude Code uchun to'liq texnik topshiriq. Shu asosda ishlaydigan Telegram bot quriladi.
> **Til:** Bot interfeysi va barcha xabarlar **o'zbek tilida** (lotin alifbosi).

---

## 1. Loyiha maqsadi

"Investisiyalarni qo'llab-quvvatlash va tijoratlashtirish markazi" jamoasini boshqarish uchun Telegram bot. Bot xodimlarni, bo'limlarni, vazifalarni va loyihalarni boshqaradi. Boshqaruv **botning shaxsiy suhbatida** tugmalar (inline keyboard) orqali bo'ladi; natijalar **avtomatik forum-guruhga** e'lon qilinadi.

**Asosiy tamoyil:** boshqaruv shaxsiy, natija guruhda. Guruh — toza "tablo", boshqaruv — qulay tugmalar.

---

## 2. Texnologiyalar

- **Til:** Python 3.11+
- **Kutubxona:** `python-telegram-bot` (v21+, async)
- **Baza:** SQLite (`aiosqlite` yoki sync `sqlite3` bilan), fayl `bot.db`
- **Rejalashtiruvchi:** `APScheduler` (deadline eslatma, haftalik hisobot)
- **Konfiguratsiya:** `.env` fayl (`python-dotenv`) — token va guruh ID
- **Struktura:** modulli (bitta katta fayl emas)

Tavsiya etilgan papka tuzilmasi:
```
ict-bot/
├── .env                  # BOT_TOKEN, GROUP_CHAT_ID
├── requirements.txt
├── bot.py                # asosiy kirish nuqtasi
├── db.py                 # baza bilan ishlash (CRUD funksiyalari)
├── keyboards.py          # inline keyboard generatorlari
├── handlers/
│   ├── common.py         # /start, rol aniqlash, menyu
│   ├── users.py          # xodim CRUD
│   ├── departments.py    # bo'lim CRUD
│   ├── tasks.py          # vazifa CRUD
│   ├── projects.py       # loyiha + bosqich CRUD
│   ├── stats.py          # statistika, hisobot
│   └── superadmin.py     # rol berish, super admin transfer
├── group.py              # guruhga xabar yuborish (mavzularga)
├── scheduler.py          # eslatma va haftalik hisobot
└── decorators.py         # @role_required xavfsizlik
```

---

## 3. Rollar (RBAC — 3 daraja)

| Rol | Tavsif | Qamrov |
|-----|--------|--------|
| **super** (Super Admin) | Yagona to'liq rahbar. Bir nechta bo'lishi mumkin. | Butun tizim |
| **admin** (Bo'lim mas'uli) | Bo'lim uchun mas'ul xodim, **rahbar emas**. O'z bo'limini boshqaradi VA o'zi ham vazifa bajaradi. | Faqat o'z bo'limi |
| **worker** (Xodim) | Oddiy xodim. | Faqat o'ziga tegishli |

**Muhim:** Admin = bo'lim mas'uli, rahbar emas. Umumiy rahbarlik faqat Super Admin'da.

### Huquqlar matritsasi

| Imkoniyat | super | admin | worker |
|-----------|:---:|:---:|:---:|
| Super Admin qo'shish/rol berish | ✅ | ❌ | ❌ |
| Xodim CRUD (qo'shish/tahrir/o'chir) | ✅ | ❌ | ❌ |
| Bo'lim CRUD | ✅ | ❌ | ❌ |
| Bo'limga biriktirish | ✅ | ❌ | ❌ |
| Vazifa qo'yish | ✅ (har bo'lim) | ✅ (o'z bo'limi) | ❌ |
| Vazifa tahrirlash/o'chirish | ✅ | ✅ (o'z bo'limi) | ❌ |
| Vazifa "bajarildi" belgilash | ✅ | ✅ | ✅ (o'ziniki) |
| Loyiha CRUD | ✅ | ❌ | ❌ |
| Statistika | ✅ butun | ✅ bo'lim | ✅ shaxsiy |
| Xodimlar reytingi | ✅ butun | ✅ bo'lim | ❌ |
| Bot sozlamalari / backup | ✅ | ❌ | ❌ |

### Xavfsizlik
- Har bir tugma/komanda ishlashidan oldin `@role_required` dekorator foydalanuvchi rolini DB dan tekshiradi.
- Xodim admin funksiyasiga "qo'lda" kirsa — bot rad etadi ("🚫 Ruxsat yo'q").
- Har muhim amal `logs` jadvaliga yoziladi (kim, nima, qachon).

---

## 4. Ma'lumotlar bazasi (SQLite)

### users
| Ustun | Tur | Izoh |
|-------|-----|------|
| id | INTEGER PK | Telegram user id |
| name | TEXT | To'liq ism |
| username | TEXT | @username |
| role | TEXT | 'super' / 'admin' / 'worker' |
| dep_id | TEXT | FK → departments.id (super uchun NULL) |
| status | TEXT | 'faol' / 'bloklangan' |
| created_at | TEXT | sana |

### departments
| Ustun | Tur | Izoh |
|-------|-----|------|
| id | TEXT PK | qisqa kod (el, ds, kn, us, bo) |
| name | TEXT | nomi |
| emoji | TEXT | 🔌 va h.k. |
| admin_id | INTEGER | FK → users.id (bo'lim mas'uli, NULL bo'lishi mumkin) |
| topic_id | INTEGER | guruhdagi forum mavzu ID (message_thread_id) |

### tasks
| Ustun | Tur | Izoh |
|-------|-----|------|
| id | INTEGER PK AUTOINCREMENT | |
| name | TEXT | vazifa nomi |
| description | TEXT | tavsif |
| dep_id | TEXT | FK → departments.id |
| masul_id | INTEGER | FK → users.id (mas'ul) |
| created_by | INTEGER | FK → users.id (kim qo'ydi) |
| deadline | TEXT | muddat (ISO sana) |
| status | TEXT | 'faol' / 'bajarildi' / 'kechikdi' |
| project_id | INTEGER | FK → projects.id (NULL bo'lishi mumkin) |
| created_at | TEXT | |

### projects
| Ustun | Tur | Izoh |
|-------|-----|------|
| id | INTEGER PK AUTOINCREMENT | |
| name | TEXT | loyiha nomi |
| status | TEXT | 'faol' / 'tugadi' |
| created_by | INTEGER | FK → users.id |
| created_at | TEXT | |

### project_stages (loyiha bosqichlari)
| Ustun | Tur | Izoh |
|-------|-----|------|
| id | INTEGER PK AUTOINCREMENT | |
| project_id | INTEGER | FK → projects.id |
| seq | INTEGER | navbat raqami (bir xil raqam = parallel) |
| dep_id | TEXT | qaysi bo'lim bajaradi |
| description | TEXT | bosqich tavsifi |
| masul_id | INTEGER | mas'ul xodim (NULL bo'lishi mumkin) |
| deadline | TEXT | muddat |
| status | TEXT | 'wait' / 'active' / 'done' |

### reminders
| Ustun | Tur | Izoh |
|-------|-----|------|
| id | INTEGER PK | |
| task_id | INTEGER | FK → tasks.id |
| remind_at | TEXT | eslatma vaqti (datetime) |
| sent | INTEGER | 0/1 |

### logs (audit)
| Ustun | Tur | Izoh |
|-------|-----|------|
| id | INTEGER PK | |
| user_id | INTEGER | kim |
| action | TEXT | nima qildi |
| created_at | TEXT | qachon |

---

## 5. Bo'limlar (boshlang'ich)

| id | nomi | emoji |
|----|------|-------|
| el | Elektronika | 🔌 |
| ds | Dasturlash | 💻 |
| kn | Konstruktor | 📐 |
| us | Ustaxona | 🔧 |
| bo | Bo'yash | 🎨 |

Bo'limlar CRUD orqali qo'shilishi/o'chirilishi/tahrirlanishi mumkin.

---

## 6. /start oqimi va menyular

`/start` bosilganda bot foydalanuvchi `id` sini DB dan qidiradi, rolini aniqlaydi va **rolga mos menyu** chiqaradi. Agar foydalanuvchi DB da yo'q bo'lsa — "Sizga ruxsat berilmagan, administratorga murojaat qiling" deydi (faqat ro'yxatga olingan foydalanuvchilar ishlatadi).

### Super Admin menyusi (inline buttons)
- 📋 Vazifa qo'yish
- 📁 Loyiha yaratish
- 🗂 Loyihalar
- 👥 Xodimlar (CRUD)
- 👑 Bo'lim mas'ullari / rollar
- 🏢 Bo'limlar (CRUD)
- 📊 To'liq statistika
- 👥 Xodimlar reytingi
- 📈 Haftalik hisobot
- ⚙️ Sozlamalar

### Bo'lim mas'uli (admin) menyusi
- 📋 Vazifa qo'yish (faqat o'z bo'limi)
- 👁️ Bo'lim vazifalari (CRUD: tahrir/o'chir/tugatish)
- 📁 Mening vazifalarim (admin ham vazifa bajaradi)
- 👷 Mening xodimlarim
- 📊 Bo'lim statistikasi
- 👥 Xodimlar reytingi (o'z bo'limi)
- 📈 Hisobot

### Xodim (worker) menyusi
- 📁 Mening vazifalarim (✅ bajarildi belgilash)
- 📊 Shaxsiy statistika
- 🔔 Eslatma o'rnatish
- ❓ Yordam

---

## 7. Funksional talablar (CRUD — hammasi)

Har bir ob'ekt uchun to'liq CRUD: **Create, Read, Update, Delete**.

### 7.1 Xodimlar (faqat super)
- **Create:** yangi xodim qo'shish (ism, username, rol, bo'lim). Taklif havolasi/ko'rsatma.
- **Read:** barcha foydalanuvchilar ro'yxati, har biri kartochka.
- **Update:** bo'lim o'zgartirish, holat (faol/bloklangan), rol o'zgartirish.
- **Delete:** xodimni o'chirish (tasdiqlash so'raladi). O'chirilganda uning vazifalari ham olib tashlanadi. **O'zini o'chira olmaydi.**

### 7.2 Rol o'zgartirish + Super Admin transfer (faqat super)
- Xodim rolini: worker / admin / super qilish.
- **Super Admin qilishda XAVFSIZLIK KODI so'raladi:**
  - Bot tasodifiy 4-6 xonali kod generatsiya qiladi.
  - Kod **amalni boshlagan super admin**ga shaxsiy yuboriladi (yoki sozlamadagi parol bilan tekshiriladi).
  - To'g'ri kiritilsa — yangi super admin tayinlanadi (mavjudlari saqlanadi; **ko'p super admin bo'lishi mumkin**).
  - Noto'g'ri kod — amal bekor.
- **Oxirgi super admin o'chirilmaydi/pasaytirilmaydi** (kamida bitta super qolishi shart).

### 7.3 Bo'limlar (faqat super)
- Create: yangi bo'lim (id, nomi, emoji).
- Read: bo'limlar ro'yxati (xodim soni, vazifa soni, mas'ul).
- Update: nomi/emoji o'zgartirish, mas'ul (admin) biriktirish.
- Delete: bo'lim o'chirish. Ichida xodim bo'lsa — avval ko'chirishni talab qilish.

### 7.4 Vazifalar
- **Create (super/admin):** bo'lim → mas'ul → muddat → tavsif. Admin faqat o'z bo'limiga, super har bo'limga. **Admin tayinlanmagan bo'limga super to'g'ridan-to'g'ri xodimga vazifa beradi.**
- **Read:** bo'lim vazifalari / shaxsiy vazifalar.
- **Update (super/admin):** muddat, mas'ul, tavsif, holat.
- **Delete (super/admin):** tasdiqlash bilan.
- **Mark done:** mas'ul xodim ✅ bosadi → status 'bajarildi' → guruhga e'lon, qo'ygan kishi teglanadi.

### 7.5 Loyihalar + bosqichlar (faqat super)
- **Create:** loyiha nomi → bosqichlarni **birma-bir qo'lda** qo'shish.
  - Har bosqich: **bo'lim + tavsif + mas'ul xodim + muddat + navbat raqami (seq)**.
  - **Parallel oqim:** bir xil `seq` raqamli bosqichlar bir vaqtda (parallel) ishlaydi. Keyingi raqam = ketma-ket.
  - Saqlashda: 1-navbat bosqichlari 'active', qolganlari 'wait'.
- **Read:** loyihalar ro'yxati (progress %), loyihani ochish — bosqichlar navbat bo'yicha guruhlangan, parallel belgisi bilan, har bosqich holati (⏳ wait / 🔄 active / ✅ done).
- **Update:** bosqich tahrirlash, mas'ul/muddat o'zgartirish.
- **Delete:** loyiha o'chirish (barcha bosqichlari bilan, tasdiqlash).
- **Bosqichni tugatish:** active bosqich 'done' bo'lganda — **keyingi navbat avtomatik 'active' bo'ladi**, lekin faqat oldingi barcha navbatlar to'liq tugagan bo'lsa. Guruhga "keyingi navbat boshlandi" e'loni + yangi mas'ullar teglanadi. Hamma bosqich tugasa — loyiha 'tugadi'.

### 7.6 Statistika
- **Super:** butun tizim — jami/bajarildi/jarayonda/kechikkan + har bo'lim progress %.
- **Admin:** faqat o'z bo'limi.
- **Worker:** shaxsiy.

### 7.7 Xodimlar reytingi (super/admin)
- Har xodim: ✅ bajarildi · 🔄 jarayonda · ⚠️ kechikkan · progress %.
- Bajarilgan vazifa bo'yicha saralangan (🥇🥈🥉).
- Vazifasiz xodimlar alohida ko'rsatiladi.
- Super — butun tizim, admin — o'z bo'limi.

---

## 8. Guruh bilan bog'lanish

Bot forum-guruhga e'lonlarni avtomatik yuboradi.

### Sozlash
1. Bot `@BotFather` orqali yaratiladi, token `.env` da `BOT_TOKEN`.
2. Bot guruhga qo'shiladi va **admin** qilinadi (xabar yuborish, mavzu boshqarish, pin huquqi).
3. Guruh `chat_id` (manfiy, `-100...` bilan boshlanadi) `.env` da `GROUP_CHAT_ID`.
4. Har bo'limning forum mavzu ID si (`message_thread_id`) aniqlanadi va `departments.topic_id` ga saqlanadi.

### Topic ID aniqlash mexanizmi
Admin komandasi `/topic_aniqla` (faqat super): guruhdagi har mavzuda bir marta yuboriladi, bot `update.message.message_thread_id` ni o'qib, mavzu nomi bo'yicha tegishli bo'limga bog'laydi va DB ga yozadi. Yoki sozlash bosqichida qo'lda kiritiladi.

### Guruhga avtomatik boradigan xabarlar
| Hodisa | Qayerga |
|--------|---------|
| Yangi vazifa | tegishli bo'lim mavzusi + mas'ul teglanadi |
| Vazifa bajarildi ✅ | bo'lim mavzusi, qo'ygan kishi teglanadi |
| Deadline eslatma | mas'ulga shaxsiy + bo'lim mavzusiga ogohlantirish |
| Haftalik hisobot | "E'lonlar" mavzusi, juma 18:00 |
| Loyiha bosqichi o'zgardi | bo'lim mavzusi(lari) + yangi mas'ullar teglanadi |

### Yuborish namunasi
```python
await context.bot.send_message(
    chat_id=GROUP_CHAT_ID,                  # -100xxxxxxxxxx
    message_thread_id=dep.topic_id,         # masalan 5 = Elektronika
    text=f"📌 Yangi vazifa #{task_id}\n"
         f"📝 {name}\n👤 {masul_username}\n⏰ {deadline}",
)
```

---

## 9. Scheduler (APScheduler)

- **Deadline eslatma:** har bir 'faol' vazifa uchun deadline−1 kun → mas'ulga shaxsiy + bo'lim mavzusiga. `reminders.sent=1` qilib belgilanadi.
- **Kechikkan vazifa:** deadline o'tib status hali 'faol' bo'lsa → 'kechikdi' ga o'tkazish, guruhga ogohlantirish.
- **Haftalik hisobot:** har juma 18:00 → "E'lonlar" mavzusiga statistika.

---

## 10. Bot komandalari (tekst, ixtiyoriy — asosiysi tugmalar)

| Komanda | Kim | Vazifa |
|---------|-----|--------|
| /start | hamma | rolga mos menyu |
| /menu | hamma | menyuga qaytish |
| /topic_aniqla | super | guruh mavzu ID larini bog'lash |
| /yordam | hamma | yordam |

Asosiy interaksiya **inline keyboard tugmalari** orqali (callback_data bilan). Komandalar minimal.

---

## 11. UX talablari

- Barcha matn **o'zbek tilida** (lotin), sodda til.
- Har menyu inline tugmalar bilan; har amaldan keyin "🏠 Menyu" tugmasi.
- O'chirish/muhim amallarda doim tasdiqlash so'raladi.
- Holatlar emoji bilan: 🔄 faol, ✅ bajarildi, ⚠️ kechikkan, ⏳ kutmoqda.
- callback_data prefikslari aniq bo'lsin (masalan `task_done:47`, `user_del:4`, `proj_stage_add`), parse oson bo'lsin.

---

## 12. Boshlang'ich ma'lumot (seed)

Birinchi ishga tushganda:
- Bot egasining Telegram ID si `.env` da `OWNER_ID` → DB ga 'super' rol bilan yoziladi.
- 5 ta bo'lim (yuqoridagi jadval) yaratiladi.
- Super Admin uchun sozlama paroli `.env` da `SUPER_TRANSFER_PASSWORD` (yangi super tayinlashda tekshiriladi).

---

## 13. Qabul mezonlari (Definition of Done)

1. `/start` 3 rolda turlicha menyu chiqaradi, ruxsatlar to'g'ri tekshiriladi.
2. Xodim/bo'lim/vazifa/loyiha uchun to'liq CRUD ishlaydi.
3. Super Admin transfer kod bilan himoyalangan, ko'p super bo'la oladi, oxirgi super himoyalangan.
4. Loyiha bosqichlari parallel (seq) ishlaydi; bosqich tugaganda keyingi navbat avtomatik faollashadi.
5. Vazifa/bajarildi/eslatma/hisobot guruhdagi to'g'ri mavzuga boradi.
6. Statistika va reyting rol qamroviga mos.
7. Barcha muhim amallar `logs` ga yoziladi.
8. Kod modulli, `.env` bilan sozlanadi, `requirements.txt` bor, README'da o'rnatish yo'riqnomasi.

---

## 14. Birinchi ishga tushirish (README ga kiritilsin)

```bash
# 1. virtual muhit
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# 2. kutubxonalar
pip install -r requirements.txt

# 3. .env to'ldirish
# BOT_TOKEN=...
# GROUP_CHAT_ID=-100...
# OWNER_ID=...
# SUPER_TRANSFER_PASSWORD=...

# 4. ishga tushirish
python bot.py
```

---

**Eslatma Claude Code uchun:** Avval `db.py` (sxema + CRUD), keyin `keyboards.py`, `decorators.py`, so'ng handler'larni modulma-modul yoz. Har modulni alohida test qilish mumkin bo'lsin. Hozircha SQLite yetarli; keyinchalik PostgreSQL ga ko'chirish oson bo'ladigan qilib yoz (DB qatlamini ajratib).
