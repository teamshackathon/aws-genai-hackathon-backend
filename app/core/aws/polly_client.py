import boto3
from fastapi import HTTPException
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings


class PollyClient:
    """Amazon Pollyクライアント"""

    def __init__(self):
        self.client = self._initialize_client()

    def _initialize_client(self):
        """Amazon Pollyクライアントを初期化"""
        try:
            return boto3.client(
                'polly',
                region_name='ap-northeast-1',  # 東京リージョン
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to initialize Amazon Polly service: {str(e)}"
            )

    def get_client(self) -> BaseChatModel:
        """Pollyクライアントを取得"""
        return self.client