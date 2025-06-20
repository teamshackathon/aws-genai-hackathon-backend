from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------
# ShoppingList スキーマ
# ---------------
class ShoppingBase(BaseModel):
    """ショッピングリストの基本スキーマ"""
    recipe_id: int = Field(..., description="レシピID")

class ShoppingCreate(ShoppingBase):
    """ショッピングリスト作成スキーマ"""
    created_date: Optional[datetime] = datetime.utcnow()
    updated_date: Optional[datetime] = datetime.utcnow()

class ShoppingUpdate(BaseModel):
    """ショッピングリスト更新スキーマ"""
    list_name: Optional[str] = Field(None, description="リスト名")
    updated_date: Optional[datetime] = datetime.utcnow()

class Shopping(ShoppingBase):
    """ショッピングリスト応答スキーマ"""
    id: int
    list_name: str = Field(..., description="リスト名")
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True

# ---------------
# UserShopping スキーマ
# ---------------
class UserShoppingBase(BaseModel):
    """ユーザーショッピングの基本スキーマ"""
    shopping_id: int = Field(..., description="ショッピングID")
    user_id: int = Field(..., description="ユーザーID")
    is_favorite: bool = Field(False, description="お気に入りフラグ")

class UserShoppingCreate(UserShoppingBase):
    """ユーザーショッピング作成スキーマ"""
    created_date: Optional[datetime] = datetime.utcnow()
    updated_date: Optional[datetime] = datetime.utcnow()

class UserShoppingUpdate(BaseModel):
    """ユーザーショッピング更新スキーマ"""
    is_favorite: Optional[bool] = Field(None, description="お気に入りフラグ")
    updated_date: Optional[datetime] = datetime.utcnow()

class UserShopping(UserShoppingBase):
    """ユーザーショッピング応答スキーマ"""
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
    shopping_id: int = Field(..., description="ショッピングID")
    ingredient: str = Field(..., description="材料名")
    amount: Optional[str] = Field(None, description="量（単位付き）")
    is_checked: bool = Field(False, description="購入済みフラグ")

class ShoppingItemCreate(ShoppingItemBase):
    """ショッピングアイテム作成スキーマ"""
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
    id: Optional[int] = None
    shopping_id: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True

# ---------------
# ShoppingList詳細スキーマ
# ---------------

class ShoppingList(BaseModel):
    items: List[Shopping]
    total: int
    page: int
    per_page: int
    pages: int
