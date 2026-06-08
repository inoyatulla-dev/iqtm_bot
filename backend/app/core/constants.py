"""Barcha sobit qiymatlar (Enum) — magic string yo'q.

Ichki qiymatlar ingliz tilida (toza kod, DB), interfeysda o'zbekcha ko'rsatiladi.
"""
from enum import Enum


class Role(str, Enum):
    BOSS = "boss"        # Boshliq (super admin)
    WORKER = "worker"    # Xodim

    @property
    def label(self) -> str:
        return {"boss": "Boshliq", "worker": "Xodim"}[self.value]


class UserStatus(str, Enum):
    ACTIVE = "active"      # Faol
    PENDING = "pending"    # Tasdiq kutmoqda
    BLOCKED = "blocked"    # Bloklangan


class TaskStatus(str, Enum):
    NEW = "new"                 # 🆕 Yangi
    IN_PROGRESS = "in_progress" # 🔄 Jarayonda
    REVIEW = "review"           # 🔍 Tekshiruvda
    DONE = "done"               # ✅ Bajarildi

    @property
    def label(self) -> str:
        return {
            "new": "Yangi",
            "in_progress": "Jarayonda",
            "review": "Tekshiruvda",
            "done": "Bajarildi",
        }[self.value]

    @property
    def emoji(self) -> str:
        return {
            "new": "🆕",
            "in_progress": "🔄",
            "review": "🔍",
            "done": "✅",
        }[self.value]


# Kanban ustunlari tartibi
TASK_STATUS_ORDER = [
    TaskStatus.NEW,
    TaskStatus.IN_PROGRESS,
    TaskStatus.REVIEW,
    TaskStatus.DONE,
]


class TaskType(str, Enum):
    STANDALONE = "standalone"  # Oddiy vazifa
    PERSONAL = "personal"      # Shaxsiy vazifa
    PROJECT = "project"        # Loyiha bosqichi vazifasi


class StageStatus(str, Enum):
    WAIT = "wait"      # ⏳ Kutmoqda
    ACTIVE = "active"  # 🔄 Faol
    DONE = "done"      # ✅ Tugadi


class ProjectStatus(str, Enum):
    ACTIVE = "active"  # Faol
    DONE = "done"      # Tugadi
