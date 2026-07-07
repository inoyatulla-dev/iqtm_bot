"""Barcha routerlarni /api ostida birlashtiradi."""
from fastapi import APIRouter

from app.api.routers import (
    auth,
    board_columns,
    departments,
    notifications,
    projects,
    reports,
    settings,
    stats,
    tasks,
    topics,
    users,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(tasks.router)
api_router.include_router(notifications.router)
api_router.include_router(users.router)
api_router.include_router(departments.router)
api_router.include_router(board_columns.router)
api_router.include_router(projects.router)
api_router.include_router(stats.router)
api_router.include_router(settings.router)
api_router.include_router(topics.router)
api_router.include_router(reports.router)
