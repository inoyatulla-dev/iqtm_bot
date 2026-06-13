"""Markaziy ruxsat tekshiruvi — barcha ruxsat qoidalari shu yerda.

Eski kodda ruxsat har handlerda takrorlanardi; bu yerda bir joyga yig'ilgan.
"""
from app.core.constants import Role, TaskType
from app.models import BoardColumn, Task, User


def is_boss(user: User) -> bool:
    return user.role == Role.BOSS


def is_observer(user: User) -> bool:
    return user.role == Role.OBSERVER


def can_view_dashboard(user: User) -> bool:
    """Monitoring paneli — boshliq va kuzatuvchi ko'ra oladi."""
    return is_boss(user) or is_observer(user)


def can_manage_users(user: User) -> bool:
    """Xodim/bo'lim/sozlama CRUD — faqat boshliq."""
    return is_boss(user)


def can_create_task(user: User) -> bool:
    """Vazifa berish — faqat boshliq (xodim faqat shaxsiy vazifa qo'shadi)."""
    return is_boss(user)


def can_create_personal_task(user: User) -> bool:
    """Shaxsiy vazifa qo'shish — kuzatuvchi faqat ko'radi, qo'sha olmaydi."""
    return not is_observer(user)


def can_view_task(user: User, task: Task) -> bool:
    if is_boss(user) or is_observer(user):
        return True
    # Xodim: o'ziga tegishli yoki o'zi yaratgan
    return task.masul_id == user.id or task.created_by == user.id


def can_edit_task(user: User, task: Task) -> bool:
    """Vazifa mazmunini (nom, tavsif, muddat, mas'ul) tahrirlash."""
    if is_observer(user):
        return False
    if is_boss(user):
        return True
    # Xodim faqat o'zining shaxsiy vazifasini tahrirlaydi
    return task.type == TaskType.PERSONAL and task.created_by == user.id


def can_change_status(user: User, task: Task, target_column: BoardColumn) -> bool:
    """Doskada holatni o'zgartirish (sudrab/menyudan) — boshliq yoki mas'ul xodim.

    "Yakuniy" (is_done) ustunga faqat boshliq o'tkaza oladi — ish tekshirib
    tasdiqlangandan keyin "Bajarildi"ga o'tadi.
    """
    if is_observer(user):
        return False
    if is_boss(user):
        return True
    if target_column.is_done:
        return False
    return task.masul_id == user.id or (
        task.type == TaskType.PERSONAL and task.created_by == user.id
    )


def can_delete_task(user: User, task: Task) -> bool:
    if is_observer(user):
        return False
    if is_boss(user):
        return True
    return task.type == TaskType.PERSONAL and task.created_by == user.id
