from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class UserRecipe(Base):
    """ユーザーとレシピの中間テーブルモデル"""
    __tablename__ = "user_recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    
    # 追加のユーザー関連情報（オプション）
    is_favorite = Column(Boolean, default=False, comment="お気に入りフラグ")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # リレーションシップ
    # user = relationship("Users", back_populates="user_recipes")
    # recipe = relationship("Recipe", back_populates="user_recipes")
    
    def __repr__(self):
        return f"<UserRecipe(id={self.id}, user_id={self.user_id}, recipe_id={self.recipe_id})>"