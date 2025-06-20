import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_mongodb
from app.schemas.mongo import CookingHistoryDocument, CookingHistoryRequest
from app.services.mongodb_cooking_service import MongoDBCookingService

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter()

def get_cooking_service(mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)) -> MongoDBCookingService:
    """
    MongoDBの料理サービスの依存関係を取得します。
    """
    try:
        return MongoDBCookingService(mongodb=mongodb)
    except Exception as e:
        logger.error(f"MongoDB Cooking Service initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"MongoDB Cooking Service initialization failed: {str(e)}"
        )
    
@router.post("", response_model=CookingHistoryDocument)
async def add_cooking_history(
    input_data: CookingHistoryRequest,
    current_user = Depends(get_current_user),
    service: MongoDBCookingService = Depends(get_cooking_service)
) -> CookingHistoryDocument:
    """
    料理履歴を追加します。
    """
    try:
        history = await service.add_cooking_history(user_id=current_user.id, recipe_id=input_data.recipe_id)
        return history
    except Exception as e:
        logger.error(f"Failed to add cooking history for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add cooking history: {str(e)}"
        )
    
@router.get("/history/{recipe_id}", response_model=List[CookingHistoryDocument])
async def get_cooking_history(
    recipe_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: MongoDBCookingService = Depends(get_cooking_service)
) -> List[CookingHistoryDocument]:
    """
    ユーザーの料理履歴を取得します。
    """
    try:
        history = await service.get_cooking_history(user_id=current_user.id, recipe_id=recipe_id)
        return history
    except Exception as e:
        logger.error(f"Failed to get cooking history for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cooking history: {str(e)}"
        )