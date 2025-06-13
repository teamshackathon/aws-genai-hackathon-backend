from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.db.base_class import Base


class ExternalService(Base):
    """外部サービスモデル"""
    __tablename__ = "external_services"
    
    id = Column(Integer, primary_key=True, index=True)
    services_name = Column(String(256), nullable=False, unique=True, comment="サービス名")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # リレーションシップ
    # recipes = relationship("Recipe", back_populates="external_service")
    
    def __repr__(self):
        return f"<ExternalService(id={self.id}, name={self.services_name})>"


class RecipeStatus(Base):
    """レシピステータスモデル"""
    __tablename__ = "recipe_status"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(100), nullable=False, comment="ステータス名")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # # リレーションシップ
    # recipes = relationship("Recipe", back_populates="status")
    
    def __repr__(self):
        return f"<RecipeStatus(id={self.id}, status={self.status})>"


class Recipe(Base):
    """レシピ基本情報モデル"""
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    status_id = Column(Integer, ForeignKey("recipe_status.id"), nullable=False)
    external_service_id = Column(Integer, ForeignKey("external_services.id"), nullable=True, comment="抽出元サービスID")
    url = Column(String(512), nullable=True, comment="抽出元URL")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    recipe_name = Column(String(256), nullable=False, comment="料理名")
    
    # リレーションシップ
    # status = relationship("RecipeStatus", back_populates="recipes")
    # external_service = relationship("ExternalService", back_populates="recipes")
    
    # 拡張リレーションシップ
    # ingredients = relationship("Ingredient", back_populates="recipe", cascade="all, delete-orphan")
    # processes = relationship("Process", back_populates="recipe", cascade="all, delete-orphan")
    # user_recipes = relationship("UserRecipe", back_populates="recipe", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Recipe(id={self.id}, name={self.recipe_name})>"


class Ingredient(Base):
    """材料リストモデル"""
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    ingredient = Column(String(256), nullable=False, comment="材料名")
    amount = Column(String(100), nullable=True, comment="量（単位付き）")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # リレーションシップ
    # recipe = relationship("Recipe", back_populates="ingredients")
    
    def __repr__(self):
        return f"<Ingredient(id={self.id}, ingredient={self.ingredient}, amount={self.amount})>"


class Process(Base):
    """調理工程モデル"""
    __tablename__ = "processes"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    process_number = Column(Integer, nullable=False, comment="手順番号")
    process = Column(Text, nullable=False, comment="手順")
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # リレーションシップ
    # recipe = relationship("Recipe", back_populates="processes")
    
    __table_args__ = (
        UniqueConstraint("recipe_id", "process_number", name="uq_recipe_process_number"),
    )
    
    def __repr__(self):
        return f"<Process(id={self.id}, recipe_id={self.recipe_id}, number={self.process_number})>"