"""Barcha modellar shu yerdan import qilinadi (Alembic va metadata uchun)."""
from app.models.attachment import Attachment
from app.models.board_column import BoardColumn
from app.models.comment import Comment
from app.models.department import Department
from app.models.misc import Log, Reminder, Setting
from app.models.notification import Notification
from app.models.project import Project, ProjectStage
from app.models.task import Task
from app.models.task_assignee import TaskAssignee
from app.models.topic import Topic
from app.models.user import User

__all__ = [
    "User",
    "Department",
    "Task",
    "TaskAssignee",
    "BoardColumn",
    "Comment",
    "Attachment",
    "Project",
    "ProjectStage",
    "Reminder",
    "Log",
    "Setting",
    "Topic",
    "Notification",
]
