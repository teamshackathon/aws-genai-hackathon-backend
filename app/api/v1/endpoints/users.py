from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.crud import user as crud
from app.schemas.user import User

router = APIRouter()

@router.get("", response_model=List[User])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    複数ユーザーを取得
    """
    users = crud.get_multi(db, skip=skip, limit=limit)
    return users