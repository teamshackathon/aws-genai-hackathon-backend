from typing import Any

from fastapi import APIRouter, Depends

from app.api import deps
from app.schemas import user as schemas

router = APIRouter()

# 自分のユーザー情報を取得するエンドポイント
@router.get("/me", response_model=schemas.UserMe)
def read_users_me(current_user = Depends(deps.get_current_user)) -> Any:
    """
    現在ログインしているユーザー情報を取得
    """
    # 返却するカラムを制限
    current_user = schemas.User.from_orm(current_user)
    return current_user