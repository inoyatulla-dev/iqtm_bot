# IQTM Hisobot HTML Shabloni — AI Qo'llanmasi

## 1. Umumiy ma'lumot

**Fayl:** `hisobot.html`  
**Maqsad:** IQTM (Innovatsiyalarni qo'llab-quvvatlash va tijoratlashtirish markazi) uchun oylik jarayon hisobotini chiroyli, A4 chop etishga tayyor HTML sifatida generatsiya qilish.  
**Til:** O'zbek  
**Font:** Plus Jakarta Sans (sarlavhalar) + Inter (asosiy matn) — Google Fonts orqali  
**Rang sxemasi:** IQTM emerald (`#0E7C5A`) asosida, holat ranglari bilan kengaytirilgan  

---

## 2. Kiruvchi ma'lumotlar (Data Schema)

Shablonni to'ldirish uchun quyidagi JSON tuzilmasidagi ma'lumotlar kerak:

```json
{
  "davr": {
    "boshlanish": "2026-06-01",
    "tugash": "2026-06-30",
    "yaratildi": "2026-06-14 09:18"
  },
  "umumiy": {
    "jami_vazifalar": 18,
    "davrda_yaratilgan": 18,
    "davrda_bajarilgan": 10,
    "kechikkan": 1
  },
  "holatlar": [
    { "nomi": "Bajarildi",        "soni": 10 },
    { "nomi": "Jarayonda",        "soni": 5  },
    { "nomi": "Yangi",            "soni": 2  },
    { "nomi": "Qaytarildi",       "soni": 1  },
    { "nomi": "Tekshiruvda",      "soni": 0  },
    { "nomi": "To'xtatib turish", "soni": 0  }
  ],
  "bolimlar": [
    { "nomi": "Dasturlash",  "jami": 3, "bajarilgan": 3 },
    { "nomi": "Konstruktor", "jami": 2, "bajarilgan": 2 },
    { "nomi": "Elektronika", "jami": 2, "bajarilgan": 1 },
    { "nomi": "Ustaxona",    "jami": 1, "bajarilgan": 0 },
    { "nomi": "Vazifalar",   "jami": 2, "bajarilgan": 0 },
    { "nomi": "Bo'yash",     "jami": 0, "bajarilgan": 0 }
  ],
  "loyihalar": [
    {
      "nomi": "Industry 4.0 mini",
      "holat": "Faol",
      "kechikkan": false,
      "muddat": null,
      "jami_vazifa": 5,
      "bajarilgan_vazifa": 1,
      "joriy_jarayon": "Muddat belgilanmagan",
      "vazifalar": [
        {
          "tartib": 1,
          "nomi": "Stentlarni konveyer qismni yig'ish",
          "masul": "Diyorbek Khojayorov",
          "muddat": null,
          "holat": "Jarayonda"
        },
        {
          "tartib": 2,
          "nomi": "Stent karkasni yig'ish",
          "masul": "Orifjon Siddikov",
          "muddat": null,
          "holat": "Jarayonda"
        },
        {
          "tartib": 3,
          "nomi": "Elektron va hardware qismlar ro'yxatini shakllantirish",
          "masul": "Inoyatulla Rajabboyev",
          "muddat": null,
          "holat": "Bajarildi"
        },
        {
          "tartib": 4,
          "nomi": "Yon panel elementlarini joylashish konstruksiyasini chizish",
          "masul": "Sardor Shomirzayev",
          "muddat": null,
          "holat": "Yangi"
        },
        {
          "tartib": 5,
          "nomi": "Stent yon panel elektron komponentlari 3D konstruksiyasini modellashtirish",
          "masul": "Rustam Musurmonov",
          "muddat": null,
          "holat": "Yangi"
        }
      ]
    },
    {
      "nomi": "BYD",
      "holat": "Faol",
      "kechikkan": true,
      "muddat": "30.06.2026",
      "jami_vazifa": 1,
      "bajarilgan_vazifa": 0,
      "joriy_jarayon": "Orqada qolmoqda — 0 kun qoldi (vaqt 100%, bajarildi 0%)",
      "vazifalar": [
        {
          "tartib": 1,
          "nomi": "BYD avtomobilni ko'zdan kechirish",
          "masul": "Inoyatulla Rajabboyev",
          "muddat": "15.06.2026 17:00",
          "muddat_kechikkan": true,
          "holat": "Jarayonda"
        }
      ]
    }
  ]
}
```

---

## 3. HTML Tuzilmasi (Bloklar)

Shablon 6 asosiy blokdan iborat. Har bir blok mustaqil va alohida generatsiya qilinishi mumkin.

```
.sheet
├── .header              ← Sarlavha (brend, davr, sana)
└── .pad
    ├── .kpis            ← 4 ta KPI karta
    ├── .status-wrap     ← Donut diagramma + legend
    ├── .depts           ← Bo'limlar progress-bar
    └── .loyihalar       ← Har bir loyiha kartasi (.project)
        ├── .proj-head   ← Nom + holat + progress
        ├── .proj-sub    ← Muddat + ogohlantirish
        └── table        ← Vazifalar jadvali
```

---

## 4. CSS Rang Tizimi

### Asosiy ranglar
| CSS O'zgaruvchi | Hex       | Ishlatilishi               |
|-----------------|-----------|----------------------------|
| `--brand`       | `#0E7C5A` | Asosiy rang (IQTM yashil)  |
| `--brand-dark`  | `#0A5B42` | Header gradient, sarlavha  |
| `--brand-tint`  | `#E7F4EF` | Yorliq foni                |
| `--ink`         | `#111827` | Asosiy matn                |
| `--muted`       | `#6B7280` | Ikkinchi darajali matn     |
| `--line`        | `#E6E8EB` | Chegaralar, bo'linmalar    |

### Holat ranglari (badge va progress-bar uchun)
| Holat            | Matn rangi | Fon rangi  | CSS class   |
|------------------|------------|------------|-------------|
| Bajarildi        | `#15803D`  | `#DCFCE7`  | `.b-done`   |
| Jarayonda        | `#1D4ED8`  | `#DBEAFE`  | `.b-prog`   |
| Yangi            | `#475569`  | `#F1F5F9`  | `.b-new`    |
| Tekshiruvda      | `#6D28D9`  | `#EDE9FE`  | `.b-review` |
| Qaytarildi       | `#B45309`  | `#FEF3C7`  | `.b-return` |
| To'xtatib turish | `#4B5563`  | `#F3F4F6`  | `.b-pause`  |
| Kechikkan        | `#DC2626`  | `#FEE2E2`  | (qizil rang)|

---

## 5. Muhim Generatsiya Qoidalari

### 5.1 Donut diagramma (CSS conic-gradient)
Donut `background: conic-gradient(...)` bilan chiziladi. Har bir holat uchun burchak hisoblash:

```python
def holat_burchak(soni: int, jami: int) -> float:
    return (soni / jami) * 360

# Misol: 18 vazifadan 10 bajarilgan, 5 jarayonda, 2 yangi, 1 qaytarildi
# done: 0   → 200deg  (10/18 * 360 ≈ 200)
# prog: 200 → 300deg  (5/18 * 360 ≈ 100)
# new:  300 → 340deg  (2/18 * 360 ≈ 40)
# ret:  340 → 360deg  (1/18 * 360 ≈ 20)
```

Conic-gradient formati:
```css
background: conic-gradient(
  <holat1_rang> 0deg <holat1_end>deg,
  <holat2_rang> <holat1_end>deg <holat2_end>deg,
  ...
);
```

### 5.2 Progress-bar kengligi
```python
def progress_pct(bajarilgan: int, jami: int) -> str:
    if jami == 0:
        return "0%"
    return f"{round(bajarilgan / jami * 100)}%"
```

Progress-bar rangi:
- `100%` → `.fill.full` (yashil `#16A34A`)
- `50%–99%` → `.fill.mid` (ko'k `#2563EB`)
- `1%–49%` → `.fill.low` (sariq-to'q `#D97706`)
- `0%` → kichik nuqta sifatida ko'rsatiladi (min `3%` width)

### 5.3 Kechikkan loyiha belgisi
`kechikkan: true` bo'lsa:
- `.project` elementiga `.late` class qo'shiladi → qizg'ish ramka
- Holat yorlig'i `.pill.late` → qizil pill
- `joriy_jarayon` matni sariq `⚠` bilan ko'rsatiladi
- Muddati o'tgan sana `<td class="due over">` → qizil matn

### 5.4 Muddat yo'q bo'lsa
`muddat: null` → jadvalda `—` belgi ko'rsatiladi

### 5.5 Bo'limlar tartibi
Bo'limlar `bajarilgan/jami` foizi bo'yicha **kamayish tartibida** saralanib ko'rsatiladi (100% eng yuqorida).

---

## 6. Jinja2 / Python bilan Generatsiya

### Jinja2 shabloni (asosiy qismlar)

**KPI karta:**
```jinja2
{% for kpi in kpis %}
<div class="kpi {% if kpi.class %}{{ kpi.class }}{% endif %}">
  <div class="label">{{ kpi.label }}</div>
  <div class="value">{{ kpi.value }}</div>
  <div class="sub">{{ kpi.sub }}</div>
</div>
{% endfor %}
```

**Bo'limlar:**
```jinja2
{% for b in bolimlar | sort(attribute='foiz', reverse=True) %}
<div class="dept">
  <div class="nm">{{ b.nomi }}</div>
  <div class="track">
    <div class="fill {{ b.rang_class }}" style="width:{{ b.foiz_str }}"></div>
  </div>
  <div class="pct"><b>{{ b.foiz_label }}</b> · {{ b.bajarilgan }}/{{ b.jami }}</div>
</div>
{% endfor %}
```

**Loyiha:**
```jinja2
{% for loyiha in loyihalar %}
<div class="project {% if loyiha.kechikkan %}late{% endif %}">
  <div class="proj-head">
    <div class="proj-title">
      <span class="pn">{{ loyiha.nomi }}</span>
      <span class="pill {% if loyiha.kechikkan %}late{% endif %}">
        {{ "Orqada qolmoqda" if loyiha.kechikkan else loyiha.holat }}
      </span>
    </div>
    <div class="proj-prog">
      <div class="ptrack">
        <div class="pfill" style="width:{{ loyiha.progress_pct }}%;
          {% if loyiha.kechikkan %}background:var(--late){% endif %}"></div>
      </div>
      <div class="ptxt"><b>{{ loyiha.bajarilgan_vazifa }}/{{ loyiha.jami_vazifa }}</b>
        · {{ loyiha.progress_pct }}%</div>
    </div>
  </div>
  ...
</div>
{% endfor %}
```

**Holat badge:**
```jinja2
{% set badge_map = {
  'Bajarildi': 'b-done',
  'Jarayonda': 'b-prog',
  'Yangi': 'b-new',
  'Tekshiruvda': 'b-review',
  'Qaytarildi': 'b-return',
  "To'xtatib turish": 'b-pause'
} %}
<span class="badge {{ badge_map[vazifa.holat] }}">{{ vazifa.holat }}</span>
```

---

## 7. Python Yordamchi Funksiyalar

```python
def progress_class(bajarilgan: int, jami: int) -> str:
    if jami == 0:
        return ""
    pct = bajarilgan / jami * 100
    if pct == 100:
        return "full"
    elif pct >= 50:
        return "mid"
    else:
        return "low"

def progress_width(bajarilgan: int, jami: int) -> str:
    if jami == 0:
        return "0%"
    pct = round(bajarilgan / jami * 100)
    return f"{max(pct, 3)}%"  # min 3% — ko'rinish uchun

def format_date(date_str: str | None) -> str:
    return date_str if date_str else "—"

def conic_gradient(holatlar: list[dict]) -> str:
    """
    holatlar = [{"rang": "#16A34A", "soni": 10}, ...]
    """
    jami = sum(h["soni"] for h in holatlar)
    if jami == 0:
        return "#E6E8EB"
    parts = []
    current = 0
    for h in holatlar:
        if h["soni"] == 0:
            continue
        end = current + (h["soni"] / jami * 360)
        parts.append(f'{h["rang"]} {current:.1f}deg {end:.1f}deg')
        current = end
    return f"conic-gradient({', '.join(parts)})"
```

---

## 8. Chop Etish / PDF

Shablon `@media print` qoidalari bilan A4 ga tayyor:
- `@page { size: A4; margin: 14mm }`
- `.project`, `.status-wrap`, `.kpi` — `break-inside: avoid`
- `h2.section` — `break-after: avoid`

**Python bilan PDF yasash (WeasyPrint):**
```python
from weasyprint import HTML
HTML(filename="hisobot.html").write_pdf("hisobot.pdf")
```

**Node.js bilan PDF yasash (Puppeteer):**
```js
const browser = await puppeteer.launch();
const page = await browser.newPage();
await page.goto(`file://${path.resolve('hisobot.html')}`);
await page.pdf({ path: 'hisobot.pdf', format: 'A4', printBackground: true });
await browser.close();
```

---

## 9. Fayl Tuzilmasi (tavsiya)

```
hisobot/
├── HISOBOT_TEMPLATE.md   ← shu fayl (AI qo'llanmasi)
├── template.html         ← Jinja2 shabloni (statik versiya: hisobot.html)
├── generate.py           ← Ma'lumotni Telegram bot / DB dan olib HTML yasaydi
├── data_schema.json      ← Bo'sh namuna JSON (§2 dagi tuzilma)
└── output/
    ├── hisobot_2026-06.html
    └── hisobot_2026-06.pdf
```

---

## 10. Tez Eslatma (AI uchun)

| Nima qilish kerak | Qanday |
|---|---|
| Yangi loyiha qo'shish | `loyihalar` arrayiga yangi ob'ekt qo'sh, `.project` blokini takrorla |
| Holat badgeni o'zgartirish | `badge_map` lug'atidan tegishli classni ol |
| Kechikkan loyihani belgilash | `kechikkan: true` → `.project.late` class |
| Donut yangilash | `conic_gradient()` funksiyasi bilan hisabla, inline CSS ga yoz |
| Bo'lim qo'shish | `bolimlar` arrayiga qo'sh, progress qoidalari avtomatik ishlaydi |
| Rang o'zgartirish | CSS `:root` dagi `--brand` va boshqa o'zgaruvchilarni o'zgartirsang yetarli |
