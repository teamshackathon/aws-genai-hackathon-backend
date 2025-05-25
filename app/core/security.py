import secrets
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext
from redis import Redis

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """アクセストークンを作成"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """パスワードハッシュを生成"""
    return pwd_context.hash(password)

redis_client = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)

def generate_state_token(session_id: str) -> str:
    """
    OAuth認証用のstateトークンを生成し、Redisに保存
    
    Args:
        session_id: ユーザーのセッションID
        
    Returns:
        生成されたstateトークン
    """
    state = secrets.token_urlsafe(32)
    
    # Redisにstateトークンを保存 (10分間有効)
    key = f"oauth_state:{session_id}"
    redis_client.setex(key, 600, state)
    
    return state

def verify_state_token(session_id: str, state: str) -> bool:
    """
    stateトークンを検証し、使用後に削除
    
    Args:
        session_id: ユーザーのセッションID
        state: 検証するstateトークン
        
    Returns:
        検証結果 (有効な場合True)
    """
    key = f"oauth_state:{session_id}"
    stored_state = redis_client.get(key)
    
    # トークンが存在し、値が一致する場合に検証成功
    if stored_state and stored_state == state:
        # 使用済みトークンを削除（再利用防止）
        redis_client.delete(key)
        return True
    
    return False