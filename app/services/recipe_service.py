from typing import Optional

from sqlalchemy.orm import Session

from app.models.recipe import ExternalService, Recipe, RecipeStatus
from app.models.user_recipe import UserRecipe
from app.schemas.recipe import RecipeList


class RecipeService:

    def __init__(self, db: Session):
        self.db = db
    

    def get_recipe_by_id(self, recipe_id: int, user_id: int) -> Recipe:
        """指定されたIDのレシピを取得"""
        recipe = self.db.query(Recipe).join(UserRecipe).filter(
            Recipe.id == recipe_id,
            UserRecipe.user_id == user_id
        ).first()
        if recipe is None:
            raise ValueError(f"Recipe with id {recipe_id} not found for user {user_id}")
        return recipe
    
    # pagenation付きのレシピ一覧を取得
    def get_recipes(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        keyword: Optional[str] = None,
        favorites_only: bool = False
    ) -> RecipeList:
        """レシピの一覧を取得"""
        query = self.db.query(Recipe).join(UserRecipe).filter(
            UserRecipe.user_id == user_id
        )

        if keyword:
            query = query.filter(Recipe.title.ilike(f"%{keyword}%"))

        if favorites_only:
            query = query.filter(UserRecipe.is_favorite.is_(True))

        total_count = query.count()
        recipes = query.offset((page - 1) * per_page).limit(per_page).all()
        pages = (total_count + per_page - 1) // per_page

        return RecipeList(items=recipes, total=total_count, page=page, per_page=per_page, pages=pages)
    
    def get_external_services(self) -> list[ExternalService]:
        """外部サービスの一覧を取得"""
        return self.db.query(ExternalService).all()
    
    def get_recipe_statuses(self) -> list[RecipeStatus]:
        """レシピステータスの一覧を取得"""
        return self.db.query(RecipeStatus).all()