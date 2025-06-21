from typing import List, Optional
from pydantic import BaseModel, Field


class RecipeParameters(BaseModel):
    """レシピ生成パラメータのスキーマ"""

    people_count: Optional[int] = Field(None, alias="peopleCount", ge=1, le=20, description="人数 (1-20)")
    cooking_time: Optional[str] = Field(None, alias="cookingTime", description="調理時間 (例: '30分', '1時間')")
    preference: Optional[str] = Field(None, description="重視する傾向 (例: 'ヘルシー', '簡単', '本格的')")
    saltiness: Optional[int] = Field(None, ge=1, le=5, description="塩味の強さ (1-5)")
    sweetness: Optional[int] = Field(None, ge=1, le=5, description="甘味の強さ (1-5)")
    spiciness: Optional[int] = Field(None, ge=1, le=5, description="辛味の強さ (1-5)")
    disliked_ingredients: Optional[List[str]] = Field(None, alias="dislikedIngredients", description="嫌いな食材のリスト")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            # 必要に応じてカスタムエンコーダーを追加
        }

    def to_dict(self) -> dict:
        """辞書形式で返す（Noneの値は除外）"""
        return {k: v for k, v in self.dict(by_alias=True, exclude_none=True).items()}
