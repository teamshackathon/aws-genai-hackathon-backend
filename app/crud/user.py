from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.user import Users
from app.schemas.user import UserCreate, UserUpdate


def get(db: Session, user_id: int) -> Optional[Users]:
    """IDでユーザーを取得"""
    return db.query(Users).filter(Users.id == user_id).first()


def get_by_name(db: Session, name: str) -> Optional[Users]:
    """名前でユーザーを取得"""
    return db.query(Users).filter(Users.name == name).first()


def get_multi(db: Session, skip: int = 0, limit: int = 100) -> List[Users]:
    """複数ユーザーを取得"""
    return db.query(Users).offset(skip).limit(limit).all()


def create(db: Session, *, obj_in: UserCreate) -> Users:
    """ユーザーを作成"""
    db_obj = Users(name=obj_in.name)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, *, db_obj: Users, obj_in: UserUpdate) -> Users:
    """ユーザーを更新"""
    if obj_in.name is not None:
        db_obj.name = obj_in.name
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def remove(db: Session, *, user_id: int) -> Users:
    """ユーザーを削除"""
    obj = db.query(Users).get(user_id)
    db.delete(obj)
    db.commit()
    return obj