from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.recipe import ExternalService, Ingredient, Process, Recipe, RecipeStatus
from app.models.user_recipe import UserRecipe
from app.schemas.recipe import IngredientUpdate, ProcessUpdate, RecipeList


class RecipeService:

    def __init__(self, db: Session):
        self.db = db

    def get_recipe_by_id(self, recipe_id: int, user_id: int) -> Recipe:
        """指定されたIDのレシピを取得"""
        result = self.db.query(Recipe).join(UserRecipe).filter(
            Recipe.id == recipe_id,
            UserRecipe.user_id == user_id
        ).first()
        
        if result is None:
            raise ValueError(f"Recipe with id {recipe_id} not found for user {user_id}")
        return result
    
    # pagenation付きのレシピ一覧を取得
    def get_recipes(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        keyword: Optional[str] = None,
        favorites_only: bool = False,
        sorted_by: Optional[str] = None, # "created_date", "updated_date", "recipe_name", "rating" などのソート条件
        order_by: Optional[str] = None
    ) -> RecipeList:
        """レシピの一覧を取得"""
        query = self.db.query(Recipe).join(UserRecipe).filter(
            UserRecipe.user_id == user_id
        )

        # フィルタリング条件の適用
        if keyword:
            query = query.filter(
                (Recipe.recipe_name.ilike(f"%{keyword}%")) |
                (Recipe.keyword.ilike(f"%{keyword}%")) |
                (Recipe.genrue.ilike(f"%{keyword}%"))
            )

        if favorites_only:
            query = query.filter(UserRecipe.is_favorite.is_(True))

        # ソート条件の適用
        if sorted_by and order_by:
            if sorted_by == "created_date":
                if order_by == "asc":
                    query = query.order_by(Recipe.created_date.asc())
                elif order_by == "desc":
                    query = query.order_by(Recipe.created_date.desc())
                query = query.order_by(Recipe.created_date.desc())
            elif sorted_by == "updated_date":
                if order_by == "asc":
                    query = query.order_by(Recipe.updated_date.asc())
                elif order_by == "desc":
                    query = query.order_by(Recipe.updated_date.desc())
            elif sorted_by == "recipe_name":
                if order_by == "asc":
                    query = query.order_by(Recipe.recipe_name.asc())
                elif order_by == "desc":
                    query = query.order_by(Recipe.recipe_name.desc())
            elif sorted_by == "rating":
                if order_by == "asc":
                    query = query.order_by(UserRecipe.rating.asc())
                elif order_by == "desc":
                    query = query.order_by(UserRecipe.rating.desc())

        total_count = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        pages = (total_count + per_page - 1) // per_page

        return RecipeList(items=results, total=total_count, page=page, per_page=per_page, pages=pages)
    
    def get_external_services(self) -> List[ExternalService]:
        """外部サービスの一覧を取得"""
        return self.db.query(ExternalService).all()
    
    def get_recipe_statuses(self) -> List[RecipeStatus]:
        """レシピステータスの一覧を取得"""
        return self.db.query(RecipeStatus).all()
    
    def get_ingredient_by_recipe_id(self, recipe_id: int) -> List[Ingredient]:
        """指定されたレシピIDの材料を取得"""
        return self.db.query(Ingredient).filter(Ingredient.recipe_id == recipe_id).all()
    
    def get_processes_by_recipe_id(self, recipe_id: int) -> List[Process]:
        """指定されたレシピIDの調理手順を取得"""
        return self.db.query(Process).filter(Process.recipe_id == recipe_id).all()
    
    async def create_recipe(self, recipe: Recipe) -> Recipe:
        """新しいレシピを作成"""
        self.db.add(recipe)
        self.db.commit()
        self.db.refresh(recipe)
        return recipe
    
    async def create_user_recipe(self, user_recipe: UserRecipe) -> UserRecipe:
        """ユーザーレシピを作成"""
        self.db.add(user_recipe)
        self.db.commit()
        self.db.refresh(user_recipe)
        return user_recipe
    
    def create_ingredient(self, recipe_id: int, ingredient: str, amount: str) -> Ingredient:
        """新しい材料を作成"""
        new_ingredient = Ingredient(
            recipe_id=recipe_id, 
            ingredient=ingredient, 
            amount=amount,
            created_date=datetime.utcnow(),
            updated_date=datetime.utcnow()
        )
        self.db.add(new_ingredient)
        self.db.commit()
        self.db.refresh(new_ingredient)
        return new_ingredient
    
    async def create_ingredients(self, ingredients: List[Ingredient]) -> List[Ingredient]:
        """材料を一括で作成"""
        self.db.add_all(ingredients)
        self.db.commit()
        for ingredient in ingredients:
            self.db.refresh(ingredient)
        return ingredients
    
    async def create_processes(self, processes: List[Process]) -> List[Process]:
        """調理手順を一括で作成"""
        self.db.add_all(processes)
        self.db.commit()
        for process in processes:
            self.db.refresh(process)
        return processes
    
    def update_recipe(self, recipe:Recipe) -> Recipe:
        """既存のレシピを更新"""
        self.db.merge(recipe)
        self.db.commit()
        self.db.refresh(recipe)
        return recipe
    
    def update_ingredients(self, ingredient_id, ingredients: IngredientUpdate) -> Ingredient:
        """材料を一括で更新"""
        existing_ingredient = self.db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if existing_ingredient is None:
            raise ValueError(f"Ingredient with id {ingredient_id} not found")
        # 更新するフィールドを設定
        existing_ingredient.ingredient = ingredients.ingredient
        existing_ingredient.amount = ingredients.amount
        existing_ingredient.updated_date = datetime.utcnow()
        self.db.commit()
        self.db.refresh(existing_ingredient)
        return existing_ingredient
    
    def delete_ingredient(self, ingredient_id: int) -> bool:
        """指定されたIDの材料を削除"""
        ingredient = self.db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if ingredient is None:
            raise ValueError(f"Ingredient with id {ingredient_id} not found")
        self.db.delete(ingredient)
        self.db.commit()
        return True
    
    def create_process(self, recipe_id: int, process_number: int, process: str) -> Process:
        """新しい調理手順を作成"""
        new_process = Process(
            recipe_id=recipe_id,
            process_number=process_number,
            process=process,
            created_date=datetime.utcnow(),
            updated_date=datetime.utcnow()
        )
        self.db.add(new_process)
        self.db.commit()
        self.db.refresh(new_process)
        return new_process
    
    def update_process(self, process_id: int, process: ProcessUpdate) -> Process:
        """調理手順を更新"""
        existing_process = self.db.query(Process).filter(Process.id == process_id).first()
        if existing_process is None:
            raise ValueError(f"Process with id {process_id} not found")
        # 更新するフィールドを設定
        if process.process_number is not None:
            existing_process.process_number = process.process_number
        if process.process is not None:
            existing_process.process = process.process
        existing_process.updated_date = datetime.utcnow()
        self.db.commit()
        self.db.refresh(existing_process)
        return existing_process
    
    def delete_process(self, process_id: int) -> bool:
        """指定されたIDの調理手順を削除"""
        process = self.db.query(Process).filter(Process.id == process_id).first()
        if process is None:
            raise ValueError(f"Process with id {process_id} not found")
        self.db.delete(process)
        self.db.commit()
        return True

    def get_user_recipe(self, user_id: int, recipe_id: int) -> UserRecipe:
        """ユーザーレシピを取得"""
        user_recipe = self.db.query(UserRecipe).filter(
            UserRecipe.user_id == user_id,
            UserRecipe.recipe_id == recipe_id
        ).first()
        if user_recipe is None:
            raise ValueError(f"UserRecipe with user_id {user_id} and recipe_id {recipe_id} not found")
        return user_recipe
    
    def get_user_recipes(self, user_id: int) -> List[UserRecipe]:
        """ユーザーレシピの一覧を取得"""
        return self.db.query(UserRecipe).filter(UserRecipe.user_id == user_id).all()
    
    def get_user_recipes_by_ids(self, user_id: int, recipe_ids: List[int]) -> List[UserRecipe]:
        """ユーザーレシピのIDリストからレシピを取得"""
        if not recipe_ids:
            return []

        return self.db.query(UserRecipe).filter(
            UserRecipe.user_id == user_id,
            UserRecipe.recipe_id.in_(recipe_ids)
        ).all()
    
    def get_user_recipe_by_id(self, user_id: int, recipe_id: int) -> UserRecipe:
        """ユーザーレシピをIDで取得"""
        user_recipe = self.db.query(UserRecipe).filter(
            UserRecipe.user_id == user_id,
            UserRecipe.recipe_id == recipe_id
        ).first()
        if user_recipe is None:
            raise ValueError(f"UserRecipe with user_id {user_id} and recipe_id {recipe_id} not found")
        return user_recipe
    
    def update_user_recipe(self, user_id: int, recipe_id: int, is_favorite: bool, note: str, rating: int) -> UserRecipe:
        """ユーザーレシピを更新"""
        db_user_recipe = self.db.query(UserRecipe).filter(
            UserRecipe.user_id == user_id,
            UserRecipe.recipe_id == recipe_id
        ).first()
        if db_user_recipe is None:
            raise ValueError(f"UserRecipe with user_id {user_id} and recipe_id {recipe_id} not found")
        if is_favorite is not None:
            db_user_recipe.is_favorite = is_favorite
        if note is not None:
            db_user_recipe.note = note
        if rating is not None:
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")
            db_user_recipe.rating = rating
        db_user_recipe.updated_date = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_user_recipe)
        return db_user_recipe