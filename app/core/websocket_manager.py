import uuid
from typing import Dict

from fastapi import WebSocket


class WebSocketConnectionManager:
    """WebSocket接続管理クラス"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_id
    
    async def connect(self, websocket: WebSocket, session_id: str) -> str:
        """WebSocket接続を受け入れ"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        self.session_connections[session_id] = connection_id
        return connection_id

    async def add_connection(self, websocket: WebSocket, session_id: str) -> str:
        """WebSocket接続を追加"""
        connection_id = await self.connect(websocket, session_id)
        return connection_id
    
    def disconnect(self, connection_id: str, session_id: str):
        """WebSocket接続を切断"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if session_id in self.session_connections:
            del self.session_connections[session_id]
    
    async def send_personal_message(self, message: dict, session_id: str):
        """特定のセッションにメッセージを送信"""
        connection_id = self.session_connections.get(session_id)
        if connection_id and connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                print(f"Failed to send message to session {session_id}: {e}")
                # 接続が無効になった場合はクリーンアップ
                self.disconnect(connection_id, session_id)
                return False
        return False
    
    def is_session_connected(self, session_id: str) -> bool:
        """セッションが接続中かどうかを確認"""
        connection_id = self.session_connections.get(session_id)
        return connection_id and connection_id in self.active_connections
    
    def get_connected_sessions(self) -> list:
        """接続中のセッション一覧を取得"""
        return list(self.session_connections.keys())

# グローバルインスタンス
ws_manager = WebSocketConnectionManager()