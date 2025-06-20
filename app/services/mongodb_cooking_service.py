import logging
import uuid
from datetime import datetime
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.mongo import CookingHistoryDocument, SessionDocument

logger = logging.getLogger(__name__)

class MongoDBCookingService:

    def __init__(self, mongodb: AsyncIOMotorDatabase):
        self.mongodb = mongodb
        self.cooking_history_collection = mongodb["cooking_history"]
        self.cooking_sessions_collection = mongodb["cooking_sessions"]

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
        
        result = await self.cooking_history_collection.insert_one(cooking_history_doc.dict(by_alias=True))
        logger.info(f"Cooking history added with ID: {result.inserted_id}")
        return cooking_history_doc
    
    async def get_cooking_history(
        self, 
        user_id: int, 
        recipe_id: int
    ) -> List[CookingHistoryDocument]:
        """ユーザーの料理履歴を取得"""
        logger.info(f"Fetching cooking history for user_id: {user_id}, recipe_id: {recipe_id}")
        docs = await self.cooking_history_collection.find(
            {"recipe_id": int(recipe_id), "user_id": user_id}
        ).to_list(length=None)
        return [CookingHistoryDocument(**doc) for doc in docs]

    async def create_session(self, user_id: Optional[int] = None) -> SessionDocument:
        """新しいセッションを作成"""
        session_id = str(uuid.uuid4())
        session_doc = SessionDocument(
            session_id=session_id,
            user_id=user_id,
            status="active"
        )
        
        # sessionsコレクションに挿入
        result = await self.cooking_sessions_collection.insert_one(session_doc.dict(by_alias=True))
        session_doc.id = result.inserted_id

        logger.info(f"Session created with ID: {session_doc.session_id}")
        return session_doc
    
    async def delete_session(self, session_id: str) -> bool:
        """セッションと履歴を削除"""
        # セッションを削除
        session_result = await self.cooking_sessions_collection.delete_one({"session_id": session_id})
        # 履歴を削除
        # history_result = await self.history_collection.delete_one({"session_id": session_id})
        
        return session_result.deleted_count > 0