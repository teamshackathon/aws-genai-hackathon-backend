from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.crud.recipe import (
    get_recipes, 
    get_recipe, 
    get_all_recipes_no_limit,
    get_recipes_with_details
)
from app.schemas.recipe import Recipe

router = APIRouter()


@router.get("/all", response_model=List[Recipe], tags=["recipes"])
def get_all_recipes(db: Session = Depends(get_db)):
    """
    全レシピを取得（制限なし）
    ブラウザで http://localhost:8000/recipes/all にアクセス
    """
    recipes = get_all_recipes_no_limit(db=db)
    return recipes


@router.get("", response_model=List[Recipe], tags=["recipes"])
def get_recipes_with_pagination(
    skip: int = 0,
    limit: int = 100,
    status_id: Optional[int] = None,
    external_service_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    レシピ一覧を取得（フィルタ・ページネーション対応）
    
    使用例:
    - 全件: http://localhost:8000/recipes
    - ページネーション: http://localhost:8000/recipes?skip=0&limit=10
    - フィルタ: http://localhost:8000/recipes?status_id=0
    """
    recipes = get_recipes(
        db=db, 
        skip=skip, 
        limit=limit, 
        status_id=status_id, 
        external_service_id=external_service_id
    )
    return recipes


@router.get("/{recipe_id}", response_model=Recipe, tags=["recipes"])
def get_recipe_by_id(recipe_id: int, db: Session = Depends(get_db)):
    """
    レシピIDを指定して単一レシピを取得
    
    使用例: http://localhost:8000/recipes/1
    """
    recipe = get_recipe(db=db, recipe_id=recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.get("/details/all", response_model=List[Recipe], tags=["recipes"])
def get_all_recipes_with_details(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    レシピ一覧を詳細情報付きで取得
    
    使用例: http://localhost:8000/recipes/details/all
    """
    recipes = get_recipes_with_details(db=db, skip=skip, limit=limit)
    return recipes