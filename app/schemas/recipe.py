from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------
# ExternalService スキーマ
# ---------------
class ExternalServiceBase(BaseModel):
    """外部サービスの基本スキーマ"""
    services_name: str = Field(..., description="サービス名")


class ExternalServiceCreate(ExternalServiceBase):
    """外部サービス作成スキーマ"""
    pass


class ExternalServiceUpdate(BaseModel):
    """外部サービス更新スキーマ"""
    services_name: Optional[str] = Field(None, description="サービス名")


class ExternalService(ExternalServiceBase):
    """外部サービス応答スキーマ"""
    id: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


# ---------------
# RecipeStatus スキーマ
# ---------------
class RecipeStatusBase(BaseModel):
    """レシピステータスの基本スキーマ"""
    status: str = Field(..., description="ステータス名")


class RecipeStatusCreate(RecipeStatusBase):
    """レシピステータス作成スキーマ"""
    pass


class RecipeStatusUpdate(BaseModel):
    """レシピステータス更新スキーマ"""
    status: Optional[str] = Field(None, description="ステータス名")


class RecipeStatus(RecipeStatusBase):
    """レシピステータス応答スキーマ"""
    id: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


# ---------------
# Ingredient スキーマ
# ---------------
class IngredientBase(BaseModel):
    """材料の基本スキーマ"""
    ingredient: str = Field(..., description="材料名")
    amount: Optional[str] = Field(None, description="量（単位付き）")


class IngredientCreate(IngredientBase):
    """材料作成スキーマ"""
    ingredient: Optional[str] = Field(None, description="材料名")
    amount: Optional[str] = Field(None, description="量（単位付き）")


class IngredientUpdate(BaseModel):
    """材料更新スキーマ"""
    ingredient: Optional[str] = Field(None, description="材料名")
    amount: Optional[str] = Field(None, description="量（単位付き）")
    updated_date: Optional[datetime] = datetime.utcnow()



class Ingredient(IngredientBase):
    """材料応答スキーマ"""
    id: int
    recipe_id: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


# ---------------
# Process スキーマ
# ---------------
class ProcessBase(BaseModel):
    """調理工程の基本スキーマ"""
    process_number: int = Field(..., description="手順番号")
    process: str = Field(..., description="手順")


class ProcessCreate(ProcessBase):
    """調理工程作成スキーマ"""
    created_date: Optional[datetime] = datetime.utcnow()
    updated_date: Optional[datetime] = datetime.utcnow()


class ProcessUpdate(BaseModel):
    """調理工程更新スキーマ"""
    process_number: Optional[int] = Field(None, description="手順番号")
    process: Optional[str] = Field(None, description="手順")


class Process(ProcessBase):
    """調理工程応答スキーマ"""
    id: int
    recipe_id: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


# ---------------
# Recipe スキーマ
# ---------------
class RecipeBase(BaseModel):
    """レシピの基本スキーマ"""
    recipe_name: str = Field(..., description="料理名")
    url: Optional[str] = Field(None, description="抽出元URL")
    keyword: Optional[str] = Field(None, description="検索キーワード")
    genrue: Optional[str] = Field(None, description="ジャンル")



class RecipeCreate(RecipeBase):
    """レシピ作成スキーマ"""
    status_id: int = Field(1, description="ステータスID（デフォルトは「生成前」）")
    external_service_id: Optional[int] = Field(None, description="抽出元サービスID")
    created_date: Optional[datetime] = datetime.utcnow()
    updated_date: Optional[datetime] = datetime.utcnow()


class RecipeUpdate(BaseModel):
    """レシピ更新スキーマ"""
    recipe_name: Optional[str] = Field(None, description="料理名")
    status_id: Optional[int] = Field(None, description="ステータスID")
    external_service_id: Optional[int] = Field(None, description="抽出元サービスID")
    url: Optional[str] = Field(None, description="抽出元URL")


class RecipeInDBBase(RecipeBase):
    """データベース内のレシピ基本スキーマ"""
    id: int
    status_id: int
    external_service_id: Optional[int] = None
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


class Recipe(RecipeInDBBase):
    """レシピ応答基本スキーマ"""
    pass


# ---------------
# 高度なレシピスキーマ
# ---------------
class RecipeDetail(Recipe):
    """詳細なレシピ情報（材料・手順・ステータス・外部サービス情報を含む）"""
    status: RecipeStatus
    external_service: Optional[ExternalService] = None
    ingredients: List[Ingredient] = []
    processes: List[Process] = []

    class Config:
        from_attributes = True


# ---------------
# レシピ作成用の複合スキーマ
# ---------------
class RecipeWithDetailsCreate(RecipeCreate):
    """材料と手順を含むレシピ作成スキーマ"""
    ingredients: List[IngredientCreate] = []
    processes: List[ProcessCreate] = []


# ---------------
# UserRecipe スキーマ (中間テーブル用)
# ---------------
class UserRecipeBase(BaseModel):
    """ユーザーレシピ関連の基本スキーマ"""
    user_id: int = Field(..., description="ユーザーID")
    recipe_id: int = Field(..., description="レシピID")
    is_favorite: bool = Field(False, description="お気に入りフラグ")
    note: Optional[str] = Field(None, description="ユーザーのメモ")
    rating: Optional[int] = Field(None, ge=1, le=5, description="ユーザー評価（1〜5）")


class UserRecipeCreate(UserRecipeBase):
    """ユーザーレシピ関連作成スキーマ"""
    pass


class UserRecipeUpdate(BaseModel):
    """ユーザーレシピ関連更新スキーマ"""
    is_favorite: Optional[bool] = Field(None, description="お気に入りフラグ")
    note: Optional[str] = Field(None, description="ユーザーのメモ")
    rating: Optional[int] = Field(None, ge=1, le=5, description="ユーザー評価（1〜5）")
    updated_date: Optional[datetime] = datetime.utcnow()


class UserRecipe(UserRecipeBase):
    """ユーザーレシピ関連応答スキーマ"""
    id: int
    created_date: datetime
    updated_date: datetime

    class Config:
        from_attributes = True


# ---------------
# レシピ検索・フィルタリング用スキーマ
# ---------------
class RecipeFilter(BaseModel):
    """レシピ検索条件スキーマ"""
    keyword: Optional[str] = None
    status_id: Optional[int] = None
    external_service_id: Optional[int] = None
    user_id: Optional[int] = None
    favorites_only: bool = False
    page: int = 1
    per_page: int = 20


# ---------------
# レシピ一覧用の応答スキーマ
# ---------------
class RecipeList(BaseModel):
    """レシピ一覧応答スキーマ"""
    items: List[Recipe]
    total: int
    page: int
    per_page: int
    pages: int

class VoiceReaderInput(BaseModel):
    """Input schema for voice chat"""

    text: str = Field(..., description="Text to be converted to speech")