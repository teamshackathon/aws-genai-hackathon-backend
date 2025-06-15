import logging
import uuid
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketConnectionManager:
    """WebSocket接続管理クラス（複数接続対応）"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}           # connection_id -> websocket
        self.session_connections: Dict[str, Set[str]] = {}           # session_id -> set of connection_ids

    async def connect(self, websocket: WebSocket, session_id: str) -> str:
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
        self.session_connections[session_id].add(connection_id)
        logger.info(f"WebSocket connected: {self.session_connections[session_id]}")
        return connection_id

    def disconnect(self, connection_id: str, session_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(connection_id)
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]

    async def send_personal_message(self, message: dict, session_id: str):
        """特定セッションに属するすべての接続へ送信"""
        connection_ids = self.session_connections.get(session_id, set())
        disconnected_ids = set()
        for conn_id in connection_ids:
            ws = self.active_connections.get(conn_id)
            logger.info(f"Sending message to {session_id} via connection {conn_id}")
            if ws:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.info(f"Failed to send message to {session_id}: {e}")
                    disconnected_ids.add(conn_id)
        # 切断された接続をクリーンアップ
        for conn_id in disconnected_ids:
            self.disconnect(conn_id, session_id)
        return len(connection_ids) > 0

    def is_session_connected(self, session_id: str) -> bool:
        return session_id in self.session_connections and bool(self.session_connections[session_id])

    def get_connected_sessions(self) -> list:
        return list(self.session_connections.keys())

# グローバルインスタンス
ws_manager = WebSocketConnectionManager()
