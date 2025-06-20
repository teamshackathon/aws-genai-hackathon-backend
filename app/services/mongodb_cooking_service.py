import logging
from datetime import datetime
from typing import List

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.mongo import CookingHistoryDocument

logger = logging.getLogger(__name__)

class MongoDBCookingService:

    def __init__(self, mongodb: AsyncIOMotorDatabase):
        self.mongodb = mongodb
        self.recipes_collection = mongodb["cooking_history"]

    async def add_cooking_history(
        self, 
        user_id: int, 
        recipe_id: int, 
    ) -> CookingHistoryDocument:
        """料理履歴を追加"""
        cooking_history_doc = CookingHistoryDocument(
            user_id=user_id,
            recipe_id=recipe_id,
            created_at=datetime.utcnow()
        )
        
        result = await self.recipes_collection.insert_one(cooking_history_doc.dict(by_alias=True))
        logger.info(f"Cooking history added with ID: {result.inserted_id}")
        return cooking_history_doc
    
    async def get_cooking_history(
        self, 
        user_id: int, 
        recipe_id: int
    ) -> List[CookingHistoryDocument]:
        """ユーザーの料理履歴を取得"""
        logger.info(f"Fetching cooking history for user_id: {user_id}, recipe_id: {recipe_id}")
        docs = await self.recipes_collection.find(
            {"recipe_id": int(recipe_id), "user_id": user_id}
        ).to_list(length=None)
        return [CookingHistoryDocument(**doc) for doc in docs]