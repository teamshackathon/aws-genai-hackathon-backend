from fastapi import APIRouter

from .endpoints import auth, blob, healthcheck, recipes, shopping, user, ws

api_router = APIRouter()

# Include the healthcheck router
api_router.include_router(
    healthcheck.router,
    prefix="/healthcheck",
    tags=["healthcheck"]
)

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(recipes.router, prefix="/recipes", tags=["recipes"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])
api_router.include_router(shopping.router, prefix="/shopping-lists", tags=["shopping"])
api_router.include_router(blob.router, prefix="/blob", tags=["blob"])
