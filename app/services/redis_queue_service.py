import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)

class RedisQueueService:

    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client
        self.queue_name = "recipe_generation_queue"

    async def enqueue_recipe_generation_task(
        self, 
        session_id: str, 
        url: str, 
        user_id: int,
        priority: int = 1
    ) -> str:
        """レシピ生成タスクをキューに追加"""
        try:
            task_data = {
                "task_id": f"recipe_gen_{session_id}_{datetime.utcnow().timestamp()}",
                "session_id": session_id,
                "url": url,
                "user_id": user_id,
                "priority": priority,
                "created_at": datetime.utcnow().isoformat(),
                "status": "queued"
            }
            
            # タスクをキューに追加
            task_json = json.dumps(task_data)
            await self.redis_client.lpush(self.queue_name, task_json)
            
            # タスク情報を保存（追跡用）
            task_key = f"task:{task_data['task_id']}"
            await self.redis_client.hset(task_key, mapping=task_data)
            await self.redis_client.expire(task_key, 3600)  # 1時間で期限切れ
            
            logger.info(f"Task enqueued: {task_data['task_id']} for session: {session_id}")
            return task_data['task_id']
            
        except Exception as e:
            logger.error(f"Error enqueuing task: {str(e)}")
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """タスクの状態を取得"""
        try:
            task_key = f"task:{task_id}"
            task_data = await self.redis_client.hgetall(task_key)
            return task_data if task_data else None
        except Exception as e:
            logger.error(f"Error getting task status: {str(e)}")
            return None
    
    async def update_task_status(self, task_id: str, status: str, result: Optional[Dict] = None):
        """タスクの状態を更新"""
        try:
            task_key = f"task:{task_id}"
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if result:
                update_data["result"] = json.dumps(result)
            
            await self.redis_client.hset(task_key, mapping=update_data)
            logger.info(f"Task status updated: {task_id} -> {status}")
            
        except Exception as e:
            logger.error(f"Error updating task status: {str(e)}")