import gc
import mimetypes
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.services.redis_service import RedisCacheService
from app.services.storage_service import StorageService

router = APIRouter()

def get_file_service() -> StorageService:
    """Fileサービスを取得"""
    try:
        return StorageService()
    except ValueError:
        raise HTTPException(
            status_code=500, detail="Failed to initialize TASUKI service. Please check API key configuration."
        )

def get_redis_service() -> RedisCacheService:
    """Redisキャッシュサービスを取得"""
    try:
        return RedisCacheService()
    except ValueError:
        raise HTTPException(
            status_code=500, detail="Failed to initialize Redis cache service. Please check configuration."
        )
    
@asynccontextmanager
async def managed_image_download(storage: StorageService, file_path: str):
    """メモリ管理付き画像ダウンロード"""
    contents = None
    try:
        contents = await storage.download_file(file_path)
        yield contents
    finally:
        # 明示的なメモリクリーンアップ
        if contents:
            del contents
            # 必要に応じてガベージコレクション
            if gc.get_count()[0] > 700:
                gc.collect()

# 画像をフロントエンドに表示するためのプロキシーエンドポイント
@router.get("/images/{file_path:path}")
async def get_image(
    file_path: str,
    use_cache: bool = Query(True, description="Redisキャッシュを使用するか"),
    storage: StorageService = Depends(get_file_service),
    cache_service: RedisCacheService = Depends(get_redis_service),
    # current_user = Depends(deps.get_current_user)
):
    """メモリ最適化された画像取得（Redisキャッシュ対応）"""
    try:
        # キャッシュから取得を試行
        if use_cache:
            cached_result = await cache_service.get_cached_image(file_path)
            print(f"Cache lookup for {file_path}: {cached_result is not None}")
            if cached_result:
                image_data, content_type = cached_result
                return Response(
                    content=image_data,
                    media_type=content_type,
                    headers={
                        "X-Cache": "HIT",
                        "Cache-Control": "public, max-age=3600"
                    }
                )
        
        # キャッシュにない場合はストレージから取得（メモリ管理付き）
        async with managed_image_download(storage, file_path) as contents:
            if not contents:
                raise HTTPException(status_code=404, detail="画像が見つかりません")

            # MIMEタイプの推測を改善
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type or not content_type.startswith('image/'):
                # ファイル拡張子による判定
                if file_path.lower().endswith(('.jpg', '.jpeg')):
                    content_type = "image/jpeg"
                elif file_path.lower().endswith('.png'):
                    content_type = "image/png"
                elif file_path.lower().endswith('.gif'):
                    content_type = "image/gif"
                elif file_path.lower().endswith('.webp'):
                    content_type = "image/webp"
                else:
                    content_type = "image/jpeg"  # デフォルト
            
            # 小さい画像のみキャッシュに保存
            if use_cache and len(contents) <= 1024 * 1024 * 5:  # 5MB以下
                print(f"Caching image {file_path} of size {len(contents)} bytes")
                await cache_service.cache_image(file_path, contents, content_type)

            # レスポンスデータをコピー（元のcontentsは解放される）
            response_data = bytes(contents)
            
            return Response(
                content=response_data,
                media_type=content_type,
                headers={
                    "X-Cache": "MISS",
                    "Cache-Control": "public, max-age=3600",
                    "Content-Length": str(len(response_data))
                }
            )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="画像が見つかりません")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像取得エラー: {str(e)}")