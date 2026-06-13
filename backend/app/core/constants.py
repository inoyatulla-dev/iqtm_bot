"""Barcha sobit qiymatlar (Enum) — magic string yo'q.

Ichki qiymatlar ingliz tilida (toza kod, DB), interfeysda o'zbekcha ko'rsatiladi.
"""
from enum import Enum


class Role(str, Enum):
    BOSS = "boss"          # Boshliq (super admin)
    WORKER = "worker"      # Xodim
    OBSERVER = "observer"  # Kuzatuvchi (faqat ko'rish)

    @property
    def label(self) -> str:
        return {"boss": "Admin", "worker": "Xodim", "observer": "Kuzatuvchi"}[self.value]


class UserStatus(str, Enum):
    ACTIVE = "active"      # Faol
    PENDING = "pending"    # Tasdiq kutmoqda
    BLOCKED = "blocked"    # Bloklangan


# Vazifa holati endi qattiq enum emas — BoardColumn jadvalida saqlanadi
# (admin ustunlarni o'zi qo'shadi/nomlaydi/tartiblaydi). Qarang: app.models.board_column


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
