import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.mongo import CookingHistoryDocument, SessionDocument, SessionHistoryDocument, SessionHistoryMessage


class MongoDBRecipeGenerationService:

    def __init__(self, mongodb: AsyncIOMotorDatabase):
        self.mongodb = mongodb
        self.sessions_collection = mongodb["sessions"]
        self.history_collection = mongodb["session_history"]

    async def create_session(self, user_id: Optional[int] = None) -> SessionDocument:
        """新しいセッションを作成"""
        session_id = str(uuid.uuid4())
        session_doc = SessionDocument(
            session_id=session_id,
            user_id=user_id,
            status="active"
        )
        
        # sessionsコレクションに挿入
        result = await self.sessions_collection.insert_one(session_doc.dict(by_alias=True))
        session_doc.id = result.inserted_id
        
        # session_historyコレクションも初期化
        history_doc = SessionHistoryDocument(session_id=session_id, user_id=user_id)
        await self.history_collection.insert_one(history_doc.dict(by_alias=True))
        
        return session_doc
    
    async def get_session(self, session_id: str) -> Optional[SessionDocument]:
        """セッションを取得"""
        doc = await self.sessions_collection.find_one({"session_id": session_id})
        return SessionDocument(**doc) if doc else None
    
    async def update_session(
        self, 
        session_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[SessionDocument]:
        """セッションを更新"""
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
        
        if result.modified_count > 0:
            return await self.get_session(session_id)
        return None
    
    async def update_session_status(
        self, 
        session_id: str, 
        status: str
    ) -> Optional[SessionDocument]:
        """セッションステータスを更新"""
        update_data = {"status": status}
        if status in ["completed", "failed", "cancelled"]:
            update_data["completed_at"] = datetime.utcnow()
        
        return await self.update_session(session_id, update_data)
    
    async def add_message_to_history(
        self, 
        session_id: str, 
        message_type: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """セッション履歴にメッセージを追加"""
        message_id = str(uuid.uuid4())
        message = SessionHistoryMessage(
            message_id=message_id,
            message_type=message_type,
            content=content,
            metadata=metadata or {}
        )
        
        # session_historyコレクションにメッセージを追加
        await self.history_collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": message.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            },
            upsert=True  # ドキュメントが存在しない場合は作成
        )
        
        return message_id
    
    async def get_session_history(self, session_id: str) -> Optional[SessionHistoryDocument]:
        """セッション履歴を取得"""
        doc = await self.history_collection.find_one({"session_id": session_id})
        return SessionHistoryDocument(**doc) if doc else None
    
    async def get_user_session_history(
        self, 
        user_id: int,
    ) -> List[SessionHistoryDocument]:
        """ユーザーのセッション履歴をすべて取得"""
        docs = await self.history_collection.find(
            {"user_id": user_id}
        ).to_list(length=None)
        return [SessionHistoryDocument(**doc) for doc in docs]
    
    async def get_session_messages(self, session_id: str) -> List[SessionHistoryMessage]:
        """セッションのメッセージリストを取得"""
        history = await self.get_session_history(session_id)
        return history.messages if history else []
    
    async def delete_session(self, session_id: str) -> bool:
        """セッションと履歴を削除"""
        # セッションを削除
        session_result = await self.sessions_collection.delete_one({"session_id": session_id})
        # 履歴を削除
        # history_result = await self.history_collection.delete_one({"session_id": session_id})
        
        return session_result.deleted_count > 0
    
    async def get_user_sessions(
        self, 
        user_id: int, 
        status: Optional[str] = None
    ) -> SessionDocument:
        """ユーザーのセッションを取得"""
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        # 一つのセッションを取得
        doc = await self.sessions_collection.find_one(query)
        return SessionDocument(**doc) if doc else None
    
class MongoDBCookingService:

    def __init__(self, mongodb: AsyncIOMotorDatabase):
        self.mongodb = mongodb
        self.recipes_collection = mongodb["cooking_history"]

    async def add_cooking_history(
        self, 
        user_id: int, 
        recipe_id: str, 
    ) -> CookingHistoryDocument:
        """料理履歴を追加"""
        history_id = str(uuid.uuid4())
        cooking_history_doc = CookingHistoryDocument(
            history_id=history_id,
            user_id=user_id,
            recipe_id=recipe_id,
            created_at=datetime.utcnow()
        )
        
        result = await self.recipes_collection.insert_one(cooking_history_doc)
        return CookingHistoryDocument(**result.inserted_id, **cooking_history_doc.dict(by_alias=True))
    
    async def get_cooking_history(
        self, 
        user_id: int, 
    ) -> List[CookingHistoryDocument]:
        """ユーザーの料理履歴を取得"""
        docs = await self.recipes_collection.find({"user_id": user_id}).to_list(length=None)
        return [CookingHistoryDocument(**doc) for doc in docs]
