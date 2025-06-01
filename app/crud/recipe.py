from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.recipe import Recipe
from app.schemas.recipe import RecipeCreate


def create_recipe(db: Session, *, recipe_in: RecipeCreate) -> Recipe:
    """新しいレシピを作成"""

def get_recipe(db: Session, recipe_id: int) -> Optional[Recipe]:
    """IDでレシピを取得"""

def get_recipes(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status_id: Optional[int] = None,
    external_service_id: Optional[int] = None
) -> List[Recipe]:
    """レシピ一覧を取得（フィルタ付き）"""
