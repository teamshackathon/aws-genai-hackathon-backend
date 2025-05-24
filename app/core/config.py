import os
from typing import Any, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "BAE-RECIPE API"
    API_V1_STR: str = "/api/v1"
    
    # 環境設定
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # データベース設定
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "bae_recipe")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
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