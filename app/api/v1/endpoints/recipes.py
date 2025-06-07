from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.recipes import get_recipe, get_recipes, get_recipes_with_details
from app.schemas.recipe import Recipe

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.get("", response_model=List[Recipe])
def read_recipes(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status_id: Optional[int] = None,
    external_service_id: Optional[int] = None,
    with_details: bool = False
):
    """
    レシピの一覧を取得します。
    """
    if with_details:
        return get_recipes_with_details(db=db, skip=skip, limit=limit)
    
    return get_recipes(
        db=db,
        skip=skip,
        limit=limit,
        status_id=status_id,
        external_service_id=external_service_id,
    )


@router.get("/{recipe_id}", response_model=Recipe)
def read_recipe_by_id(recipe_id: int, db: Session = Depends(deps.get_db)):
    """
    指定されたIDの単一レシピを取得します。
    """
    db_recipe = get_recipe(db=db, recipe_id=recipe_id)
    if db_recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return db_recipe