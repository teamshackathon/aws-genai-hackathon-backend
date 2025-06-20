from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.shopping import Shopping, ShoppingItem, UserShopping
from app.schemas.shopping import ShoppingItemCreate, ShoppingItemUpdate, ShoppingList


class ShoppingService:
    """ショッピングサービス"""

    def __init__(self, db: Session):
        self.db = db

    def get_lists_with_pagination(self, user_id: int, page: int, per_page: int, keyword: Optional[str]) -> ShoppingList:
        query = self.db.query(Shopping).join(UserShopping).filter(
            UserShopping.user_id == user_id
        ).order_by(Shopping.created_date.desc())
        if keyword:
            query = query.filter(Shopping.list_name.ilike(f"%{keyword}%"))
        total = query.count()
        pages = (total + per_page - 1) // per_page
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        item_list = [
            Shopping(
                id=item.id,
                recipe_id=item.recipe_id,
                list_name=item.list_name,
                created_date=item.created_date.isoformat(),
                updated_date=item.updated_date.isoformat()
            ) for item in items
        ]
        return ShoppingList(
            items=item_list,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )

    def get_user_shoppings_by_ids(self, shopping_ids: List[int], user_id: int) -> List[UserShopping]:
        """指定されたショッピングIDのリストを取得"""
        if not shopping_ids:
            return []
        user_shoppings = self.db.query(UserShopping).filter(
            UserShopping.shopping_id.in_(shopping_ids),
            UserShopping.user_id == user_id
        ).all()
        return user_shoppings
    
    def get_user_shopping_by_id(self, user_shopping_id: int, user_id: int) -> Optional[UserShopping]:
        """ユーザーショッピングをIDで取得"""
        user_shopping = self.db.query(UserShopping).filter(
            UserShopping.id == user_shopping_id,
            UserShopping.user_id == user_id
        ).first()
        if not user_shopping:
            return None
        return user_shopping
    
    def get_user_shoppings(self, user_id: int) -> List[UserShopping]:
        """ユーザーのショッピングリストを取得"""
        user_shoppings = self.db.query(UserShopping).filter(
            UserShopping.user_id == user_id
        ).all()
        return user_shoppings
    
    def update_user_shopping(self, user_shopping_id: int, is_favorite: bool) -> Optional[UserShopping]:
        """ユーザーショッピングの更新"""
        user_shopping = self.db.query(UserShopping).filter(
            UserShopping.id == user_shopping_id
        ).first()
        if not user_shopping:
            return None
        user_shopping.is_favorite = is_favorite
        user_shopping.updated_date = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user_shopping)
        return user_shopping

    def create_list(self, recipe_id: int, list_name: str) -> Shopping:
        new_list = Shopping(
            recipe_id=recipe_id,
            list_name=list_name,
            created_date=datetime.utcnow(),
            updated_date=datetime.utcnow()
        )
        self.db.add(new_list)
        try:
            self.db.commit()
            print("Transaction committed successfully")
        except Exception as e:
            print(f"Transaction failed: {e}")
            self.db.rollback()
            print("Transaction rolled back")
            raise e
        self.db.refresh(new_list)
        return Shopping(
            id=new_list.id,
            recipe_id=new_list.recipe_id,
            list_name=new_list.list_name,
            created_date=new_list.created_date.isoformat(),
            updated_date=new_list.updated_date.isoformat()
        )

    def get_shopping(self, shopping_id: int, user_id: int) -> Optional[Shopping]:
        shopping = self.db.query(Shopping).join(UserShopping).filter(
            Shopping.id == shopping_id,
            UserShopping.user_id == user_id
        ).first()
        if not shopping:
            return None
        return shopping
    
    def create_items(self, items: List[ShoppingItemCreate]) -> List[ShoppingItem]:
        """ショッピングリストアイテムを一括で作成する"""
        if not items:
            return []
        items = [
            ShoppingItem(
                shopping_id=item.shopping_id,
                ingredient=item.ingredient,
                amount=item.amount,
                is_checked=item.is_checked,
                created_date=datetime.utcnow(),
                updated_date=datetime.utcnow()
            ) for item in items
        ]
        self.db.add_all(items)
        try:
            self.db.commit()
            print("Transaction committed successfully")
        except Exception as e:
            print(f"Transaction failed: {e}")
            self.db.rollback()
            print("Transaction rolled back")
            raise e
        for item in items:
            self.db.refresh(item)
        return [
            ShoppingItem(
                id=item.id,
                ingredient=item.ingredient,
                amount=item.amount,
                is_checked=item.is_checked,
                created_date=item.created_date.isoformat(),
                updated_date=item.updated_date.isoformat()
            ) for item in items
        ]

    def create_user_shopping(self, shopping_id: int, user_id: int) -> UserShopping:
        new_user_shopping = UserShopping(
            shopping_id=shopping_id,
            user_id=user_id,
            is_favorite=False,
            created_date=datetime.utcnow(),
            updated_date=datetime.utcnow()
        )
        self.db.add(new_user_shopping)
        try:
            self.db.commit()
            print("Transaction committed successfully")
        except Exception as e:
            print(f"Transaction failed: {e}")
            self.db.rollback()
            print("Transaction rolled back")
            raise e
        self.db.refresh(new_user_shopping)
        return UserShopping(
            id=new_user_shopping.id,
            shopping_id=new_user_shopping.shopping_id,
            user_id=new_user_shopping.user_id,
            is_favorite=new_user_shopping.is_favorite,
            created_date=new_user_shopping.created_date.isoformat(),
            updated_date=new_user_shopping.updated_date.isoformat()
        )

    def get_items(self, shopping_id: int) -> List[ShoppingItem]:
        items = self.db.query(ShoppingItem).filter(
            ShoppingItem.shopping_id == shopping_id
        ).all()
        return [
            ShoppingItem(
                id=item.id,
                shopping_id=item.shopping_id,
                ingredient=item.ingredient,
                amount=item.amount,
                is_checked=item.is_checked,
                created_date=item.created_date.isoformat(),
                updated_date=item.updated_date.isoformat()
            ) for item in items
        ]

    def update_item(self, shopping_item_id: int, req: ShoppingItemUpdate) -> Optional[ShoppingItem]:
        item = self.db.query(ShoppingItem).filter(
            ShoppingItem.id == shopping_item_id
        ).first()
        if not item:
            return None
        if req.ingredient is not None:
            item.ingredient = req.ingredient
        if req.amount is not None:
            item.amount = req.amount
        if req.is_checked is not None:
            item.is_checked = req.is_checked
        item.updated_date = datetime.utcnow()
        self.db.commit()
        self.db.refresh(item)
        return ShoppingItem(
            id=item.id,
            shopping_id=item.shopping_id,
            ingredient=item.ingredient,
            amount=item.amount,
            is_checked=item.is_checked,
            created_date=item.created_date.isoformat(),
            updated_date=item.updated_date.isoformat()
        )