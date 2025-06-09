from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import user as crud
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

@router.put("/me", response_model=schemas.UserMe)
def update_user_me(
    user_update: schemas.UserUpdate,
    current_user = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    現在ログインしているユーザー情報を更新
    """
    updated_user = crud.update(db=db, db_obj=current_user, obj_in=user_update)
    return schemas.UserMe.from_orm(updated_user)