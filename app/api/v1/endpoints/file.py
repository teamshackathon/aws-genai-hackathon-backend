
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api import deps
from app.crud.minio import StorageService

router = APIRouter()

def get_file_service() -> StorageService:
    """Fileサービスを取得"""
    try:
        return StorageService()
    except ValueError:
        raise HTTPException(
            status_code=500, detail="Failed to initialize TASUKI service. Please check API key configuration."
        )
    
@router.get("")
async def list_files(
    prefix: str = Query("", description="検索するプレフィックス"),
    storage: StorageService = Depends(get_file_service),
    current_user = Depends(deps.get_current_user)
):
    """指定したプレフィックスのファイル一覧を取得する"""
    try:
        files = await storage.list_files(prefix)
        return {"files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイル一覧取得エラー: {str(e)}")
    

