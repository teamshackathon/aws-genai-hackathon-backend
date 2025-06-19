import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import shopping as models
from app.schemas.shopping import ShoppingListCreateRequest, ShoppingListItemResponse, ShoppingListListResponse, ShoppingListResponse, UpdateShoppingListItemRequest


class ShoppingService:
    """ショッピングサービス"""

    def __init__(self, db: Session):
        self.db = db

    def get_lists_with_pagination(self, user_id: int, page: int, per_page: int, keyword: Optional[str]) -> ShoppingListListResponse:
        query = self.db.query(models.ShoppingList).filter(models.ShoppingList.user_id == user_id)
        if keyword:
            query = query.filter(models.ShoppingList.name.ilike(f"%{keyword}%"))
        total = query.count()
        pages = (total + per_page - 1) // per_page
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        item_list = [
            ShoppingListResponse(
                id=item.id,
                recipe_id=item.recipe_id,
                list_name=item.name,
                list_id=str(item.uuid) if hasattr(item, 'uuid') else str(uuid.uuid4()),
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat()
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
        new_list = models.ShoppingList(
            user_id=user_id,
            recipe_id=req.recipe_id,
            name="Shopping List",
            uuid=uuid.uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(new_list)
        self.db.commit()
        self.db.refresh(new_list)
        return ShoppingListResponse(
            id=new_list.id,
            recipe_id=new_list.recipe_id,
            list_name=new_list.name,
            list_id=str(new_list.uuid),
            created_at=new_list.created_at.isoformat(),
            updated_at=new_list.updated_at.isoformat()
        )

    def get_list_detail(self, shopping_list_id: int, user_id: int) -> Optional[ShoppingListResponse]:
        item = self.db.query(models.ShoppingList).filter(
            models.ShoppingList.id == shopping_list_id,
            models.ShoppingList.user_id == user_id
        ).first()
        if not item:
            return None
        return ShoppingListResponse(
            id=item.id,
            recipe_id=item.recipe_id,
            list_name=item.name,
            list_id=str(item.uuid),
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat()
        )

    def get_items(self, shopping_list_id: int, user_id: int) -> List[ShoppingListItemResponse]:
        items = self.db.query(models.ShoppingItem).filter(
            models.ShoppingItem.shopping_list_id == shopping_list_id
        ).all()
        return [
            ShoppingListItemResponse(
                id=i.id,
                ingredient_id=i.ingredient_id,
                is_checked=i.is_checked,
                created_at=i.created_at.isoformat(),
                updated_at=i.updated_at.isoformat()
            ) for i in items
        ]

    def update_item(self, shopping_list_item_id: int, req: UpdateShoppingListItemRequest, user_id: int) -> Optional[ShoppingListItemResponse]:
        item = self.db.query(models.ShoppingItem).filter(
            models.ShoppingItem.id == shopping_list_item_id
        ).first()
        if not item:
            return None
        item.is_checked = req.is_checked
        item.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(item)
        return ShoppingListItemResponse(
            id=item.id,
            ingredient_id=item.ingredient_id,
            is_checked=item.is_checked,
            created_at=item.created_at.isoformat(),
            updated_at=item.updated_at.isoformat()
        )