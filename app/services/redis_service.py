import base64
import json
from typing import Optional, Tuple

import redis.asyncio as redis

from app.core.config import settings


class RedisCacheService:
    """Redis画像キャッシュサービス"""
    
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False  # バイナリデータのためFalse
        )
    
    async def cache_image(
        self, 
        file_path: str, 
        image_data: bytes, 
        content_type: str,
        expiration: int = None
    ) -> bool:
        """画像をRedisにキャッシュ"""
        try:
            # サイズ制限チェック
            if len(image_data) > settings.REDIS_MAX_IMAGE_SIZE:
                return False
                
            cache_key = f"image:{file_path}"
            cache_value = {
                "data": base64.b64encode(image_data).decode('utf-8'),
                "content_type": content_type,
                "size": len(image_data)
            }
            
            ttl = expiration or settings.REDIS_IMAGE_CACHE_TTL
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_value)
            )
            return True
        except Exception as e:
            print(f"Redis cache error: {e}")
            return False
    
    async def cache_data(
        self, 
        key: str, 
        data: bytes,
        expiration: Optional[int] = None
    ):
        """汎用データをRedisにキャッシュ"""
        try:
            cache_key = f"data:{key}"
            await self.redis_client.set(cache_key, data, ex=expiration)
            return True
        except Exception as e:
            print(f"Redis cache error: {e}")
            return False

    async def get_cached_data(self, key: str) -> Optional[bytes]:
        """Redisから汎用データを取得"""
        try:
            cache_key = f"data:{key}"
            cached_data = await self.redis_client.get(cache_key)
            return cached_data
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    async def get_cached_image(self, file_path: str) -> Optional[Tuple[bytes, str]]:
        """Redisから画像を取得"""
        try:
            cache_key = f"image:{file_path}"
            cached_data = await self.redis_client.get(cache_key)
            
            if not cached_data:
                return None
            
            cache_value = json.loads(cached_data)
            image_data = base64.b64decode(cache_value["data"])
            content_type = cache_value["content_type"]
            
            return image_data, content_type
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    async def cache_exists(self, file_path: str) -> bool:
        """キャッシュの存在確認"""
        cache_key = f"image:{file_path}"
        return await self.redis_client.exists(cache_key) > 0
    
    async def delete_cache(self, file_path: str) -> bool:
        """キャッシュを削除"""
        cache_key = f"image:{file_path}"
        deleted = await self.redis_client.delete(cache_key)
        return deleted > 0
    
    async def get_cache_info(self, file_path: str) -> Optional[dict]:
        """キャッシュ情報を取得"""
        try:
            cache_key = f"image:{file_path}"
            cached_data = await self.redis_client.get(cache_key)
            
            if not cached_data:
                return None
            
            cache_value = json.loads(cached_data)
            ttl = await self.redis_client.ttl(cache_key)
            
            return {
                "size": cache_value["size"],
                "content_type": cache_value["content_type"],
                "ttl": ttl,
                "cached": True
            }
        except Exception:
            return None
    
    async def close(self):
        """Redis接続を閉じる"""
        await self.redis_client.close()