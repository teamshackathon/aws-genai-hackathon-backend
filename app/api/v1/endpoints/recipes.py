from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import Users
from app.schemas.recipe import Recipe, RecipeList
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

# ページネーション付きのレシピ一覧を取得
@router.get("", response_model=RecipeList)
def get_recipes(
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(20, ge=1, le=100, description="1ページあたりのレシピ数"),
    keyword: Optional[str] = Query(None, description="検索キーワード"),
    favorites_only: bool = Query(False, description="お気に入りのみを取得するかどうか"),
    recipe_service: RecipeService = Depends(get_recipe_service),
    current_user: Users = Depends(deps.get_current_user)
) -> RecipeList:
    """
    ページネーション付きのレシピ一覧を取得します。
    """
    return recipe_service.get_recipes(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        keyword=keyword,
        favorites_only=favorites_only
    )


@router.get("/{recipe_id}", response_model=Recipe)
def get_recipe_by_id(
    recipe_id: int, 
    recipe_service: RecipeService = Depends(get_recipe_service),
    current_user: Users = Depends(deps.get_current_user)
) -> Recipe:
    """
    指定されたIDの単一レシピを取得します。
    """
    recipe = recipe_service.get_recipe_by_id(recipe_id, current_user.id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe