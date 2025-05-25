import os
from typing import Any, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "BAE-RECIPE API"
    API_V1_STR: str = "/api/v1"
    
    # 環境設定
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # JWT認証
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-for-development")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))  # 1日

    # OAuth設定
    GITHUB_CLIENT_ID: Optional[str] = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: Optional[str] = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI: Optional[str] = os.getenv("GITHUB_REDIRECT_URI")

    GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: Optional[str] = os.getenv("GOOGLE_REDIRECT_URI")

    FRONTEND_REDIRECT_URL: Optional[str] = os.getenv("FRONTEND_REDIRECT_URL", "http://localhost:3000/bae-recipe")
    
    # データベース設定
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "bae_recipe")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    # Redis設定
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        
        # 環境に基づいてDBのURIを設定
        if self.ENVIRONMENT == "production":
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        else:
            # 開発環境ではSQLiteも使用可能
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
            # または: self.SQLALCHEMY_DATABASE_URI = "sqlite:///./test.db"
            
    class Config:
        case_sensitive = True

settings = Settings()