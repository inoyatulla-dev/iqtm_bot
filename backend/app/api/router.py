"""Barcha routerlarni /api ostida birlashtiradi."""
from fastapi import APIRouter

from app.api.routers import auth, departments, settings, stats, tasks, users

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(tasks.router)
api_router.include_router(users.router)
api_router.include_router(departments.router)
api_router.include_router(stats.router)
api_router.include_router(settings.router)
