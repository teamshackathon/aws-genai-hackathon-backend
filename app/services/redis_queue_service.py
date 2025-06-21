import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from celery import Celery
from celery.result import AsyncResult
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisQueueService:
    """Redis-based queue service using Celery for recipe generation tasks"""

    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client
        self.queue_name = "recipe_gen_queue"

        # Initialize Celery client
        self.celery_app = Celery("bae-recipe-client", broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0", backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0")

        # Configure Celery
        self.celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            result_expires=3600,
        )

    async def enqueue_recipe_generation_task(self, session_id: str, url: str, user_id: int, recipe_params: Optional[dict] = None, priority: int = 1) -> str:
        """Send recipe generation task to Celery queue"""
        try:  # Generate task metadata
            task_metadata = {
                "session_id": session_id,
                "url": url,
                "user_id": user_id,
                "recipe_params": recipe_params,
                "priority": priority,
                "created_at": datetime.utcnow().isoformat(),
                "status": "queued",
            }

            logger.info(f"Enqueuing recipe generation task with params: {recipe_params}")

            # Send task to Celery worker
            celery_result = self.celery_app.send_task(
                "tasks.queue_processor.process_recipe_generation_task",
                args=[session_id, url, user_id],
                kwargs={"metadata": task_metadata},
                queue=self.queue_name,
                priority=priority,
            )

            # Store task information in Redis for tracking
            task_key = f"task:{celery_result.id}"
            task_data = {
                **task_metadata,
                "task_id": celery_result.id,
                "celery_task_id": celery_result.id,
            }

            # Convert values to strings for Redis storage
            redis_data = {k: str(v) for k, v in task_data.items()}
            await self.redis_client.hset(task_key, mapping=redis_data)
            await self.redis_client.expire(task_key, 3600)  # Expire in 1 hour

            logger.info(f"Task enqueued: {celery_result.id} for session: {session_id}")
            return celery_result.id

        except Exception as e:
            logger.error(f"Error enqueuing task: {str(e)}")
            raise

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status from both Redis and Celery"""
        try:
            # Get task data from Redis
            task_key = f"task:{task_id}"
            redis_data = await self.redis_client.hgetall(task_key)

            if not redis_data:
                logger.warning(f"Task not found in Redis: {task_id}")
                return None

            # Get Celery task status
            celery_result = AsyncResult(task_id, app=self.celery_app)
            celery_status = celery_result.status
            celery_result_data = celery_result.result

            # Prepare response data
            task_status = {
                "task_id": task_id,
                "session_id": redis_data.get("session_id"),
                "url": redis_data.get("url"),
                "user_id": int(redis_data.get("user_id", 0)),
                "priority": int(redis_data.get("priority", 1)),
                "created_at": redis_data.get("created_at"),
                "updated_at": redis_data.get("updated_at"),
                "status": redis_data.get("status"),
                "celery_status": celery_status,
                "celery_result": celery_result_data,
                "error": redis_data.get("error"),
            }

            # Update status based on Celery state
            if celery_status == "PENDING":
                task_status["status"] = "queued"
            elif celery_status == "STARTED":
                task_status["status"] = "processing"
            elif celery_status == "SUCCESS":
                task_status["status"] = "completed"
                task_status["result"] = celery_result_data
            elif celery_status == "FAILURE":
                task_status["status"] = "failed"
                task_status["error"] = str(celery_result_data)
            elif celery_status == "RETRY":
                task_status["status"] = "retrying"
            elif celery_status == "REVOKED":
                task_status["status"] = "cancelled"

            # Update Redis with latest status
            await self._update_redis_status(task_id, task_status["status"], task_status.get("error"))

            return task_status

        except Exception as e:
            logger.error(f"Error getting task status: {str(e)}")
            return None

    async def update_task_status(self, task_id: str, status: str, result: Optional[Dict] = None, error: Optional[str] = None) -> bool:
        """Update task status in Redis"""
        try:
            return await self._update_redis_status(task_id, status, error, result)
        except Exception as e:
            logger.error(f"Error updating task status: {str(e)}")
            return False

    async def _update_redis_status(self, task_id: str, status: str, error: Optional[str] = None, result: Optional[Dict] = None) -> bool:
        """Internal method to update Redis task status"""
        try:
            task_key = f"task:{task_id}"

            # Check if task exists
            exists = await self.redis_client.exists(task_key)
            if not exists:
                logger.warning(f"Task not found for update: {task_id}")
                return False

            update_data = {"status": status, "updated_at": datetime.utcnow().isoformat()}

            if result:
                update_data["result"] = json.dumps(result)

            if error:
                update_data["error"] = error

            await self.redis_client.hset(task_key, mapping=update_data)
            logger.info(f"Task status updated: {task_id} -> {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating Redis status: {str(e)}")
            return False

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a Celery task"""
        try:
            # Revoke Celery task
            self.celery_app.control.revoke(task_id, terminate=True)

            # Update Redis status
            success = await self._update_redis_status(task_id, "cancelled")

            if success:
                logger.info(f"Task cancelled: {task_id}")

            return success

        except Exception as e:
            logger.error(f"Error cancelling task: {str(e)}")
            return False

    async def get_queue_length(self) -> int:
        """Get approximate queue length (Celery active tasks)"""
        try:
            inspect = self.celery_app.control.inspect()
            active_tasks = inspect.active()

            if active_tasks:
                total_tasks = sum(len(tasks) for tasks in active_tasks.values())
                return total_tasks

            return 0

        except Exception as e:
            logger.error(f"Error getting queue length: {str(e)}")
            return 0

    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result from Celery"""
        try:
            celery_result = AsyncResult(task_id, app=self.celery_app)

            if celery_result.ready():
                return {"task_id": task_id, "status": celery_result.status, "result": celery_result.result, "successful": celery_result.successful(), "failed": celery_result.failed()}

            return {"task_id": task_id, "status": celery_result.status, "ready": False}

        except Exception as e:
            logger.error(f"Error getting task result: {str(e)}")
            return None

    async def cleanup_expired_tasks(self) -> int:
        """Clean up expired task data from Redis"""
        try:
            task_keys = await self.redis_client.keys("task:*")
            cleaned_count = 0

            for task_key in task_keys:
                ttl = await self.redis_client.ttl(task_key)
                if ttl == -2:  # Key doesn't exist
                    cleaned_count += 1
                elif ttl == -1:  # No expiration set
                    await self.redis_client.expire(task_key, 3600)

            logger.info(f"Cleaned up {cleaned_count} expired tasks")
            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up tasks: {str(e)}")
            return 0

    def get_celery_app(self) -> Celery:
        """Get the Celery app instance"""
        return self.celery_app
