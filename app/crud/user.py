from datetime import datetime
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import Users
from app.schemas.user import UserCreate, UserOAuthCreate, UserUpdate


def get(db: Session, user_id: int) -> Optional[Users]:
    """
    IDでユーザーを取得
    """
    return db.query(Users).filter(Users.id == user_id).first()


def update(db: Session, *, db_obj: Users, obj_in: Union[UserUpdate, Dict[str, Any]]) -> Users:
    """
    ユーザー情報を更新
    """
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)
        
    if update_data.get("password"):
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
        
    for field in update_data:
        if hasattr(db_obj, field):
            setattr(db_obj, field, update_data[field])
            
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_multi(db: Session, *, skip: int = 0, limit: int = 100) -> list[Users]:
    """
    複数ユーザーを取得
    """
    return db.query(Users).offset(skip).limit(limit).all()

def get_by_email(db: Session, *, email: str) -> Optional[Users]:
    """メールアドレスでユーザーを取得"""
    return db.query(Users).filter(Users.email == email).first()


def get_by_oauth_id(db: Session, *, provider: str, oauth_id: str) -> Optional[Users]:
    """OAuth IDでユーザーを取得"""
    return db.query(Users).filter(
        Users.oauth_provider == provider,
        Users.oauth_id == oauth_id
    ).first()


def create(db: Session, *, obj_in: UserCreate) -> Users:
    """パスワード認証ユーザーを作成"""
    db_obj = Users(
        email=obj_in.email,
        name=obj_in.name,
        hashed_password=get_password_hash(obj_in.password),
        is_active=True,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def create_oauth_user(db: Session, *, obj_in: UserOAuthCreate) -> Users:
    """OAuthユーザーを作成"""
    db_obj = Users(
        email=obj_in.email,
        name=obj_in.name,
        oauth_provider=obj_in.oauth_provider,
        oauth_id=obj_in.oauth_id,
        github_username=obj_in.github_username,
        github_avatar_url=obj_in.github_avatar_url,
        google_picture=obj_in.google_picture,
        google_verified_email=obj_in.google_verified_email,
        is_active=True,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def authenticate(db: Session, *, email: str, password: str) -> Optional[Users]:
    """パスワード認証"""
    user = get_by_email(db, email=email)
    if not user:
        return None
    if not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_login_time(db: Session, *, user: Users) -> Users:
    """最終ログイン日時を更新"""
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_refresh_token(db: Session, *, user: Users, 
                         token: Optional[str], expires: Optional[datetime]) -> Users:
    """リフレッシュトークンを更新"""
    user.refresh_token = token
    user.token_expires = expires
    db.add(user)
    db.commit()
    db.refresh(user)
    return user