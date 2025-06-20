from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.base_class import Base


class Shopping(Base):
    """ショッピングモデル"""
    __tablename__ = "shoppings"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False, comment="レシピID")
    list_name = Column(String(256), nullable=False, comment="買い物リスト名")
    created_date = Column(DateTime, default=func.now(), nullable=False, comment="作成日時")
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新日時")


class UserShopping(Base):
    """ユーザーショッピングモデル"""
    __tablename__ = "user_shoppings"

    id = Column(Integer, primary_key=True, index=True)
    shopping_id = Column(Integer, ForeignKey("shoppings.id"), nullable=False, comment="レシピID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="ユーザーID")
    is_favorite = Column(Boolean, default=False, comment="お気に入りフラグ")
    created_date = Column(DateTime, default=func.now(), nullable=False, comment="作成日時")
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新日時")


class ShoppingItem(Base):
    """ショッピングアイテムモデル"""
    __tablename__ = "shopping_items"

    id = Column(Integer, primary_key=True, index=True)
    shopping_id = Column(Integer, ForeignKey("shoppings.id"), nullable=False, comment="ショッピングID")
    ingredient = Column(String(256), nullable=False, comment="材料名")
    amount = Column(String(64), nullable=True, comment="数量")
    is_checked = Column(Boolean, default=False, comment="チェック済みフラグ")
    created_date = Column(DateTime, default=func.now(), nullable=False, comment="作成日時")
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新日時")