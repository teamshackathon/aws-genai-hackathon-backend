import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import user as crud
from app.schemas import user as schemas
from app.schemas.recipe import UserRecipeUpdate
from app.services.recipe_service import RecipeService

router = APIRouter()

def get_recipe_service(db: Session = Depends(deps.get_db)) -> RecipeService:
    """
    レシピサービスの依存関係を取得します。
    """
    try:
        return RecipeService(db=db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"レシピサービスの初期化に失敗しました: {str(e)}"
        )


# ロガーの設定
logger = logging.getLogger(__name__)

# 自分のユーザー情報を取得するエンドポイント
@router.get("/me", response_model=schemas.UserMe)
def read_users_me(current_user = Depends(deps.get_current_user)) -> Any:
    """
    現在ログインしているユーザー情報を取得
    """
    # 返却するカラムを制限
    current_user = schemas.User.from_orm(current_user)
    logger.info(f"現在のユーザー情報: {current_user.id}")
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

@router.put("/me/recipes/{recipe_id}", response_model=bool)
def update_user_recipe(
    recipe_id: int,
    user_recipe_update: UserRecipeUpdate,
    current_user = Depends(deps.get_current_user),
    recipe_service: RecipeService = Depends(get_recipe_service),
) -> bool:
    """
    ユーザーのレシピ情報を更新
    """
    try:
        # ユーザーのレシピ情報を取得

        # 更新処理
        updated_user_recipe = recipe_service.update_user_recipe(
            user_id=current_user.id,
            recipe_id=recipe_id,
            is_favorite=user_recipe_update.is_favorite,
        )
        
        if not updated_user_recipe:
            raise ValueError(f"レシピID {recipe_id} のユーザーレシピが見つかりません。")
        

        return True
    except ValueError as e:
        logger.error(f"レシピ更新エラー: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )