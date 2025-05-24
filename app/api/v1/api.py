from fastapi import APIRouter

from .endpoints import healthcheck, users

api_router = APIRouter()

# Include the healthcheck router
api_router.include_router(
    healthcheck.router,
    prefix="/healthcheck",
    tags=["healthcheck"]
)

api_router.include_router(users.router, prefix="/users", tags=["users"])