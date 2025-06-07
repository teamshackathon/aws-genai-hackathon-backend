from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.schemas.recipe import RecipeCreate


def create_recipe(db: Session, *, recipe_in: RecipeCreate) -> Recipe:
    """新しいレシピを作成"""
    db_recipe = Recipe(
        recipe_name=recipe_in.recipe_name,
        url=recipe_in.url,
        status_id=recipe_in.status_id,
        external_service_id=recipe_in.external_service_id
    )
    db.add(db_recipe)
    db.commit()
    db.refresh(db_recipe)
    return db_recipe


def get_recipe(db: Session, recipe_id: int) -> Optional[Recipe]:
    """IDでレシピを取得（全カラム）"""
    return db.query(Recipe).filter(Recipe.id == recipe_id).first()


def get_recipes(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status_id: Optional[int] = None,
    external_service_id: Optional[int] = None
) -> List[Recipe]:
    """レシピ一覧を取得（全カラム、フィルタ付き）"""
    query = db.query(Recipe)
    
    # フィルタ条件を追加
    if status_id is not None:
        query = query.filter(Recipe.status_id == status_id)
    
    if external_service_id is not None:
        query = query.filter(Recipe.external_service_id == external_service_id)
    
    # ページネーションを適用して全カラムを取得
    return query.offset(skip).limit(limit).all()


def get_all_recipes_no_limit(db: Session) -> List[Recipe]:
    """制限なしで全レシピを取得"""
    return db.query(Recipe).all()


def get_recipe_with_details(db: Session, recipe_id: int) -> Optional[Recipe]:
    """
    IDでレシピを取得（リレーション情報も含む）
    status と external_service の情報も一緒に取得
    """
    return (
        db.query(Recipe)
        .filter(Recipe.id == recipe_id)
        .first()
    )


def get_recipes_with_details(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[Recipe]:
    """
    レシピ一覧を取得（リレーション情報も含む）
    status と external_service の情報も一緒に取得
    """
    return (
        db.query(Recipe)
        .offset(skip)
        .limit(limit)
        .all()
    )