from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import shopping as models
from app.models.shopping import ShoppingItem
from app.schemas.shopping import ShoppingListCreateRequest, ShoppingListItemResponse, ShoppingListListResponse, ShoppingListResponse, UpdateShoppingListItemRequest


class ShoppingService:
    """ショッピングサービス"""

    def __init__(self, db: Session):
        self.db = db

    def get_lists_with_pagination(self, user_id: int, page: int, per_page: int, keyword: Optional[str]) -> ShoppingListListResponse:
        query = self.db.query(models.UserShopping).filter(models.UserShopping.user_id == user_id)
        if keyword:
            query = query.filter(models.UserShopping.list_name.ilike(f"%{keyword}%"))
        total = query.count()
        pages = (total + per_page - 1) // per_page
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        item_list = [
            ShoppingListResponse(
                id=item.id,
                recipe_id=item.recipe_id,
                list_name=item.list_name,
                list_id=str(item.id),  # uuidが不要な場合はidを文字列化
                created_at=item.created_date.isoformat(),
                updated_at=item.updated_date.isoformat()
            ) for item in items
        ]
        return ShoppingListListResponse(
            items=item_list,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )

    def create_list(self, req: ShoppingListCreateRequest, user_id: int) -> ShoppingListResponse:
        new_list = models.UserShopping(
            user_id=user_id,
            recipe_id=req.recipe_id,
            list_name="Shopping List",
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
        return ShoppingListResponse(
            id=new_list.id,
            recipe_id=new_list.recipe_id,
            list_name=new_list.list_name,
            list_id=str(new_list.id),
            created_at=new_list.created_date.isoformat(),
            updated_at=new_list.updated_date.isoformat()
        )

    def get_list_detail(self, shopping_list_id: int, user_id: int) -> Optional[ShoppingListResponse]:
        item = self.db.query(models.UserShopping).filter(
            models.UserShopping.id == shopping_list_id,
            models.UserShopping.user_id == user_id
        ).first()
        if not item:
            return None
        return ShoppingListResponse(
            id=item.id,
            recipe_id=item.recipe_id,
            list_name=item.list_name,
            list_id=str(item.id),
            created_at=item.created_date.isoformat(),
            updated_at=item.updated_date.isoformat()
        )
    
    def create_items(self, items: List[ShoppingItem]) -> List[ShoppingListItemResponse]:
        """ショッピングリストアイテムを一括で作成する"""
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
            ShoppingListItemResponse(
                id=item.id,
                ingredient_id=item.ingredient_id,
                is_checked=item.is_checked,
                created_at=item.created_date.isoformat(),
                updated_at=item.updated_date.isoformat()
            ) for item in items
        ]


    def get_items(self, shopping_list_id: int, user_id: int) -> List[ShoppingListItemResponse]:
        items = self.db.query(models.ShoppingItem).filter(
            models.ShoppingItem.user_shopping_id == shopping_list_id
        ).all()
        return [
            ShoppingListItemResponse(
                id=i.id,
                ingredient_id=i.ingredient_id,
                is_checked=i.is_checked,
                created_at=i.created_date.isoformat(),
                updated_at=i.updated_date.isoformat()
            ) for i in items
        ]

    def update_item(self, shopping_list_item_id: int, req: UpdateShoppingListItemRequest, user_id: int) -> Optional[ShoppingListItemResponse]:
        item = self.db.query(models.ShoppingItem).filter(
            models.ShoppingItem.id == shopping_list_item_id
        ).first()
        if not item:
            return None
        item.is_checked = req.is_checked
        item.updated_date = datetime.utcnow()
        self.db.merge(item)
        try:
            self.db.commit()
            print("Transaction committed successfully")
        except Exception as e:
            print(f"Transaction failed: {e}")
            self.db.rollback()
            print("Transaction rolled back")
            raise e
        return ShoppingListItemResponse(
            id=item.id,
            ingredient_id=item.ingredient_id,
            is_checked=item.is_checked,
            created_at=item.created_date.isoformat(),
            updated_at=item.updated_date.isoformat()
        )