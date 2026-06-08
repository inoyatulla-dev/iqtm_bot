"""Markaziy ruxsat tekshiruvi — barcha ruxsat qoidalari shu yerda.

Eski kodda ruxsat har handlerda takrorlanardi; bu yerda bir joyga yig'ilgan.
"""
from app.core.constants import Role, TaskType
from app.models import Task, User


def is_boss(user: User) -> bool:
    return user.role == Role.BOSS


def can_manage_users(user: User) -> bool:
    """Xodim/bo'lim/sozlama CRUD — faqat boshliq."""
    return is_boss(user)


def can_create_task(user: User) -> bool:
    """Vazifa berish — faqat boshliq (xodim faqat shaxsiy vazifa qo'shadi)."""
    return is_boss(user)


def can_view_task(user: User, task: Task) -> bool:
    if is_boss(user):
        return True
    # Xodim: o'ziga tegishli yoki o'zi yaratgan
    return task.masul_id == user.id or task.created_by == user.id


def can_edit_task(user: User, task: Task) -> bool:
    """Vazifa mazmunini (nom, tavsif, muddat, mas'ul) tahrirlash."""
    if is_boss(user):
        return True
    # Xodim faqat o'zining shaxsiy vazifasini tahrirlaydi
    return task.type == TaskType.PERSONAL and task.created_by == user.id


def can_change_status(user: User, task: Task) -> bool:
    """Doskada holatni o'zgartirish (sudrab) — boshliq yoki mas'ul xodim."""
    if is_boss(user):
        return True
    return task.masul_id == user.id or (
        task.type == TaskType.PERSONAL and task.created_by == user.id
    )


def can_delete_task(user: User, task: Task) -> bool:
    if is_boss(user):
        return True
    return task.type == TaskType.PERSONAL and task.created_by == user.id
