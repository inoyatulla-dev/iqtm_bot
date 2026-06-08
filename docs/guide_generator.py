# -*- coding: utf-8 -*-
"""
IQTM Workspace Bot — Yo'riqnoma generatori.
3 ta rol uchun zamonaviy HTML yo'riqnoma yaratadi (Super Admin / Admin / Worker).
Keyin Edge headless orqali PDF ga aylantiriladi.
"""
import os
import html as _html

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ──────────────────────────── ROL TEMALARI ────────────────────────────
THEMES = {
    "super": {
        "name": "Super Admin",
        "icon": "👑",
        "subtitle": "Tizim boshqaruvchisi — to'liq nazorat",
        "c1": "#7c3aed",   # asosiy
        "c2": "#a855f7",
        "c3": "#fbbf24",   # urg'u (oltin)
        "soft": "#f5f3ff",
        "softline": "#ede9fe",
    },
    "admin": {
        "name": "Bo'lim mas'uli (Admin)",
        "icon": "🔑",
        "subtitle": "Bo'lim rahbari — jamoa va vazifalar",
        "c1": "#2563eb",
        "c2": "#3b82f6",
        "c3": "#06b6d4",
        "soft": "#eff6ff",
        "softline": "#dbeafe",
    },
    "worker": {
        "name": "Xodim",
        "icon": "👤",
        "subtitle": "Jamoa a'zosi — vazifalarni bajarish",
        "c1": "#059669",
        "c2": "#10b981",
        "c3": "#84cc16",
        "soft": "#ecfdf5",
        "softline": "#d1fae5",
    },
}


# ──────────────────────────── KOMPONENTLAR ────────────────────────────
def esc(t):
    return _html.escape(str(t))


def phone(messages):
    """Telegram telefon mockup. messages = list of dict."""
    blocks = []
    for m in messages:
        if m.get("type") == "user":
            blocks.append(
                f'<div class="tg-row tg-right"><div class="tg-bubble tg-out">{m["text"]}'
                f'<span class="tg-time">{m.get("time","")}</span></div></div>'
            )
        elif m.get("type") == "note":
            blocks.append(f'<div class="tg-note">{m["text"]}</div>')
        else:  # bot
            kb = ""
            if m.get("buttons"):
                rows = []
                for row in m["buttons"]:
                    cells = "".join(
                        f'<div class="tg-btn{" tg-btn-accent" if b.get("accent") else ""}">{b["t"]}</div>'
                        for b in row
                    )
                    rows.append(f'<div class="tg-btnrow">{cells}</div>')
                kb = f'<div class="tg-kb">{"".join(rows)}</div>'
            blocks.append(
                f'<div class="tg-row tg-left">'
                f'<div class="tg-ava">🤖</div>'
                f'<div class="tg-bubble tg-in">{m["text"]}{kb}'
                f'<span class="tg-time">{m.get("time","")}</span></div></div>'
            )
    inner = "".join(blocks)
    return f'''
    <div class="phone">
      <div class="phone-notch"></div>
      <div class="phone-top">
        <div class="phone-bava">🤖</div>
        <div class="phone-binfo"><b>IQTM Workspace</b><span>bot</span></div>
      </div>
      <div class="phone-chat">{inner}</div>
      <div class="phone-input"><span>Xabar yozing…</span><div class="phone-send">➤</div></div>
    </div>'''


def feature_card(icon, title, desc, items=None):
    li = ""
    if items:
        li = "<ul class='fc-list'>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
    return f'''
    <div class="fcard">
      <div class="fcard-ic">{icon}</div>
      <div class="fcard-body">
        <div class="fcard-title">{title}</div>
        <div class="fcard-desc">{desc}</div>
        {li}
      </div>
    </div>'''


def steps(items):
    rows = []
    for i, (t, d) in enumerate(items, 1):
        rows.append(f'''
        <div class="step">
          <div class="step-num">{i}</div>
          <div class="step-body"><div class="step-t">{t}</div><div class="step-d">{d}</div></div>
        </div>''')
    return f'<div class="steps">{"".join(rows)}</div>'


def section(num, title, sub=""):
    s = f'<div class="sec-sub">{sub}</div>' if sub else ""
    return f'''
    <div class="sec-head">
      <div class="sec-num">{num}</div>
      <div><div class="sec-title">{title}</div>{s}</div>
    </div>'''


# ──────────────────────────── CSS ────────────────────────────
def css(th):
    return f'''
    @page {{ size: A4; margin: 0; }}
    * {{ margin:0; padding:0; box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
    html,body {{ font-family:"Segoe UI","Inter",system-ui,sans-serif; color:#1e2330; background:#fff; line-height:1.55; }}
    .page {{ width:210mm; min-height:297mm; padding:18mm 16mm; position:relative; page-break-after:always; }}
    .page:last-child {{ page-break-after:auto; }}

    /* ---- COVER ---- */
    .cover {{ padding:0; display:flex; flex-direction:column; }}
    .cover-bg {{
      position:absolute; inset:0;
      background:
        radial-gradient(circle at 18% 12%, {th['c2']}55, transparent 42%),
        radial-gradient(circle at 88% 80%, {th['c3']}44, transparent 45%),
        linear-gradient(140deg, {th['c1']} 0%, {th['c2']} 55%, {th['c1']} 100%);
    }}
    .cover-mesh {{ position:absolute; inset:0; opacity:.10;
      background-image:linear-gradient(#fff 1px,transparent 1px),linear-gradient(90deg,#fff 1px,transparent 1px);
      background-size:26px 26px; }}
    .cover-inner {{ position:relative; z-index:2; color:#fff; padding:30mm 22mm; display:flex; flex-direction:column; height:297mm; }}
    .cover-logo {{ width:108px; height:108px; border-radius:30px; background:rgba(255,255,255,.16);
      border:1.5px solid rgba(255,255,255,.4); display:flex; align-items:center; justify-content:center;
      font-size:62px; backdrop-filter:blur(4px); box-shadow:0 18px 50px rgba(0,0,0,.25); }}
    .cover-kicker {{ margin-top:42px; letter-spacing:.32em; font-size:13px; font-weight:600; opacity:.9; text-transform:uppercase; }}
    .cover-h1 {{ font-size:58px; font-weight:800; line-height:1.04; margin-top:14px; letter-spacing:-1px; }}
    .cover-h1 span {{ color:{th['c3']}; }}
    .cover-role {{ margin-top:30px; display:inline-flex; align-items:center; gap:14px; align-self:flex-start;
      background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.34); padding:14px 26px 14px 16px;
      border-radius:60px; font-size:22px; font-weight:700; backdrop-filter:blur(4px); }}
    .cover-role .rb {{ width:46px; height:46px; border-radius:50%; background:#fff; color:{th['c1']};
      display:flex; align-items:center; justify-content:center; font-size:26px; }}
    .cover-sub {{ margin-top:18px; font-size:17px; opacity:.92; max-width:420px; }}
    .cover-foot {{ margin-top:auto; display:flex; justify-content:space-between; align-items:flex-end;
      border-top:1px solid rgba(255,255,255,.25); padding-top:20px; font-size:13px; opacity:.85; }}
    .cover-foot b {{ font-size:15px; }}

    /* ---- HEADER (oddiy sahifa) ---- */
    .phead {{ display:flex; justify-content:space-between; align-items:center; padding-bottom:12px;
      border-bottom:2px solid {th['softline']}; margin-bottom:24px; }}
    .phead-l {{ display:flex; align-items:center; gap:11px; font-weight:700; color:{th['c1']}; font-size:15px; }}
    .phead-l .d {{ width:30px; height:30px; border-radius:9px; background:{th['c1']}; color:#fff;
      display:flex; align-items:center; justify-content:center; font-size:16px; }}
    .phead-r {{ font-size:12px; color:#9aa3b2; font-weight:600; letter-spacing:.05em; }}

    /* ---- SECTION HEAD ---- */
    .sec-head {{ display:flex; gap:16px; align-items:center; margin:32px 0 18px; }}
    .sec-head:first-child {{ margin-top:0; }}
    .sec-num {{ min-width:42px; height:42px; border-radius:12px; font-size:19px; font-weight:800; color:#fff;
      background:linear-gradient(135deg,{th['c1']},{th['c2']}); display:flex; align-items:center; justify-content:center;
      box-shadow:0 6px 16px {th['c1']}40; }}
    .sec-title {{ font-size:23px; font-weight:800; color:#161b26; letter-spacing:-.3px; }}
    .sec-sub {{ font-size:13.5px; color:#7a8497; margin-top:2px; }}

    /* ---- LEDE ---- */
    .lede {{ background:{th['soft']}; border:1px solid {th['softline']}; border-left:5px solid {th['c1']};
      border-radius:14px; padding:18px 22px; font-size:14.5px; color:#33405a; margin-bottom:8px; }}
    .lede b {{ color:{th['c1']}; }}

    /* ---- FEATURE CARD ---- */
    .grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    .fcard {{ display:flex; gap:14px; background:#fff; border:1px solid #e9ecf3; border-radius:16px;
      padding:17px 18px; box-shadow:0 2px 10px rgba(20,30,60,.04); break-inside:avoid; }}
    .fcard-ic {{ min-width:46px; height:46px; border-radius:13px; background:{th['soft']}; color:{th['c1']};
      display:flex; align-items:center; justify-content:center; font-size:24px; }}
    .fcard-title {{ font-weight:750; font-size:15.5px; color:#1b2230; }}
    .fcard-desc {{ font-size:13px; color:#65718a; margin-top:3px; }}
    .fc-list {{ margin:9px 0 0 0; padding-left:0; list-style:none; }}
    .fc-list li {{ font-size:12.5px; color:#4a5670; padding:3px 0 3px 18px; position:relative; }}
    .fc-list li::before {{ content:"›"; position:absolute; left:4px; color:{th['c1']}; font-weight:800; }}

    /* ---- STEPS ---- */
    .steps {{ display:flex; flex-direction:column; gap:10px; }}
    .step {{ display:flex; gap:15px; align-items:flex-start; background:#fff; border:1px solid #eaedf4;
      border-radius:14px; padding:14px 18px; break-inside:avoid; }}
    .step-num {{ min-width:32px; height:32px; border-radius:50%; background:{th['c1']}; color:#fff;
      font-weight:800; font-size:15px; display:flex; align-items:center; justify-content:center; }}
    .step-t {{ font-weight:700; font-size:14.5px; color:#1b2230; }}
    .step-d {{ font-size:13px; color:#65718a; margin-top:2px; }}

    /* ---- PHONE MOCKUP ---- */
    .mock-wrap {{ display:flex; gap:26px; align-items:flex-start; margin:6px 0; }}
    .mock-wrap.center {{ justify-content:center; }}
    .mock-side {{ flex:1; padding-top:6px; }}
    .phone {{ width:280px; min-width:280px; background:#0e1621; border-radius:30px; padding:10px;
      box-shadow:0 22px 55px rgba(15,30,60,.30); position:relative; border:1px solid #243244; }}
    .phone-notch {{ width:120px; height:7px; background:#243244; border-radius:6px; margin:3px auto 9px; }}
    .phone-top {{ display:flex; align-items:center; gap:10px; padding:4px 12px 11px; border-bottom:1px solid #1c2839; }}
    .phone-bava {{ width:38px; height:38px; border-radius:50%; background:linear-gradient(135deg,{th['c1']},{th['c2']});
      display:flex; align-items:center; justify-content:center; font-size:20px; }}
    .phone-binfo {{ display:flex; flex-direction:column; line-height:1.2; }}
    .phone-binfo b {{ color:#fff; font-size:14px; }}
    .phone-binfo span {{ color:#5fb3f3; font-size:11px; }}
    .phone-chat {{ background:#17212b; padding:13px 11px; min-height:120px;
      background-image:radial-gradient(circle at 30% 20%, #1d2c3a 0, transparent 38%); }}
    .tg-row {{ display:flex; gap:7px; margin-bottom:11px; align-items:flex-end; }}
    .tg-left {{ justify-content:flex-start; }}
    .tg-right {{ justify-content:flex-end; }}
    .tg-ava {{ min-width:26px; height:26px; border-radius:50%; background:{th['c1']};
      display:flex; align-items:center; justify-content:center; font-size:14px; }}
    .tg-bubble {{ max-width:200px; padding:8px 11px 16px; border-radius:14px; font-size:12.5px; position:relative; }}
    .tg-in {{ background:#fff; color:#10212e; border-bottom-left-radius:4px; }}
    .tg-out {{ background:{th['c1']}; color:#fff; border-bottom-right-radius:4px; }}
    .tg-time {{ position:absolute; right:9px; bottom:4px; font-size:9px; opacity:.5; }}
    .tg-kb {{ margin-top:9px; display:flex; flex-direction:column; gap:5px; }}
    .tg-btnrow {{ display:flex; gap:5px; }}
    .tg-btn {{ flex:1; background:#eaf2fb; color:#1f6fb2; border-radius:9px; padding:7px 6px;
      text-align:center; font-size:11px; font-weight:600; }}
    .tg-btn-accent {{ background:{th['c1']}; color:#fff; }}
    .tg-note {{ text-align:center; font-size:10.5px; color:#8aa0b3; background:#1c2a38;
      align-self:center; margin:0 auto 11px; padding:4px 12px; border-radius:11px; width:fit-content; }}
    .phone-input {{ display:flex; align-items:center; justify-content:space-between; padding:10px 14px;
      background:#17212b; border-top:1px solid #1c2839; border-radius:0 0 22px 22px; }}
    .phone-input span {{ color:#5a6b7b; font-size:11.5px; }}
    .phone-send {{ width:30px; height:30px; border-radius:50%; background:{th['c1']}; color:#fff;
      display:flex; align-items:center; justify-content:center; font-size:14px; }}
    .mock-cap {{ font-size:12px; color:#8a93a6; text-align:center; margin-top:10px; font-style:italic; }}

    /* ---- STATUS LEGEND ---- */
    .legend {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:9px; }}
    .lg {{ display:flex; align-items:center; gap:10px; background:#fff; border:1px solid #eaedf4;
      border-radius:12px; padding:10px 12px; break-inside:avoid; }}
    .lg-ic {{ font-size:20px; }}
    .lg-t {{ font-weight:700; font-size:13px; }}
    .lg-d {{ font-size:10.5px; color:#6b7689; line-height:1.35; }}

    /* ---- TIP / WARN ---- */
    .tip {{ display:flex; gap:13px; border-radius:13px; padding:15px 18px; margin:14px 0; break-inside:avoid; font-size:13.5px; }}
    .tip-i {{ font-size:22px; }}
    .tip.info {{ background:{th['soft']}; border:1px solid {th['softline']}; color:#3a4663; }}
    .tip.warn {{ background:#fef6e7; border:1px solid #fde6bd; color:#7a5a16; }}
    .tip.ok {{ background:#ecfdf5; border:1px solid #c7f0dd; color:#16623f; }}
    .tip b {{ color:inherit; }}

    /* ---- FOOTER ---- */
    .pfoot {{ position:absolute; bottom:10mm; left:16mm; right:16mm; display:flex; justify-content:space-between;
      font-size:11px; color:#aeb6c4; border-top:1px solid #eef0f5; padding-top:8px; }}
    .pfoot b {{ color:{th['c1']}; }}

    h2.block {{ font-size:16px; font-weight:750; color:#1b2230; margin:22px 0 12px; display:flex; align-items:center; gap:9px; }}
    h2.block::before {{ content:""; width:5px; height:18px; background:{th['c1']}; border-radius:3px; display:inline-block; }}
    '''


def page(content, th, footer_l, pageno):
    return f'''<div class="page">
      <div class="phead">
        <div class="phead-l"><div class="d">{th['icon']}</div> IQTM Workspace · {th['name']}</div>
        <div class="phead-r">YO'RIQNOMA</div>
      </div>
      {content}
      <div class="pfoot"><span>{footer_l}</span><span><b>IQTM Workspace</b> · {pageno}-bet</span></div>
    </div>'''


def cover(th):
    return f'''<div class="page cover">
      <div class="cover-bg"></div>
      <div class="cover-mesh"></div>
      <div class="cover-inner">
        <div class="cover-logo">🤖</div>
        <div class="cover-kicker">IQTM Workspace · Telegram bot</div>
        <div class="cover-h1">Foydalanish<br><span>yo'riqnomasi</span></div>
        <div class="cover-role"><div class="rb">{th['icon']}</div> {th['name']}</div>
        <div class="cover-sub">{th['subtitle']}. Ushbu qo'llanma botning barcha imkoniyatlarini bosqichma-bosqich tushuntiradi.</div>
        <div class="cover-foot">
          <div>Innovatsiyalarni qo'llab-quvvatlash va<br>tijoratlashtirish markazi<br><b>@iqtm_bot</b></div>
          <div style="text-align:right">Versiya 1.0<br><b>2026</b></div>
        </div>
      </div>
    </div>'''


def doc(th, body):
    return f'''<!DOCTYPE html><html lang="uz"><head><meta charset="utf-8">
    <style>{css(th)}</style></head><body>{body}</body></html>'''


# ════════════════════════════ KONTENT: UMUMIY (kirish) ════════════════════════════
def intro_page(th, footer):
    onboard = phone([
        {"type": "user", "text": "/start", "time": "09:00"},
        {"type": "bot", "text": "👋 Salom! Arizangiz yuborildi.<br>Administrator tasdiqlagunicha kuting. ⏳", "time": "09:00"},
        {"type": "note", "text": "Super admin tasdiqlagach 👇"},
        {"type": "bot", "text": "🎉 Tabriklaymiz! Siz tizimga qo'shildingiz.", "time": "09:05",
         "buttons": [[{"t": "🏠 Asosiy menyu", "accent": True}]]},
    ])
    c = section("01", "Botga kirish", "Birinchi marta foydalanish")
    c += f'''<div class="lede"><b>IQTM</b> (Innovatsiyalarni qo'llab-quvvatlash va tijoratlashtirish markazi)
      jamoasini boshqarish tizimi. Vazifalar, loyihalar, statistika — barchasi bitta joyda.
      Barcha amallar <b>tugmalar</b> orqali bajariladi, <b>🏠 Menyu</b> esa har doim boshiga qaytaradi.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += steps([
        ("Botni oching", "Havola orqali yoki <b>@iqtm_bot</b> ni qidirib toping."),
        ("/start bosing", "Pastdagi <b>«▶️ Start»</b> tugmasini bosing — ariza avtomatik yuboriladi."),
        ("Tasdiqni kuting", "Super admin sizga rol va bo'lim belgilaydi."),
        ("Ishni boshlang", "Tasdiqlangach asosiy menyu ochiladi. ✅"),
    ])
    c += '</div>' + phone_wrap(onboard, "Ariza berish va tasdiqlanish jarayoni") + '</div>'
    c += status_block(th)
    return page(c, th, footer, 2)


def phone_wrap(ph, cap):
    return f'<div style="display:flex;flex-direction:column;align-items:center">{ph}<div class="mock-cap">{cap}</div></div>'


def status_block(th):
    legend = [
        ("🆕", "Yangi", "Hali boshlanmagan"),
        ("🔄", "Jarayonda", "Ish davom etmoqda"),
        ("🔍", "Tekshiruvda", "Tekshirilmoqda"),
        ("✅", "Bajarildi", "Yakunlandi"),
        ("⚠️", "Kechikdi", "Muddati o'tgan"),
        ("🔒", "Qulflangan", "Muddat o'zgarmas"),
    ]
    lg = "".join(
        f'<div class="lg"><div class="lg-ic">{i}</div><div><div class="lg-t">{t}</div><div class="lg-d">{d}</div></div></div>'
        for i, t, d in legend
    )
    return (
        f'<div style="break-inside:avoid;margin-top:14px">'
        f'<h2 class="block">Vazifa holatlari (statuslar)</h2>'
        f'<div class="legend">{lg}</div>'
        f'</div>'
    )


# ════════════════════════════ SUPER ADMIN ════════════════════════════
def build_super():
    th = THEMES["super"]
    footer = "Super Admin yo'riqnomasi"
    pages = [cover(th), intro_page(th, footer)]

    # --- Sahifa 3: Asosiy menyu + Vazifalar ---
    main_menu = phone([
        {"type": "bot", "text": "🤖 <b>IQTM Workspace</b><br>👑 Xush kelibsiz, Super Admin!", "time": "09:10",
         "buttons": [
             [{"t": "📋 Vazifalar"}], [{"t": "📁 Loyihalar"}],
             [{"t": "👥 Guruh sozlamalari 🔔2"}],
             [{"t": "📊 Statistika"}], [{"t": "⚙️ Bot sozlamalari"}],
         ]},
    ])
    c = section("02", "Asosiy menyu", "Super admin — 5 ta bo'lim")
    c += f'''<div class="lede">Super admin <b>butun tizimni</b> boshqaradi. Asosiy menyu 5 ta bo'limga ajratilgan.
      <b>🔔</b> belgisi yangi arizalar borligini bildiradi.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += "".join([
        feature_card("📋", "Vazifalar", "Barcha bo'limlardagi vazifalarni yaratish va kuzatish."),
        feature_card("📁", "Loyihalar", "Loyihalar va ularning bosqichlarini boshqarish."),
        feature_card("👥", "Guruh sozlamalari", "Xodimlar, rollar, bo'limlar va arizalar."),
        feature_card("📊", "Statistika", "Hisobotlar, reyting va haftalik natijalar."),
        feature_card("⚙️", "Bot sozlamalari", "Guruh, topiclar va zaxira nusxa."),
    ])
    c += '</div>' + phone_wrap(main_menu, "Super admin asosiy menyusi") + '</div>'
    pages.append(page(c, th, footer, 3))

    # --- Sahifa 4: Vazifa yaratish ---
    task_create = phone([
        {"type": "user", "text": "➕ Vazifa qo'shish", "time": "10:00"},
        {"type": "bot", "text": "Vazifa turini tanlang:", "time": "10:00",
         "buttons": [[{"t": "📁 Loyiha bo'yicha"}], [{"t": "📋 Erkin vazifa", "accent": True}]]},
        {"type": "bot", "text": "🏢 Bo'limlarni tanlang (bir nechta):", "time": "10:01",
         "buttons": [[{"t": "✅ Dasturlash"}, {"t": "⬜ Dizayn"}], [{"t": "✅ SMM"}], [{"t": "➡️ Davom etish", "accent": True}]]},
        {"type": "note", "text": "Har bo'lim uchun ish tavsifi + muddat 🔒"},
    ])
    c = section("03", "Vazifa yaratish", "Bir vazifa — bir nechta bo'limga")
    c += f'''<div class="lede">Super admin vazifani <b>bir nechta bo'limga</b> birdan biriktirishi mumkin.
      Har bo'lim uchun alohida ish tavsifi yoziladi. Muddat <b>🔒 qulflangan</b> bo'ladi —
      uni faqat super admin o'zgartira oladi.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += steps([
        ("Tur tanlang", "<b>Loyiha bo'yicha</b> yoki <b>Erkin</b> vazifa."),
        ("Bo'limlarni belgilang", "Bir yoki bir nechta bo'lim — ✅ bilan tanlanadi."),
        ("Nom va tavsif", "Vazifa nomi, so'ng har bo'lim uchun ish tavsifi."),
        ("Muddat tanlang", "Kalendardan sana — bu muddat qulflanadi 🔒."),
        ("Avtomatik xabar", "Har bo'limning o'z mavzusiga bildirishnoma boradi 📨."),
    ])
    c += '</div>' + phone_wrap(task_create, "Ko'p bo'limli vazifa yaratish") + '</div>'
    pages.append(page(c, th, footer, 4))

    # --- Sahifa 5: Loyihalar ---
    proj = phone([
        {"type": "user", "text": "📂 Loyihalar ro'yxati", "time": "11:00"},
        {"type": "bot", "text": "📂 <b>Loyihalar</b> — 12 ta · Sahifa 1/2<br><br> 1. 🟡 Veb-sayt<br> 2. 🟢 Mobil ilova<br> 3. 🔵 CRM tizimi", "time": "11:00",
         "buttons": [[{"t": "1"}, {"t": "2"}, {"t": "3"}, {"t": "4"}, {"t": "5"}],
                     [{"t": "Keyingi ▶️"}], [{"t": "➕ Loyiha qo'shish", "accent": True}]]},
    ])
    c = section("04", "Loyihalar", "Yaratish, holat va bosqichlar")
    c += f'''<div class="lede">Loyihalar ro'yxati raqamli ko'rinishda, <b>10 tadan</b> sahifalanadi.
      Raqamni bosib loyihani ochasiz. Yaratishda nom, tasnif va holat kiritiladi.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += "".join([
        feature_card("➕", "Loyiha qo'shish", "Nom → tasnif → holat. Sodda 3 qadam.",
                     ["🔵 Rejalashtirilgan", "🟡 Jarayonda", "🟢 Yakunlangan", "🔴 To'xtatilgan"]),
        feature_card("📌", "Holatni o'zgartirish", "Loyiha holatini istalgan paytda yangilash."),
        feature_card("📋", "Bosqichlar", "Loyihaga bosqichlar qo'shish va kuzatish."),
    ])
    c += '</div>' + phone_wrap(proj, "Sahifalangan loyihalar ro'yxati") + '</div>'
    pages.append(page(c, th, footer, 5))

    # --- Sahifa 6: Jamoa (xodim qo'shish) ---
    invite = phone([
        {"type": "user", "text": "🔗 Havola orqali", "time": "12:00"},
        {"type": "bot", "text": "🔗 <b>Yangi xodim qo'shish</b><br>Havolani xodimga yuboring:<br><br>https://t.me/iqtm_bot", "time": "12:00",
         "buttons": [[{"t": "📨 Havolani ulashish", "accent": True}], [{"t": "🔗 Havolani ochish"}]]},
    ])
    c = section("05", "Jamoa boshqaruvi", "Xodimlar, rollar va arizalar")
    c += f'''<div class="lede"><b>👥 Guruh sozlamalari</b> bo'limida jamoani to'liq boshqarasiz.
      Yangi xodimni <b>qo'lda</b> yoki <b>havola orqali</b> qo'shish mumkin.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += steps([
        ("Havola orqali qo'shish", "<b>Havolani ulashish</b> tugmasi tayyor matn bilan yuboradi."),
        ("Arizani qabul qiling", "<b>📥 Qabul</b> bo'limida yangi arizalar ko'rinadi."),
        ("Rol belgilang", "Super / Admin / Worker — kerakli rolni tanlang."),
        ("Bo'lim biriktiring", "Xodimni tegishli bo'limga joylang."),
    ])
    c += f'''<div class="tip info"><div class="tip-i">👑</div><div><b>Rollar bo'limi</b> har bir rolning
      imkoniyatlarini ko'rsatadi — kim nimaga ruxsatli ekani aniq ko'rinadi.</div></div>'''
    c += '</div>' + phone_wrap(invite, "Havola orqali xodim taklif qilish") + '</div>'
    pages.append(page(c, th, footer, 6))

    # --- Sahifa 7: Statistika + Bot sozlamalari ---
    stats = phone([
        {"type": "user", "text": "📈 Haftalik hisobot", "time": "13:00"},
        {"type": "bot", "text": "📈 <b>Haftalik hisobot</b><br>Jami: 48 | ✅32 🔄12 ⚠️4<br>Bajarilish: 67%", "time": "13:00",
         "buttons": [[{"t": "📤 Guruhga yuborish", "accent": True}], [{"t": "🏠 Menyu"}]]},
    ])
    c = section("06", "Statistika va sozlamalar", "Hisobotlar va tizim sozlamalari")
    c += f'''<div class="lede">Statistikani <b>ko'rganingizda guruhga yuborilmaydi</b>.
      Faqat <b>📤 Guruhga yuborish</b> tugmasi bosilganda yuboriladi. Har <b>juma soat 18:00</b> da
      hisobot avtomatik guruhga jo'natiladi.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += "".join([
        feature_card("📊", "To'liq statistika", "Barcha bo'limlar bo'yicha umumiy ko'rsatkichlar."),
        feature_card("🏆", "Reyting", "Eng faol xodimlar va bo'limlar reytingi."),
        feature_card("🔗", "Guruhni ulash", "Botni asosiy ishchi guruhga bog'lash."),
        feature_card("📡", "Topic sozlash", "Forum mavzularini bo'limlarga biriktirish."),
        feature_card("💾", "Zaxira (backup)", "Ma'lumotlar bazasining nusxasini olish."),
    ])
    c += '</div>' + phone_wrap(stats, "Hisobotni ko'rish va guruhga yuborish") + '</div>'
    pages.append(page(c, th, footer, 7))

    return doc(th, "".join(pages))


# ════════════════════════════ ADMIN ════════════════════════════
def build_admin():
    th = THEMES["admin"]
    footer = "Bo'lim mas'uli yo'riqnomasi"
    pages = [cover(th), intro_page(th, footer)]

    main_menu = phone([
        {"type": "bot", "text": "🤖 <b>IQTM Workspace</b><br>🔑 Xush kelibsiz, Bo'lim mas'uli!", "time": "09:10",
         "buttons": [
             [{"t": "📋 Vazifalar ro'yxati"}], [{"t": "➕ Vazifa qo'shish"}],
             [{"t": "📁 Mening vazifalarim"}], [{"t": "👷 Mening xodimlarim"}],
             [{"t": "📊 Statistika"}, {"t": "🏆 Reyting"}], [{"t": "📈 Hisobot"}],
         ]},
    ])
    c = section("02", "Asosiy menyu", "Bo'lim mas'uli imkoniyatlari")
    c += f'''<div class="lede">Admin — <b>o'z bo'limining</b> rahbari. U bo'limga vazifa qo'yadi,
      xodimlarni boshqaradi va bo'lim statistikasini kuzatadi.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += "".join([
        feature_card("📋", "Vazifalar ro'yxati", "Bo'limingizdagi barcha vazifalar — filtr va sahifalash bilan."),
        feature_card("➕", "Vazifa qo'shish", "Bo'lim xodimiga yangi vazifa biriktirish."),
        feature_card("📁", "Mening vazifalarim", "Shaxsan sizga tegishli vazifalar."),
        feature_card("👷", "Mening xodimlarim", "Bo'lim a'zolari ro'yxati va holati."),
        feature_card("📊", "Statistika / Reyting", "Bo'lim ko'rsatkichlari va xodimlar reytingi."),
        feature_card("📈", "Hisobot", "Bo'lim bo'yicha hisobot."),
    ])
    c += '</div>' + phone_wrap(main_menu, "Admin asosiy menyusi") + '</div>'
    pages.append(page(c, th, footer, 3))

    # --- Vazifa qo'shish ---
    tcreate = phone([
        {"type": "user", "text": "➕ Vazifa qo'shish", "time": "10:00"},
        {"type": "bot", "text": "👤 Mas'ul xodimni tanlang:", "time": "10:00",
         "buttons": [[{"t": "Ali Valiyev"}], [{"t": "Hasan Husanov"}], [{"t": "— Mas'ul yo'q —"}]]},
        {"type": "bot", "text": "📝 Vazifa nomini kiriting:", "time": "10:01"},
        {"type": "user", "text": "Bosh sahifa dizayni", "time": "10:02"},
        {"type": "bot", "text": "📅 Muddatni tanlang:", "time": "10:02",
         "buttons": [[{"t": "◀️"}, {"t": "Iyun 2026"}, {"t": "▶️"}], [{"t": "12"}, {"t": "13"}, {"t": "14", "accent": True}]]},
    ])
    c = section("03", "Vazifa qo'shish", "Bo'lim xodimiga vazifa biriktirish")
    c += f'''<div class="lede">Admin sifatida siz <b>o'z bo'limingiz</b> xodimlariga vazifa qo'yasiz.
      Xodim tanlanadi, nom va tavsif yoziladi, muddat belgilanadi.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += steps([
        ("Xodimni tanlang", "Bo'lim ro'yxatidan mas'ul xodimni belgilang."),
        ("Nom va tavsif", "Vazifa nomi va qisqa izoh kiriting."),
        ("Muddat tanlang", "Kalendardan tugash sanasini belgilang."),
        ("Tayyor!", "Xodimga va bo'lim mavzusiga xabar boradi 📨."),
    ])
    c += f'''<div class="tip warn"><div class="tip-i">🔒</div><div>Super admin qo'ygan
      <b>ko'p bo'limli vazifalarda</b> muddat qulflangan bo'ladi — uni o'zgartira olmaysiz,
      lekin <b>o'z bo'limingizga xodim belgilashingiz</b> mumkin.</div></div>'''
    c += '</div>' + phone_wrap(tcreate, "Vazifa qo'shish jarayoni") + '</div>'
    pages.append(page(c, th, footer, 4))

    # --- Vazifalarni boshqarish + statuslar ---
    tlist = phone([
        {"type": "user", "text": "📋 Vazifalar ro'yxati", "time": "11:00"},
        {"type": "bot", "text": "📋 <b>Dizayn vazifalari</b> — 8 ta<br><br> 1. 🔄 Logotip<br> 2. 🔍 Banner<br> 3. ✅ Vizitka", "time": "11:00",
         "buttons": [[{"t": "📋 Barchasi"}, {"t": "🔄 Jarayonda"}, {"t": "🔍 Tekshiruv"}],
                     [{"t": "1"}, {"t": "2"}, {"t": "3"}], [{"t": "🏠 Menyu"}]]},
    ])
    c = section("04", "Vazifalarni boshqarish", "Filtrlash, holat va xodim belgilash")
    c += f'''<div class="lede">Vazifalar ro'yxati <b>holat bo'yicha filtrlanadi</b> va 10 tadan sahifalanadi.
      Raqamni bosib vazifani ochasiz va boshqarasiz.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += "".join([
        feature_card("🔍", "Filtrlash", "Yangi / Jarayonda / Tekshiruvda / Bajarildi bo'yicha ajratish."),
        feature_card("📌", "Holatni o'zgartirish", "Vazifa holatini yangilash."),
        feature_card("👤", "Xodim belgilash", "Ko'p bo'limli vazifada o'z bo'lim xodimini tayinlash."),
        feature_card("✅", "Bajarildi deb belgilash", "Vazifani yakunlangan deb belgilash."),
    ])
    c += '</div>' + phone_wrap(tlist, "Filtr va sahifalash bilan ro'yxat") + '</div>'
    pages.append(page(c, th, footer, 5))

    return doc(th, "".join(pages))


# ════════════════════════════ WORKER ════════════════════════════
def build_worker():
    th = THEMES["worker"]
    footer = "Xodim yo'riqnomasi"
    pages = [cover(th), intro_page(th, footer)]

    main_menu = phone([
        {"type": "bot", "text": "🤖 <b>IQTM Workspace</b><br>👋 Xush kelibsiz, xodim!", "time": "09:10",
         "buttons": [
             [{"t": "📁 Mening vazifalarim"}],
             [{"t": "👤 Shaxsiy vazifa qo'shish"}],
             [{"t": "📊 Shaxsiy statistika"}],
             [{"t": "🔔 Eslatma o'rnatish"}],
             [{"t": "❓ Yordam"}],
         ]},
    ])
    c = section("02", "Asosiy menyu", "Xodim imkoniyatlari")
    c += f'''<div class="lede">Xodim sifatida siz o'zingizga biriktirilgan vazifalarni bajarasiz,
      ularning <b>holatini yangilab turasiz</b> va o'zingiz uchun shaxsiy vazifalar qo'shishingiz mumkin.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += "".join([
        feature_card("📁", "Mening vazifalarim", "Sizga biriktirilgan barcha vazifalar."),
        feature_card("👤", "Shaxsiy vazifa", "O'zingiz uchun shaxsiy vazifa yaratish."),
        feature_card("📊", "Shaxsiy statistika", "Sizning bajarilish ko'rsatkichlaringiz."),
        feature_card("🔔", "Eslatma", "Vazifa uchun eslatma vaqtini o'rnatish."),
    ])
    c += '</div>' + phone_wrap(main_menu, "Xodim asosiy menyusi") + '</div>'
    pages.append(page(c, th, footer, 3))

    # --- Vazifa holatini o'zgartirish ---
    tstatus = phone([
        {"type": "bot", "text": "📋 <b>Mening vazifalarim</b> — 4 ta<br><br> 1. 🔄 Logotip dizayni<br> 2. 🆕 Banner", "time": "10:00",
         "buttons": [[{"t": "1"}, {"t": "2"}, {"t": "3"}, {"t": "4"}], [{"t": "🏠 Menyu"}]]},
        {"type": "bot", "text": "🔄 <b>Vazifa #12</b><br>📝 Logotip dizayni<br>⏰ Muddat: 14-iyun", "time": "10:01",
         "buttons": [[{"t": "📌 Holat o'zgartirish", "accent": True}], [{"t": "✅ Bajarildi"}]]},
        {"type": "bot", "text": "Yangi holatni tanlang:", "time": "10:02",
         "buttons": [[{"t": "🔄 Jarayonda"}], [{"t": "🔍 Tekshiruvda"}], [{"t": "✅ Bajarildi", "accent": True}]]},
    ])
    c = section("03", "Vazifa holatini yangilash", "Ishingiz qay bosqichda?")
    c += f'''<div class="lede">Eng muhim vazifangiz — vazifa <b>holatini o'z vaqtida yangilab turish</b>.
      Bu rahbariyatga ishning qay bosqichda ekanini ko'rsatadi.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += steps([
        ("Vazifani oching", "Ro'yxatdan raqamni bosib vazifani oching."),
        ("Holat o'zgartirish", "<b>📌 Holat o'zgartirish</b> tugmasini bosing."),
        ("Bosqichni tanlang", "🔄 Jarayonda → 🔍 Tekshiruvda → ✅ Bajarildi."),
        ("Avtomatik xabar", "Holat o'zgarishi guruhga bildiriladi 📨."),
    ])
    c += '</div>' + phone_wrap(tstatus, "Vazifa holatini o'zgartirish") + '</div>'
    pages.append(page(c, th, footer, 4))

    # --- Shaxsiy vazifa + eslatma ---
    personal = phone([
        {"type": "user", "text": "👤 Shaxsiy vazifa qo'shish", "time": "11:00"},
        {"type": "bot", "text": "👤 <b>Shaxsiy vazifa</b><br>Vazifa nomini kiriting:", "time": "11:00"},
        {"type": "user", "text": "Hujjatlarni tartiblash", "time": "11:01"},
        {"type": "bot", "text": "📄 Tavsif kiriting yoki o'tkazib yuboring:", "time": "11:01",
         "buttons": [[{"t": "⏭ O'tkazib yuborish"}]]},
        {"type": "bot", "text": "📅 Muddatni tanlang:", "time": "11:02",
         "buttons": [[{"t": "12"}, {"t": "13"}, {"t": "14", "accent": True}, {"t": "15"}]]},
    ])
    c = section("04", "Shaxsiy vazifa va eslatma", "O'zingiz uchun rejalashtirish")
    c += f'''<div class="lede">O'zingiz uchun <b>shaxsiy vazifa</b> qo'shishingiz mumkin. Ular ro'yxatda
      <b>👤 belgisi</b> bilan ajralib turadi va faqat sizga ko'rinadi — rahbariyat ro'yxatida chiqmaydi.</div>'''
    c += '<div class="mock-wrap"><div class="mock-side">'
    c += "".join([
        feature_card("👤", "Shaxsiy vazifa", "Nom → tavsif → muddat. Faqat sizga ko'rinadi.",
                     ["O'zingiz boshqarasiz", "Holatini yangilaysiz", "Kerak bo'lsa o'chirasiz"]),
        feature_card("🔔", "Eslatma o'rnatish", "Muhim vazifa uchun eslatma vaqtini belgilang — bot vaqtida eslatadi."),
    ])
    c += f'''<div class="tip ok"><div class="tip-i">✅</div><div><b>Tayyor!</b> Endi siz botning
      barcha imkoniyatlaridan foydalana olasiz. Savol tug'ilsa — <b>❓ Yordam</b> tugmasini bosing.</div></div>'''
    c += '</div>' + phone_wrap(personal, "Shaxsiy vazifa yaratish") + '</div>'
    pages.append(page(c, th, footer, 5))

    return doc(th, "".join(pages))


# ──────────────────────────── YOZISH ────────────────────────────
def main():
    files = {
        "01_Super_Admin_qollanma": build_super(),
        "02_Admin_qollanma": build_admin(),
        "03_Xodim_qollanma": build_worker(),
    }
    for name, content in files.items():
        path = os.path.join(OUT_DIR, name + ".html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("WROTE:", path)


if __name__ == "__main__":
    main()
