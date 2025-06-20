from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, WithJsonSchema
from pydantic.json_schema import JsonSchemaValue


def validate_object_id(v: Any) -> ObjectId:
    """ObjectId validation function"""
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str):
        if ObjectId.is_valid(v):
            return ObjectId(v)
    raise ValueError('Invalid ObjectId')

def serialize_object_id(v: ObjectId) -> str:
    """ObjectId serialization function"""
    return str(v)

def object_id_json_schema(schema: JsonSchemaValue, model_type: type) -> JsonSchemaValue:
    """JSON schema for ObjectId"""
    schema.update(type='string', format='objectid')
    return schema

# Pydantic v2 compatible ObjectId type
PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(validate_object_id),
    PlainSerializer(serialize_object_id, return_type=str),
    WithJsonSchema(object_id_json_schema),
]

class SessionDocument(BaseModel):
    """MongoDB sessionsコレクション用ドキュメント"""
    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}
    
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id", description="MongoDB ObjectId")
    session_id: str = Field(..., description="ユニークセッションID")
    user_id: Optional[int] = Field(None, description="ユーザーID（PostgreSQL）")
    status: str = Field(default="active", description="active, completed, failed, cancelled")
    url: Optional[str] = Field(None, description="処理対象の動画URL")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    generated_recipe_id: Optional[int] = Field(None, description="生成されたレシピID（PostgreSQL）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="追加メタデータ")

class SessionHistoryMessage(BaseModel):
    """セッション履歴メッセージ"""
    model_config = {"arbitrary_types_allowed": True}
    
    message_id: str = Field(..., description="メッセージのユニークID")
    message_type: str = Field(..., description="user_input, system_response, progress, error")
    content: str = Field(..., description="メッセージ内容")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SessionHistoryDocument(BaseModel):
    """MongoDB session_historyコレクション用ドキュメント"""
    model_config = {"arbitrary_types_allowed": True, "populate_by_name": True}
    
    id: Optional[PyObjectId] = Field(default_factory=ObjectId, alias="_id", description="MongoDB ObjectId")
    session_id: str = Field(..., description="セッションID")
    user_id: Optional[int] = Field(None, description="ユーザーID（PostgreSQL）")
    messages: List[SessionHistoryMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# WebSocket用のスキーマ
class WebSocketMessage(BaseModel):
    """WebSocketメッセージ用スキーマ"""
    type: str = Field(..., description="メッセージタイプ")
    data: Dict[str, Any] = Field(..., description="メッセージデータ")
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None

class WebSocketResponse(BaseModel):
    """WebSocketレスポンス用スキーマ"""
    type: str
    data: Dict[str, Any]
    session_id: str
    timestamp: datetime
    message_id: Optional[str] = None

class SessionCreateRequest(BaseModel):
    """セッション作成リクエスト"""
    user_id: Optional[int] = None
    video_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SessionResponse(BaseModel):
    """セッション情報レスポンス"""
    session_id: str
    user_id: Optional[int] = None
    status: str
    video_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    generated_recipe_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SessionHistoryResponse(BaseModel):
    """セッション履歴レスポンス"""
    session_id: str
    messages: List[SessionHistoryMessage]
    created_at: datetime
    updated_at: datetime
    total_messages: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_messages = len(self.messages)

class SessionListResponse(BaseModel):
    """セッション一覧レスポンス"""
    sessions: List[SessionResponse]
    total: int
    page: int = 1
    per_page: int = 10
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total = len(self.sessions)

class CookingHistoryDocument(BaseModel):
    """MongoDB cooking_historyコレクション用ドキュメント"""
    user_id: Optional[int] = Field(None, description="ユーザーID（PostgreSQL）")
    recipe_id: int = Field(..., description="レシピID（PostgreSQL）")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CookingHistoryRequest(BaseModel):
    """料理履歴追加リクエスト"""
    recipe_id: int = Field(..., description="レシピID（PostgreSQL）")