from fastapi import APIRouter

from .handlers.health import router as health_router
from .handlers.pull_requests import router as pr_router
from .handlers.teams import router as teams_router
from .handlers.users import router as users_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(teams_router)
api_router.include_router(users_router)
api_router.include_router(pr_router)