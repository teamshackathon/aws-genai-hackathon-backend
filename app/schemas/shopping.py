from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------
# ShoppingList スキーマ
# ---------------
class ShoppingListBase(BaseModel):
    """ショッピングリストの基本スキーマ"""
    user_id: int = Field(..., description="ユーザーID")
    name: str = Field(..., description="リスト名")

class ShoppingListCreate(ShoppingListBase):
    """ショッピングリスト作成スキーマ"""
    created_date: Optional[datetime] = datetime.utcnow()
    updated_date: Optional[datetime] = datetime.utcnow()

class ShoppingListUpdate(BaseModel):
    """ショッピングリスト更新スキーマ"""
    name: Optional[str] = Field(None, description="リスト名")
    updated_date: Optional[datetime] = datetime.utcnow()

class ShoppingList(ShoppingListBase):
    """ショッピングリスト応答スキーマ"""
    id: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True

# ---------------
# ShoppingItem スキーマ
# ---------------
class ShoppingItemBase(BaseModel):
    """ショッピングアイテムの基本スキーマ"""
    ingredient: str = Field(..., description="材料名")
    amount: Optional[str] = Field(None, description="量（単位付き）")
    is_checked: bool = Field(False, description="購入済みフラグ")

class ShoppingItemCreate(ShoppingItemBase):
    """ショッピングアイテム作成スキーマ"""
    shopping_list_id: int
    created_date: Optional[datetime] = datetime.utcnow()
    updated_date: Optional[datetime] = datetime.utcnow()

class ShoppingItemUpdate(BaseModel):
    """ショッピングアイテム更新スキーマ"""
    ingredient: Optional[str] = Field(None, description="材料名")
    amount: Optional[str] = Field(None, description="量（単位付き）")
    is_checked: Optional[bool] = Field(None, description="購入済みフラグ")
    updated_date: Optional[datetime] = datetime.utcnow()

class ShoppingItem(ShoppingItemBase):
    """ショッピングアイテム応答スキーマ"""
    id: int
    shopping_list_id: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True

# ---------------
# ShoppingList詳細スキーマ
# ---------------
class ShoppingListDetail(ShoppingList):
    """ショッピングリスト詳細（アイテム一覧を含む）"""
    items: List[ShoppingItem] = []

    class Config:
        from_attributes = True
