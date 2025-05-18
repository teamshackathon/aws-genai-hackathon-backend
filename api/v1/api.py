from fastapi import APIRouter
from .endpoints import healthcheck

api_router = APIRouter()

# Include the healthcheck router
api_router.include_router(
    healthcheck.router,
    prefix="/healthcheck",
    tags=["healthcheck"]
)