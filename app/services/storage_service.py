from typing import Any, Dict, List

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageService:
    """S3/MinIO互換のストレージサービス
    
    開発環境ではMinIO、本番環境ではAWS S3を利用するためのサービス。
    aioboto3を使用して非同期処理に対応しています。
    """
    
    def __init__(self):
        self.session = aioboto3.Session(
            aws_access_key_id=settings.MINIO_ACCESS_KEY_ID,
            aws_secret_access_key=settings.MINIO_SECRET_ACCESS_KEY,
        )
        self.bucket_name = settings.STORAGE_BUCKET_NAME
        self.endpoint_url = settings.MINIO_ENDPOINT_URL

    async def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """指定したプレフィックス以下のファイル一覧を取得
        
        Args:
            prefix: 検索するプレフィックス (例: "users/avatars/")
            
        Returns:
            List[Dict[str, Any]]: ファイル情報のリスト
        """
        async with self.session.client('s3', endpoint_url=self.endpoint_url) as minio:
            response = await minio.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            if 'Contents' not in response:
                return []
                
            result = []
            for item in response["Contents"]:
                url = f"{self.endpoint_url}/{self.bucket_name}/{item['Key']}"
                    
                result.append({
                    "key": item["Key"],
                    "size": item["Size"],
                    "last_modified": item["LastModified"],
                    "url": url
                })
            return result
        
    async def download_file(self, path: str) -> bytes:
        """ファイルをダウンロードする
        
        Args:
            path: ファイルのパス
            
        Returns:
            bytes: ファイルの内容
            
        Raises:
            ClientError: ファイルが見つからない、またはアクセスできない場合
        """
        async with self.session.client('s3', endpoint_url=self.endpoint_url) as s3:
            try:
                response = await s3.get_object(Bucket=self.bucket_name, Key=path)
                async with response['Body'] as stream:
                    return await stream.read()
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                if error_code == 'NoSuchKey':
                    raise FileNotFoundError(f"File not found: {path}")
                raise