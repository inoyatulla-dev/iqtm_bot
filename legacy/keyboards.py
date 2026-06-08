from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def menu_button():
    return [InlineKeyboardButton("🏠 Menyu", callback_data="menu")]


def back_button(cb="menu"):
    return [InlineKeyboardButton("◀️ Orqaga", callback_data=cb)]


# ─────────────────────────── MAIN MENUS ────────────────────────────

def super_menu_kb(pending_count: int = 0):
    notif = f" 🔔{pending_count}" if pending_count > 0 else ""
    buttons = [
        [InlineKeyboardButton("📋 Vazifalar",                      callback_data="task_menu")],
        [InlineKeyboardButton("📁 Loyihalar",                      callback_data="proj_menu")],
        [InlineKeyboardButton(f"👥 Guruh sozlamalari{notif}",      callback_data="group_settings_menu")],
        [InlineKeyboardButton("📊 Statistika",                     callback_data="stats_menu")],
        [InlineKeyboardButton("⚙️ Bot sozlamalari",                callback_data="bot_settings_menu")],
    ]
    return InlineKeyboardMarkup(buttons)


def task_submenu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Vazifalar ro'yxati",  callback_data="dep_tasks")],
        [InlineKeyboardButton("➕ Vazifa qo'shish",     callback_data="task_create")],
        menu_button(),
    ])


def proj_submenu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 Loyihalar ro'yxati",  callback_data="proj_list")],
        [InlineKeyboardButton("➕ Loyiha qo'shish",     callback_data="proj_create")],
        menu_button(),
    ])


def group_settings_submenu_kb(pending_count: int = 0):
    notif = f" 🔔{pending_count}" if pending_count > 0 else ""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Xodimlar ro'yxati",          callback_data="user_list")],
        [InlineKeyboardButton("👑 Rollar",                      callback_data="role_manage")],
        [InlineKeyboardButton(f"📥 Qabul{notif}",              callback_data="pending_list")],
        [InlineKeyboardButton("🏢 Bo'limlar",                   callback_data="dep_list")],
        [InlineKeyboardButton("👤 Guruh a'zolari",             callback_data="group_members")],
        menu_button(),
    ])


def stats_submenu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 To'liq statistika",   callback_data="stats_global")],
        [InlineKeyboardButton("📈 Haftalik hisobot",    callback_data="report_weekly")],
        [InlineKeyboardButton("🏆 Reyting",             callback_data="rating_global")],
        menu_button(),
    ])


def bot_settings_submenu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Guruhni ulash",       callback_data="settings_group")],
        [InlineKeyboardButton("📡 Topic sozlash",       callback_data="topic_settings")],
        [InlineKeyboardButton("💾 Zaxira (backup)",     callback_data="backup_db")],
        [InlineKeyboardButton("❓ Yo'riqnoma",          callback_data="help")],
        menu_button(),
    ])


def admin_menu_kb():
    buttons = [
        [InlineKeyboardButton("📋 Vazifalar ro'yxati",  callback_data="dep_tasks")],
        [InlineKeyboardButton("➕ Vazifa qo'shish",     callback_data="task_create")],
        [InlineKeyboardButton("📁 Mening vazifalarim",  callback_data="my_tasks")],
        [InlineKeyboardButton("👷 Mening xodimlarim",   callback_data="my_workers")],
        [
            InlineKeyboardButton("📊 Statistika",       callback_data="stats_dep"),
            InlineKeyboardButton("🏆 Reyting",          callback_data="rating_dep"),
        ],
        [InlineKeyboardButton("📈 Hisobot",             callback_data="report_dep")],
    ]
    return InlineKeyboardMarkup(buttons)


def worker_menu_kb():
    buttons = [
        [InlineKeyboardButton("📁 Mening vazifalarim",      callback_data="my_tasks")],
        [InlineKeyboardButton("👤 Shaxsiy vazifa qo'shish", callback_data="task_personal_create")],
        [InlineKeyboardButton("📊 Shaxsiy statistika",      callback_data="stats_personal")],
        [InlineKeyboardButton("🔔 Eslatma o'rnatish",       callback_data="reminder_set")],
        [InlineKeyboardButton("❓ Yordam",                  callback_data="help")],
    ]
    return InlineKeyboardMarkup(buttons)


# ─────────────────────────── CONFIRM ────────────────────────────

def confirm_kb(yes_cb: str, no_cb: str = "menu"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Ha", callback_data=yes_cb),
            InlineKeyboardButton("❌ Yo'q", callback_data=no_cb),
        ]
    ])


# ─────────────────────────── USERS ────────────────────────────

def user_list_kb(users):
    buttons = []
    for u in users:
        role_icon = {"super": "👑", "admin": "🔑", "worker": "👤"}.get(u["role"], "👤")
        status_icon = "✅" if u["status"] == "faol" else "🚫"
        label = f"{status_icon} {role_icon} {u['name']}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"user_view:{u['id']}")])
    buttons.append([
        InlineKeyboardButton("➕ Qo'lda qo'shish", callback_data="user_add"),
        InlineKeyboardButton("🔗 Havola orqali",   callback_data="invite_link"),
    ])
    buttons.append(menu_button())
    return InlineKeyboardMarkup(buttons)


def user_actions_kb(user_id: int, current_role: str, current_status: str):
    buttons = [
        [InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"user_edit:{user_id}")],
        [InlineKeyboardButton("👑 Rol o'zgartirish", callback_data=f"user_role:{user_id}")],
    ]
    if current_status == "faol":
        buttons.append([InlineKeyboardButton("🚫 Bloklash", callback_data=f"user_block:{user_id}")])
    else:
        buttons.append([InlineKeyboardButton("✅ Faollashtirish", callback_data=f"user_unblock:{user_id}")])
    buttons.append([InlineKeyboardButton("🗑 O'chirish", callback_data=f"user_del_confirm:{user_id}")])
    buttons.append(back_button("user_list"))
    return InlineKeyboardMarkup(buttons)


def role_select_kb(user_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👤 Worker", callback_data=f"user_setrole:{user_id}:worker"),
            InlineKeyboardButton("🔑 Admin", callback_data=f"user_setrole:{user_id}:admin"),
            InlineKeyboardButton("👑 Super", callback_data=f"user_setrole:{user_id}:super"),
        ],
        back_button(f"user_view:{user_id}"),
    ])


# ─────────────────────────── DEPARTMENTS ────────────────────────────

def dep_list_kb(deps, show_add=True):
    buttons = []
    for d in deps:
        buttons.append([InlineKeyboardButton(
            f"{d['emoji']} {d['name']}", callback_data=f"dep_view:{d['id']}"
        )])
    if show_add:
        buttons.append([InlineKeyboardButton("➕ Yangi bo'lim", callback_data="dep_add")])
    buttons.append(menu_button())
    return InlineKeyboardMarkup(buttons)


def dep_actions_kb(dep_id: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"dep_edit:{dep_id}")],
        [InlineKeyboardButton("👑 Mas'ul tayinlash", callback_data=f"dep_set_admin:{dep_id}")],
        [InlineKeyboardButton("🔗 Topic ID sozlash", callback_data=f"dep_set_topic:{dep_id}")],
        [InlineKeyboardButton("🗑 O'chirish", callback_data=f"dep_del_confirm:{dep_id}")],
        back_button("dep_list"),
    ])


def dep_select_kb(deps, prefix: str):
    buttons = []
    for d in deps:
        buttons.append([InlineKeyboardButton(
            f"{d['emoji']} {d['name']}", callback_data=f"{prefix}:{d['id']}"
        )])
    buttons.append(back_button())
    return InlineKeyboardMarkup(buttons)


# ─────────────────────────── TASKS ────────────────────────────

_TASK_SICON = {
    "faol":        "🆕",
    "jarayonda":   "🔄",
    "tekshiruvda": "🔍",
    "bajarildi":   "✅",
    "kechikdi":    "⚠️",
}

_TASK_PER_PAGE = 10

_TASK_FILTERS = [
    ("all",         "📋", "Barchasi"),
    ("faol",        "🆕", "Yangi"),
    ("jarayonda",   "🔄", "Jarayonda"),
    ("tekshiruvda", "🔍", "Tekshiruv"),
    ("bajarildi",   "✅", "Bajarildi"),
    ("kechikdi",    "⚠️", "Kechikdi"),
]


def _filter_tasks(tasks, status_filter: str):
    if not status_filter or status_filter == "all":
        return tasks
    return [t for t in tasks if t["status"] == status_filter]


def task_list_paged_text(all_tasks, page: int, status_filter: str, title: str) -> str:
    tasks = _filter_tasks(all_tasks, status_filter)
    start = page * _TASK_PER_PAGE
    page_tasks = tasks[start:start + _TASK_PER_PAGE]
    total_pages = max(1, (len(tasks) + _TASK_PER_PAGE - 1) // _TASK_PER_PAGE)

    header = f"📋 <b>{title}</b> — {len(tasks)} ta"
    if total_pages > 1:
        header += f"  |  Sahifa {page + 1}/{total_pages}"

    lines = [header]
    if status_filter and status_filter != "all":
        lbl = next((l for v, _, l in _TASK_FILTERS if v == status_filter), status_filter)
        lines.append(f"<i>Filtr: {lbl}</i>")
    lines.append("")

    if not page_tasks:
        lines.append("Vazifalar topilmadi.")
    else:
        for i, t in enumerate(page_tasks):
            si = _TASK_SICON.get(t["status"], "❓")
            locked = " 🔒" if t.get("is_locked") else ""
            personal = "👤 " if t.get("type") == "personal" else ""
            n = start + i + 1
            lines.append(f"{n:>2}. {personal}{si}  {t['name'][:40]}{locked}")

    lines += ["", "<i>Raqamni bosib vazifani oching 👇</i>"]
    return "\n".join(lines)


def task_list_paged_kb(all_tasks, page: int, status_filter: str, base_cb: str):
    """base_cb: 'dep_tasks' yoki 'my_tasks'"""
    tasks = _filter_tasks(all_tasks, status_filter)
    start = page * _TASK_PER_PAGE
    page_tasks = tasks[start:start + _TASK_PER_PAGE]
    total_pages = max(1, (len(tasks) + _TASK_PER_PAGE - 1) // _TASK_PER_PAGE)

    buttons = []

    # Filtr satrlari (2 qator x 3 ta)
    row1, row2 = [], []
    for i, (val, ico, lbl) in enumerate(_TASK_FILTERS):
        mark = "✓" if val == status_filter else ""
        label = f"{ico}{mark} {lbl}" if mark else f"{ico} {lbl}"
        btn = InlineKeyboardButton(label, callback_data=f"{base_cb}:{val}:0")
        if i < 3:
            row1.append(btn)
        else:
            row2.append(btn)
    buttons.append(row1)
    buttons.append(row2)

    # Raqam tugmalari (5 ustun)
    row = []
    for i, t in enumerate(page_tasks):
        row.append(InlineKeyboardButton(str(i + 1), callback_data=f"task_view:{t['id']}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Pagination nav
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"{base_cb}:{status_filter}:{page - 1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"{base_cb}:{status_filter}:{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append(menu_button())
    return InlineKeyboardMarkup(buttons)


def task_list_kb(tasks, back_cb="menu"):
    buttons = []
    for t in tasks:
        icon = _TASK_SICON.get(t["status"], "❓")
        label = f"{icon} #{t['id']} {t['name'][:30]}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"task_view:{t['id']}")])
    buttons.append(back_button(back_cb))
    return InlineKeyboardMarkup(buttons)


def task_actions_kb(task_id: int, user_role: str, is_masul: bool, dep_match: bool, is_personal_owner: bool = False):
    buttons = []
    can_manage = is_masul or user_role in ("super", "admin") or is_personal_owner
    can_edit = user_role == "super" or (user_role == "admin" and dep_match) or is_personal_owner
    if can_manage:
        buttons.append([InlineKeyboardButton("📌 Holat o'zgartirish", callback_data=f"task_status_menu:{task_id}")])
    if can_manage:
        buttons.append([InlineKeyboardButton("✅ Bajarildi", callback_data=f"task_done:{task_id}")])
    if can_edit:
        buttons.append([InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"task_edit:{task_id}")])
        buttons.append([InlineKeyboardButton("🗑 O'chirish", callback_data=f"task_del_confirm:{task_id}")])
    buttons.append(back_button("my_tasks" if is_personal_owner else "menu"))
    return InlineKeyboardMarkup(buttons)


TASK_STATUSES = [
    ("faol",       "🆕 Yangi"),
    ("jarayonda",  "🔄 Jarayonda"),
    ("tekshiruvda", "🔍 Tekshiruvda"),
    ("bajarildi",  "✅ Bajarildi"),
]

TD_STATUSES = [
    ("jarayonda",  "🔄 Jarayonda"),
    ("tekshiruvda", "🔍 Tekshiruvda"),
    ("bajarildi",  "✅ Bajarildi"),
]


def task_status_select_kb(task_id: int, current: str):
    buttons = []
    for val, label in TASK_STATUSES:
        mark = " ◀" if val == current else ""
        buttons.append([InlineKeyboardButton(f"{label}{mark}", callback_data=f"task_setstatus:{task_id}:{val}")])
    buttons.append(back_button(f"task_view:{task_id}"))
    return InlineKeyboardMarkup(buttons)


def td_status_select_kb(td_id: int, current: str, task_id: int):
    buttons = []
    for val, label in TD_STATUSES:
        mark = " ◀" if val == current else ""
        buttons.append([InlineKeyboardButton(f"{label}{mark}", callback_data=f"td_setstatus:{td_id}:{val}")])
    buttons.append(back_button(f"task_view:{task_id}"))
    return InlineKeyboardMarkup(buttons)


def user_select_kb(users, prefix: str, back_cb="menu"):
    buttons = []
    for u in users:
        buttons.append([InlineKeyboardButton(u["name"], callback_data=f"{prefix}:{u['id']}")])
    buttons.append([InlineKeyboardButton("— Mas'ul yo'q —", callback_data=f"{prefix}:none")])
    buttons.append(back_button(back_cb))
    return InlineKeyboardMarkup(buttons)


# ─────────────────────────── PROJECTS ────────────────────────────

_PROJ_SICON = {
    "rejalashtirilgan": "🔵",
    "jarayonda":        "🟡",
    "yakunlangan":      "🟢",
    "toxtatilgan":      "🔴",
    "faol":             "🔄",
    "tugadi":           "✅",
}

_PROJ_PER_PAGE = 10


def proj_list_text(projects, page: int = 0) -> str:
    start = page * _PROJ_PER_PAGE
    page_projects = projects[start:start + _PROJ_PER_PAGE]
    total_pages = max(1, (len(projects) + _PROJ_PER_PAGE - 1) // _PROJ_PER_PAGE)

    header = f"📂 <b>Loyihalar ro'yxati</b> — {len(projects)} ta"
    if total_pages > 1:
        header += f"  |  Sahifa {page + 1}/{total_pages}"

    lines = [header, ""]
    for i, p in enumerate(page_projects):
        si = _PROJ_SICON.get(p["proj_status"] or p["status"], "🔄")
        n = start + i + 1
        lines.append(f"{n:>2}. {si}  {p['name']}")

    lines += ["", "<i>Raqamni bosib loyihani oching 👇</i>"]
    return "\n".join(lines)


def project_list_kb(projects, page: int = 0):
    """Raqamli pagination keyboard."""
    start = page * _PROJ_PER_PAGE
    page_projects = projects[start:start + _PROJ_PER_PAGE]
    total_pages = max(1, (len(projects) + _PROJ_PER_PAGE - 1) // _PROJ_PER_PAGE)

    buttons = []
    row = []
    for i, p in enumerate(page_projects):
        row.append(InlineKeyboardButton(str(i + 1), callback_data=f"proj_view:{p['id']}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Oldingi", callback_data=f"proj_page:{page - 1}"))
    if total_pages > 1:
        nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Keyingi ▶️", callback_data=f"proj_page:{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton("➕ Loyiha qo'shish", callback_data="proj_create")])
    buttons.append(menu_button())
    return InlineKeyboardMarkup(buttons)


def project_actions_kb(project_id: int, proj_status: str = ""):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Holat o'zgartirish",    callback_data=f"proj_status_menu:{project_id}")],
        [InlineKeyboardButton("➕ Bosqich qo'shish",      callback_data=f"stage_add:{project_id}")],
        [InlineKeyboardButton("📋 Bosqichlarni ko'rish",  callback_data=f"proj_stages:{project_id}")],
        [InlineKeyboardButton("🗑 Loyihani o'chirish",    callback_data=f"proj_del_confirm:{project_id}")],
        back_button("proj_list"),
    ])


def proj_status_change_kb(project_id: int, current: str = ""):
    statuses = [
        ("rejalashtirilgan", "🔵 Rejalashtirilgan"),
        ("jarayonda",        "🟡 Jarayonda"),
        ("yakunlangan",      "🟢 Yakunlangan"),
        ("toxtatilgan",      "🔴 To'xtatilgan"),
    ]
    buttons = []
    for val, label in statuses:
        mark = " ✅" if val == current else ""
        buttons.append([InlineKeyboardButton(f"{label}{mark}", callback_data=f"proj_setstatus:{project_id}:{val}")])
    buttons.append(back_button(f"proj_view:{project_id}"))
    return InlineKeyboardMarkup(buttons)


def proj_status_kb(current: str = ""):
    statuses = [
        ("rejalashtirilgan", "🔵 Rejalashtirilgan"),
        ("jarayonda",        "🟡 Jarayonda"),
        ("yakunlangan",      "🟢 Yakunlangan"),
        ("toxtatilgan",      "🔴 To'xtatilgan"),
    ]
    buttons = []
    for val, label in statuses:
        mark = " ✅" if val == current else ""
        buttons.append([InlineKeyboardButton(f"{label}{mark}", callback_data=f"projstatus:{val}")])
    return InlineKeyboardMarkup(buttons)


def task_type_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Loyiha bo'yicha vazifa", callback_data="tasktype:project")],
        [InlineKeyboardButton("📋 Erkin vazifa",          callback_data="tasktype:standalone")],
        menu_button(),
    ])


def dep_multiselect_kb(deps, selected_ids: set):
    buttons = []
    for d in deps:
        mark = "✅" if d["id"] in selected_ids else "⬜"
        buttons.append([InlineKeyboardButton(
            f"{mark} {d['emoji']} {d['name']}",
            callback_data=f"dep_toggle:{d['id']}",
        )])
    count = len(selected_ids)
    done_label = f"✅ Tayyor ({count} ta)" if count else "— Hech bo'lim tanlanmagan —"
    buttons.append([InlineKeyboardButton(done_label, callback_data="dep_sel_done")])
    buttons.append(menu_button())
    return InlineKeyboardMarkup(buttons)


def project_select_kb(projects):
    buttons = []
    for p in projects:
        buttons.append([InlineKeyboardButton(
            f"📁 #{p['id']} {p['name'][:35]}",
            callback_data=f"taskproj:{p['id']}",
        )])
    buttons.append(menu_button())
    return InlineKeyboardMarkup(buttons)


def task_dep_view_kb(td_id: int, dep_status: str, task_id: int, user_role: str):
    buttons = []
    if dep_status == "jarayonda":
        if user_role in ("super", "admin"):
            buttons.append([InlineKeyboardButton("👤 Xodim belgilash", callback_data=f"td_assign:{td_id}")])
        if user_role == "super":
            buttons.append([InlineKeyboardButton("✅ Bajarildi (bu bo'lim)", callback_data=f"td_done:{td_id}")])
        else:
            buttons.append([InlineKeyboardButton("✅ Bajarildi", callback_data=f"td_done:{td_id}")])
    buttons.append(back_button(f"task_view:{task_id}"))
    return InlineKeyboardMarkup(buttons)


def stage_list_kb(stages, project_id: int):
    buttons = []
    for s in stages:
        icon = {"wait": "⏳", "active": "🔄", "done": "✅"}.get(s["status"], "❓")
        label = f"{icon} #{s['seq']} {s['description'][:25]}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"stage_view:{s['id']}")])
    buttons.append([InlineKeyboardButton("➕ Bosqich qo'shish", callback_data=f"stage_add:{project_id}")])
    buttons.append(back_button(f"proj_view:{project_id}"))
    return InlineKeyboardMarkup(buttons)


def stage_actions_kb(stage_id: int, status: str, project_id: int):
    buttons = []
    if status == "active":
        buttons.append([InlineKeyboardButton("✅ Bosqich tugadi", callback_data=f"stage_done:{stage_id}")])
    buttons.append([InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"stage_edit:{stage_id}")])
    buttons.append(back_button(f"proj_stages:{project_id}"))
    return InlineKeyboardMarkup(buttons)


# ─────────────────────────── SETTINGS ────────────────────────────

def settings_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Guruhni ulash", callback_data="settings_group")],
        [InlineKeyboardButton("🧵 Topic sozlash", callback_data="topic_settings")],
        [InlineKeyboardButton("💾 Backup (DB)", callback_data="backup_db")],
        menu_button(),
    ])


# ─────────────────────────── TOPIC SETTINGS ──────────────────────────

TOPIC_KEYS = [
    ("topic_elonlar",   "📣 E'lonlar"),
    ("topic_vazifalar", "📋 Vazifalar"),
    ("topic_reja",      "📅 Reja/Deadline"),
    ("topic_hisobotlar","📊 Hisobotlar"),
]


def topic_settings_kb(topics: dict, deps=None):
    buttons = []
    # 4 ta umumiy kanal
    for key, label in TOPIC_KEYS:
        tid = topics.get(key)
        status = f"✅ {tid}" if tid else "❌ —"
        buttons.append([InlineKeyboardButton(
            f"{label}:  {status}",
            callback_data=f"topic_set:{key}",
        )])
    # Bo'limlar
    if deps:
        buttons.append([InlineKeyboardButton("── Bo'limlar ──", callback_data="noop")])
        for dep in deps:
            tid = dep["topic_id"]
            status = f"✅ {tid}" if tid else "❌ —"
            buttons.append([InlineKeyboardButton(
                f"{dep['emoji']} {dep['name']}:  {status}",
                callback_data=f"dep_set_topic:{dep['id']}",
            )])
    buttons.append([InlineKeyboardButton("🔗 Auto yo'riqnoma", callback_data="topic_auto_help")])
    buttons.append(back_button("settings"))
    return InlineKeyboardMarkup(buttons)


# ─────────────────────────── PENDING USERS ───────────────────────────

def pending_list_kb(users):
    buttons = []
    for u in users:
        label = f"👤 {u['name']}"
        if u["username"]:
            label += f" @{u['username']}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"approve_user:{u['id']}")])
    if not users:
        buttons.append([InlineKeyboardButton("— Kutayotganlar yo'q —", callback_data="noop")])
    buttons.append(menu_button())
    return InlineKeyboardMarkup(buttons)


def approve_role_kb(user_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Xodim (worker)", callback_data=f"approve_role:{user_id}:worker")],
        [InlineKeyboardButton("🔑 Mas'ul (admin)", callback_data=f"approve_role:{user_id}:admin")],
        [InlineKeyboardButton("👑 Super Admin", callback_data=f"approve_role:{user_id}:super")],
        [InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_user:{user_id}")],
        back_button("pending_list"),
    ])


def approve_dep_kb(user_id: int, role: str, deps):
    buttons = []
    for d in deps:
        buttons.append([InlineKeyboardButton(
            f"{d['emoji']} {d['name']}",
            callback_data=f"approve_dep:{user_id}:{role}:{d['id']}"
        )])
    buttons.append(back_button(f"approve_user:{user_id}"))
    return InlineKeyboardMarkup(buttons)


# ─────────────────────────── GROUP MEMBERS ───────────────────────────

def group_members_kb(admins_new, db_users):
    buttons = []

    # Qo'shish usullari
    buttons.append([InlineKeyboardButton("🔗 Taklif havolasi yuborish", callback_data="invite_link")])

    # Guruh adminlari — tizimda yo'qlar (qo'shish mumkin)
    if admins_new:
        buttons.append([InlineKeyboardButton("── Guruh adminlari (yangi) ──", callback_data="noop")])
        for admin in admins_new:
            u = admin.user
            name = u.full_name[:22]
            uname = f" @{u.username}" if u.username else ""
            buttons.append([InlineKeyboardButton(f"➕ {name}{uname}", callback_data=f"gm_add:{u.id}")])

    # DB foydalanuvchilari
    if db_users:
        buttons.append([InlineKeyboardButton("── Tizim foydalanuvchilari ──", callback_data="noop")])
        role_icon = {"super": "👑", "admin": "🔑", "worker": "👤"}
        status_icon = {"faol": "✅", "pending": "⏳", "bloklangan": "🚫"}
        for u in db_users:
            si = status_icon.get(u["status"], "❓")
            ri = role_icon.get(u["role"], "👤")
            name = u["name"][:22]
            cb = f"approve_user:{u['id']}" if u["status"] == "pending" else f"user_view:{u['id']}"
            buttons.append([InlineKeyboardButton(f"{si} {ri} {name}", callback_data=cb)])

    buttons.append(menu_button())
    return InlineKeyboardMarkup(buttons)
