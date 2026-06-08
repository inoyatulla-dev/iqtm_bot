"""Barcha modellar shu yerdan import qilinadi (Alembic va metadata uchun)."""
from app.models.department import Department
from app.models.misc import Log, Reminder, Setting
from app.models.project import Project, ProjectStage
from app.models.task import Task
from app.models.user import User

__all__ = [
    "User",
    "Department",
    "Task",
    "Project",
    "ProjectStage",
    "Reminder",
    "Log",
    "Setting",
]
