from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.shopping import ShoppingItem, UserShopping


class ShoppingService:
    """ショッピングサービス"""

    def __init__(self, db: Session):
        self.db = db

    def get_shopping_list(self, user_id: int, list_name: Optional[str] = None) -> List[dict]:
        """ユーザーのショッピングリストを取得"""
        query = self.db.query(UserShopping).filter(UserShopping.user_id == user_id)
        if list_name:
            query = query.filter(UserShopping.list_name == list_name)
        return query.all()

    def add_shopping_item(self, user_id: int, recipe_id: int, item_name: str) -> None:
        """ショッピングアイテムを追加"""
        shopping_item = ShoppingItem(
            user_shopping_id=user_id,
            ingredient_id=recipe_id,
            is_checked=False,
            created_date=datetime.now(),
            updated_date=datetime.now()
        )
        self.db.add(shopping_item)
        self.db.commit()