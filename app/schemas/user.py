from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, computed_field


class UserBase(BaseModel):
    """ユーザーのベーススキーマ"""
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    """パスワードありユーザー作成スキーマ"""
    email: EmailStr
    name: str
    password: str

class UserOAuthCreate(UserBase):
    """OAuth経由のユーザー作成スキーマ"""
    email: EmailStr
    oauth_provider: str
    oauth_id: str
    # GitHub情報
    github_username: Optional[str] = None
    github_avatar_url: Optional[str] = None
    # Google情報
    google_picture: Optional[str] = None
    google_verified_email: Optional[bool] = None


class UserUpdate(UserBase):
    """ユーザー更新スキーマ"""
    password: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None


class UserInDBBase(UserBase):
    """データベース内のユーザー情報"""
    id: int
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    github_username: Optional[str] = None
    github_avatar_url: Optional[str] = None
    google_picture: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_date: datetime
    updated_date: datetime
    serving_size: Optional[int]
    salt_preference: Optional[str]
    sweetness_preference: Optional[str]
    spiciness_preference: Optional[str]
    cooking_time_preference: Optional[str]
    meal_purpose: Optional[str]
    disliked_ingredients: Optional[str]
    preference_trend: Optional[str]

    class Config:
        from_attributes = True


class User(UserInDBBase):
    """APIレスポンス用ユーザースキーマ"""
    pass

class UserMe(BaseModel):
    """ログインユーザー自身の情報スキーマ（限定フィールド）"""
    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    profile_image_url: Optional[str] = None  # 元のフィールド
    github_avatar_url: Optional[str] = None  # 元のフィールド
    google_picture: Optional[str] = None     # 元のフィールド
    last_login: Optional[datetime] = None
    bio: Optional[str] = None
    serving_size: Optional[int]
    salt_preference: Optional[str]
    sweetness_preference: Optional[str]
    spiciness_preference: Optional[str]
    cooking_time_preference: Optional[str]
    meal_purpose: Optional[str]
    disliked_ingredients: Optional[str]
    preference_trend: Optional[str]

    class Config:
        from_attributes = True
    
    @computed_field
    @property
    def avatar_url(self) -> Optional[str]:
        """アバター画像URLを返す"""
        if self.profile_image_url:
            return self.profile_image_url
        elif self.github_avatar_url:
            return self.github_avatar_url
        elif self.google_picture:
            return self.google_picture
        return None

class Token(BaseModel):
    """アクセストークンスキーマ"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    """トークンペイロードスキーマ"""
    sub: Optional[int] = None  # subject (user id)
    exp: Optional[int] = None