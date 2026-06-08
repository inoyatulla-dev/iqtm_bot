import aiosqlite
import os
from datetime import datetime

DB_PATH = "bot.db"


async def get_db():
    return await aiosqlite.connect(DB_PATH)


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:  # noqa: F841 (shadowed name)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                username TEXT,
                role TEXT NOT NULL DEFAULT 'worker',
                dep_id TEXT,
                status TEXT NOT NULL DEFAULT 'faol',
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                emoji TEXT NOT NULL DEFAULT '🏢',
                admin_id INTEGER,
                topic_id INTEGER,
                FOREIGN KEY (admin_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                dep_id TEXT NOT NULL,
                masul_id INTEGER,
                created_by INTEGER NOT NULL,
                deadline TEXT,
                status TEXT NOT NULL DEFAULT 'faol',
                project_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (dep_id) REFERENCES departments(id),
                FOREIGN KEY (masul_id) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'faol',
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS project_stages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                seq INTEGER NOT NULL DEFAULT 1,
                dep_id TEXT NOT NULL,
                description TEXT NOT NULL,
                masul_id INTEGER,
                deadline TEXT,
                status TEXT NOT NULL DEFAULT 'wait',
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (dep_id) REFERENCES departments(id),
                FOREIGN KEY (masul_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                remind_at TEXT NOT NULL,
                sent INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS task_deps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                dep_id TEXT NOT NULL,
                work_desc TEXT,
                worker_id INTEGER,
                status TEXT NOT NULL DEFAULT 'jarayonda',
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (dep_id) REFERENCES departments(id),
                FOREIGN KEY (worker_id) REFERENCES users(id)
            )
        """)
        await db.commit()

        # Migration: hidden ustunlarini qo'shish (agar mavjud bo'lmasa)
        for stmt in [
            "ALTER TABLE users      ADD COLUMN hidden INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE departments ADD COLUMN hidden INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE tasks       ADD COLUMN hidden INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE projects    ADD COLUMN hidden INTEGER NOT NULL DEFAULT 0",
        ]:
            try:
                await db.execute(stmt)
                await db.commit()
            except Exception:
                pass  # ustun allaqachon mavjud

        for stmt in [
            "ALTER TABLE projects ADD COLUMN description TEXT",
            "ALTER TABLE projects ADD COLUMN proj_status TEXT NOT NULL DEFAULT 'rejalashtirilgan'",
            "ALTER TABLE tasks ADD COLUMN type TEXT NOT NULL DEFAULT 'standalone'",
            "ALTER TABLE tasks ADD COLUMN is_locked INTEGER NOT NULL DEFAULT 0",
        ]:
            try:
                await db.execute(stmt)
                await db.commit()
            except Exception:
                pass


async def seed_data():
    """Boshlang'ich ma'lumotlar (departments va owner)."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Bo'limlar
        deps = [
            ("el", "Elektronika", "🔌"),
            ("ds", "Dasturlash", "💻"),
            ("kn", "Konstruktor", "📐"),
            ("us", "Ustaxona", "🔧"),
            ("bo", "Bo'yash", "🎨"),
        ]
        for dep_id, name, emoji in deps:
            await db.execute(
                "INSERT OR IGNORE INTO departments (id, name, emoji) VALUES (?, ?, ?)",
                (dep_id, name, emoji),
            )

        # Owner
        try:
            owner_id = int(os.getenv("OWNER_ID", "0"))
        except (ValueError, TypeError):
            owner_id = 0
        if owner_id:
            now = datetime.now().isoformat()
            await db.execute(
                """INSERT OR IGNORE INTO users (id, name, username, role, status, created_at)
                   VALUES (?, ?, ?, 'super', 'faol', ?)""",
                (owner_id, "Super Admin", "", now),
            )
        await db.commit()


# ─────────────────────────── USERS ────────────────────────────

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id=? AND hidden=0", (user_id,)) as cur:
            return await cur.fetchone()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE hidden=0 ORDER BY name") as cur:
            return await cur.fetchall()


async def get_users_by_dep(dep_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE dep_id=? AND hidden=0 ORDER BY name", (dep_id,)
        ) as cur:
            return await cur.fetchall()


async def create_user(user_id: int, name: str, username: str, role: str, dep_id=None):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO users (id, name, username, role, dep_id, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'faol', ?)""",
            (user_id, name, username, role, dep_id, now),
        )
        await db.commit()


async def update_user(user_id: int, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE users SET {fields} WHERE id=?", values)
        await db.commit()


async def delete_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET hidden=1 WHERE id=?", (user_id,))
        await db.commit()


# ─────────────────────────── SETTINGS ────────────────────────────

async def get_setting(key: str, default=None):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key=?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else default


async def save_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        await db.commit()


# ─────────────────────────── PENDING / ROLE HELPERS ───────────────

async def get_users_by_role(role: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE role=? AND status='faol' AND hidden=0", (role,)
        ) as cur:
            return await cur.fetchall()


async def get_pending_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE status='pending' AND hidden=0 ORDER BY created_at DESC"
        ) as cur:
            return await cur.fetchall()


async def update_department_admin_clear(user_id: int):
    """Bu user boshqa bo'limning admin_id bo'lsa, uni tozalash."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE departments SET admin_id=NULL WHERE admin_id=?", (user_id,)
        )
        await db.commit()


async def count_supers():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE role='super'") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


# ─────────────────────────── DEPARTMENTS ────────────────────────────

async def get_all_departments():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM departments WHERE hidden=0 ORDER BY id") as cur:
            return await cur.fetchall()


async def get_department(dep_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM departments WHERE id=? AND hidden=0", (dep_id,)) as cur:
            return await cur.fetchone()


async def create_department(dep_id: str, name: str, emoji: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO departments (id, name, emoji) VALUES (?, ?, ?)",
            (dep_id, name, emoji),
        )
        await db.commit()


async def update_department(dep_id: str, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [dep_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE departments SET {fields} WHERE id=?", values)
        await db.commit()


async def delete_department(dep_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE departments SET hidden=1 WHERE id=?", (dep_id,))
        await db.commit()


async def dep_has_users(dep_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE dep_id=?", (dep_id,)
        ) as cur:
            row = await cur.fetchone()
            return (row[0] if row else 0) > 0


# ─────────────────────────── TASKS ────────────────────────────

async def get_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tasks WHERE id=? AND hidden=0", (task_id,)) as cur:
            return await cur.fetchone()


async def get_tasks_by_dep(dep_id: str):
    """Bo'limga biriktirilgan barcha vazifalar (to'g'ridan-to'g'ri va ko'p bo'limli)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # To'g'ridan-to'g'ri biriktirilgan (shaxsiy vazifalar ko'rsatilmaydi)
        async with db.execute(
            "SELECT * FROM tasks WHERE dep_id=? AND (type IS NULL OR type!='personal') AND hidden=0 ORDER BY created_at DESC",
            (dep_id,)
        ) as cur:
            direct = await cur.fetchall()
        # Ko'p bo'limli (task_deps orqali)
        async with db.execute(
            """SELECT DISTINCT t.* FROM tasks t
               JOIN task_deps td ON t.id = td.task_id
               WHERE td.dep_id=? AND t.dep_id='multi' AND t.hidden=0
               ORDER BY t.created_at DESC""",
            (dep_id,)
        ) as cur:
            multi = await cur.fetchall()
        seen = {r["id"] for r in direct}
        return list(direct) + [r for r in multi if r["id"] not in seen]


async def get_tasks_by_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tasks WHERE masul_id=? AND hidden=0 ORDER BY created_at DESC", (user_id,)
        ) as cur:
            return await cur.fetchall()


async def get_all_tasks():
    """Barcha vazifalar — shaxsiy vazifalar ko'rsatilmaydi."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tasks WHERE hidden=0 AND (type IS NULL OR type!='personal') ORDER BY created_at DESC"
        ) as cur:
            return await cur.fetchall()


async def create_task(
    name: str, description: str, dep_id: str, masul_id, created_by: int,
    deadline: str, project_id=None, task_type: str = "standalone"
):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO tasks (name, description, dep_id, masul_id, created_by, deadline, status, project_id, type, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'faol', ?, ?, ?)""",
            (name, description, dep_id, masul_id, created_by, deadline, project_id, task_type, now),
        )
        await db.commit()
        return cur.lastrowid


async def update_task(task_id: int, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [task_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE tasks SET {fields} WHERE id=?", values)
        await db.commit()


async def delete_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE tasks SET hidden=1 WHERE id=?", (task_id,))
        await db.commit()


async def get_overdue_tasks():
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tasks WHERE status='faol' AND hidden=0 AND deadline < ?", (now,)
        ) as cur:
            return await cur.fetchall()


# ─────────────────────────── PROJECTS ────────────────────────────

async def get_all_projects():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM projects WHERE hidden=0 ORDER BY created_at DESC") as cur:
            return await cur.fetchall()


async def get_project(project_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM projects WHERE id=? AND hidden=0", (project_id,)) as cur:
            return await cur.fetchone()


async def create_project(name: str, created_by: int, description: str = "", proj_status: str = "rejalashtirilgan"):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO projects (name, description, proj_status, status, created_by, created_at) VALUES (?, ?, ?, 'faol', ?, ?)",
            (name, description, proj_status, created_by, now),
        )
        await db.commit()
        return cur.lastrowid


async def update_project(project_id: int, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [project_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE projects SET {fields} WHERE id=?", values)
        await db.commit()


async def delete_project(project_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE projects SET hidden=1 WHERE id=?", (project_id,))
        await db.commit()


# ─────────────────────────── TASK DEPS (ko'p bo'limli vazifalar) ──────────────

async def create_task_dep(task_id: int, dep_id: str, work_desc: str = "", worker_id=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO task_deps (task_id, dep_id, work_desc, worker_id) VALUES (?, ?, ?, ?)",
            (task_id, dep_id, work_desc, worker_id),
        )
        await db.commit()


async def get_task_deps(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM task_deps WHERE task_id=?", (task_id,)
        ) as cur:
            return await cur.fetchall()


async def get_task_dep(td_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM task_deps WHERE id=?", (td_id,)) as cur:
            return await cur.fetchone()


async def get_task_dep_for_dep(task_id: int, dep_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM task_deps WHERE task_id=? AND dep_id=?", (task_id, dep_id)
        ) as cur:
            return await cur.fetchone()


async def update_task_dep(td_id: int, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [td_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE task_deps SET {fields} WHERE id=?", values)
        await db.commit()


async def get_multidep_tasks_for_dep(dep_id: str):
    """Ko'p bo'limli vazifalar ichida ushbu bo'limga tegishlilari."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT t.* FROM tasks t
               JOIN task_deps td ON t.id = td.task_id
               WHERE td.dep_id=? AND t.hidden=0
               ORDER BY t.created_at DESC""",
            (dep_id,)
        ) as cur:
            return await cur.fetchall()


# ─────────────────────────── PROJECT STAGES ────────────────────────────

async def get_stages_by_project(project_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM project_stages WHERE project_id=? ORDER BY seq, id",
            (project_id,),
        ) as cur:
            return await cur.fetchall()


async def get_stage(stage_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM project_stages WHERE id=?", (stage_id,)) as cur:
            return await cur.fetchone()


async def create_stage(project_id: int, seq: int, dep_id: str, description: str, masul_id, deadline: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO project_stages (project_id, seq, dep_id, description, masul_id, deadline, status)
               VALUES (?, ?, ?, ?, ?, ?, 'wait')""",
            (project_id, seq, dep_id, description, masul_id, deadline),
        )
        await db.commit()
        return cur.lastrowid


async def update_stage(stage_id: int, **kwargs):
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [stage_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE project_stages SET {fields} WHERE id=?", values)
        await db.commit()


async def activate_first_stages(project_id: int):
    """Loyiha yaratilganda 1-navbat bosqichlarini faollashtirish."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT MIN(seq) FROM project_stages WHERE project_id=?", (project_id,)
        ) as cur:
            row = await cur.fetchone()
            if not row or row[0] is None:
                return
            min_seq = row[0]
        await db.execute(
            "UPDATE project_stages SET status='active' WHERE project_id=? AND seq=?",
            (project_id, min_seq),
        )
        await db.commit()


async def advance_project_stages(project_id: int) -> list:
    """
    Bosqich 'done' bo'lganda keyingisini faollashtirish.
    Qaytaradi: yangi active bo'lgan bosqichlar ro'yxati.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Hali tugamagan bosqichlar bormi?
        async with db.execute(
            "SELECT * FROM project_stages WHERE project_id=? AND status != 'done' ORDER BY seq",
            (project_id,),
        ) as cur:
            remaining = await cur.fetchall()

        if not remaining:
            await db.execute("UPDATE projects SET status='tugadi' WHERE id=?", (project_id,))
            await db.commit()
            return []

        # Hozirgi aktiv navbat seq
        async with db.execute(
            "SELECT MIN(seq) FROM project_stages WHERE project_id=? AND status='active'",
            (project_id,),
        ) as cur:
            row = await cur.fetchone()
            if row and row[0]:
                current_seq = row[0]
            else:
                current_seq = None

        if current_seq is None:
            return []

        # current_seq dagi barcha bosqichlar done?
        async with db.execute(
            "SELECT COUNT(*) FROM project_stages WHERE project_id=? AND seq=? AND status!='done'",
            (project_id, current_seq),
        ) as cur:
            row = await cur.fetchone()
            if row and row[0] > 0:
                return []  # hali tugamagan bor

        # Keyingi navbat
        async with db.execute(
            "SELECT MIN(seq) FROM project_stages WHERE project_id=? AND seq>? AND status='wait'",
            (project_id, current_seq),
        ) as cur:
            row = await cur.fetchone()
            if not row or row[0] is None:
                # Hammasi tugadi
                await db.execute("UPDATE projects SET status='tugadi' WHERE id=?", (project_id,))
                await db.commit()
                return []
            next_seq = row[0]

        await db.execute(
            "UPDATE project_stages SET status='active' WHERE project_id=? AND seq=?",
            (project_id, next_seq),
        )
        await db.commit()

        async with db.execute(
            "SELECT * FROM project_stages WHERE project_id=? AND seq=?",
            (project_id, next_seq),
        ) as cur:
            return await cur.fetchall()


# ─────────────────────────── REMINDERS ────────────────────────────

async def create_reminder(task_id: int, remind_at: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reminders (task_id, remind_at, sent) VALUES (?, ?, 0)",
            (task_id, remind_at),
        )
        await db.commit()


async def get_pending_reminders():
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reminders WHERE sent=0 AND remind_at <= ?", (now,)
        ) as cur:
            return await cur.fetchall()


async def mark_reminder_sent(reminder_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE reminders SET sent=1 WHERE id=?", (reminder_id,))
        await db.commit()


# ─────────────────────────── LOGS ────────────────────────────

async def add_log(user_id: int, action: str):
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO logs (user_id, action, created_at) VALUES (?, ?, ?)",
            (user_id, action, now),
        )
        await db.commit()


# ─────────────────────────── STATS ────────────────────────────

async def get_stats_global():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        result = {}
        async with db.execute("SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status") as cur:
            rows = await cur.fetchall()
            result["tasks"] = {r["status"]: r["cnt"] for r in rows}
        async with db.execute("SELECT COUNT(*) as cnt FROM users WHERE status='faol'") as cur:
            row = await cur.fetchone()
            result["users"] = row["cnt"] if row else 0
        async with db.execute("SELECT COUNT(*) as cnt FROM projects WHERE status='faol'") as cur:
            row = await cur.fetchone()
            result["projects"] = row["cnt"] if row else 0
        return result


async def get_stats_by_dep(dep_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        result = {}
        async with db.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks WHERE dep_id=? GROUP BY status", (dep_id,)
        ) as cur:
            rows = await cur.fetchall()
            result["tasks"] = {r["status"]: r["cnt"] for r in rows}
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE dep_id=? AND status='faol'", (dep_id,)
        ) as cur:
            row = await cur.fetchone()
            result["users"] = row["cnt"] if row else 0
        return result


async def get_stats_by_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks WHERE masul_id=? GROUP BY status", (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return {r["status"]: r["cnt"] for r in rows}


async def get_rating(dep_id: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if dep_id:
            async with db.execute(
                """SELECT u.id, u.name, u.username,
                       SUM(CASE WHEN t.status='bajarildi' THEN 1 ELSE 0 END) as done,
                       SUM(CASE WHEN t.status='faol' THEN 1 ELSE 0 END) as active,
                       SUM(CASE WHEN t.status='kechikdi' THEN 1 ELSE 0 END) as late
                   FROM users u
                   LEFT JOIN tasks t ON t.masul_id = u.id
                   WHERE u.dep_id=? AND u.status='faol'
                   GROUP BY u.id ORDER BY done DESC""",
                (dep_id,),
            ) as cur:
                return await cur.fetchall()
        else:
            async with db.execute(
                """SELECT u.id, u.name, u.username,
                       SUM(CASE WHEN t.status='bajarildi' THEN 1 ELSE 0 END) as done,
                       SUM(CASE WHEN t.status='faol' THEN 1 ELSE 0 END) as active,
                       SUM(CASE WHEN t.status='kechikdi' THEN 1 ELSE 0 END) as late
                   FROM users u
                   LEFT JOIN tasks t ON t.masul_id = u.id
                   WHERE u.status='faol'
                   GROUP BY u.id ORDER BY done DESC"""
            ) as cur:
                return await cur.fetchall()
