from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base_class import Base


class Users(Base):
    """ユーザーモデル"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # 基本情報
    name = Column(String, index=True, unique=True, nullable=True)  # ユーザー名
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)  # パスワード認証用
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # OAuth関連情報
    oauth_provider = Column(String, nullable=True)  # "google", "github" などの認証プロバイダ
    oauth_id = Column(String, nullable=True, index=True)  # OAuth プロバイダでのユーザーID
    
    # GitHub固有のフィールド
    github_username = Column(String, nullable=True)
    github_avatar_url = Column(String, nullable=True)
    
    # Google固有のフィールド
    google_picture = Column(String, nullable=True)
    google_verified_email = Column(Boolean, nullable=True)
    
    # プロフィール情報
    bio = Column(Text, nullable=True)
    profile_image_url = Column(String, nullable=True)
    
    # タイムスタンプ
    created_date = Column(DateTime, default=func.now(), nullable=False)
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # 認証トークン (リフレッシュトークンなどの保存用)
    refresh_token = Column(String, nullable=True)
    token_expires = Column(DateTime, nullable=True)

    # 追加のフィールド
    serving_size = Column(Integer, nullable=True, default=1, comment="食べる人数")
    salt_preference = Column(String, nullable=True, default="normal", comment="塩分の好み（low, normal, high）")
    sweetness_preference = Column(String, nullable=True, default="normal", comment="甘さの好み（low, normal, high）")
    spiciness_preference = Column(String, nullable=True, default="normal", comment="辛さの好み（low, normal, high）")
    cooking_time_preference = Column(String, nullable=True, default="30分以内", comment="調理時間の好み")
    meal_purpose = Column(String, nullable=True, default="", comment="食事の目的（breakfast, lunch, dinner, snack）")
    disliked_ingredients = Column(Text, nullable=True, comment="嫌いな食材（カンマ区切り）")
    preference_trend = Column(Text, nullable=True, comment="好みの傾向")

    @property
    def display_name(self):
        """表示用の名前を返す"""
        if self.name:
            return self.name
        elif self.github_username:
            return self.github_username
        elif self.email:
            return self.email.split('@')[0]
        return f"User {self.id}"
    
    @property
    def avatar_url(self):
        """アバター画像URLを返す"""
        if self.profile_image_url:
            return self.profile_image_url
        elif self.github_avatar_url:
            return self.github_avatar_url
        elif self.google_picture:
            return self.google_picture
        return None
    
    def is_oauth_user(self):
        """OAuthユーザーかどうかを判定"""
        return bool(self.oauth_provider and self.oauth_id)
    
    @property
    def favorite_recipes(self):
        """ユーザーのお気に入りレシピを取得"""
        return [user_recipe.recipe for user_recipe in self.user_recipes if user_recipe.is_favorite]
