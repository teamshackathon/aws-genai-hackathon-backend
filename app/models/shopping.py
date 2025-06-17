from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.base_class import Base


class UserShopping(Base):
    """ユーザーショッピングモデル"""
    __tablename__ = "user_shoppings"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False, comment="レシピID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="ユーザーID")
    list_name = Column(String(256), nullable=False, comment="買い物リスト名")
    created_date = Column(DateTime, default=func.now(), nullable=False, comment="作成日時")
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新日時")


class ShoppingItem(Base):
    """ショッピングアイテムモデル"""
    __tablename__ = "shopping_items"

    id = Column(Integer, primary_key=True, index=True)
    user_shopping_id = Column(Integer, ForeignKey("user_shoppings.id"), nullable=False, comment="ユーザーショッピングID")
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False, comment="材料ID")
    is_checked = Column(Boolean, default=False, comment="チェック済みフラグ")
    created_date = Column(DateTime, default=func.now(), nullable=False, comment="作成日時")
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新日時")