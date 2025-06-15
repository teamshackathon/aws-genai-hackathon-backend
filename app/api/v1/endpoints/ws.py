import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.api import deps
from app.core.websocket_manager import ws_manager
from app.models.recipe import Ingredient, Process, Recipe
from app.models.user import Users
from app.models.user_recipe import UserRecipe
from app.schemas.mongo import WebSocketMessage
from app.services.mongodb_recipe_generation_service import MongoDBRecipeGenerationService
from app.services.recipe_service import RecipeService
from app.services.redis_queue_service import RedisQueueService

logger = logging.getLogger(__name__)

router = APIRouter()

def get_redis_queue_service(
        redis_client: Redis = Depends(deps.get_redis)
):
    """
    Redisキューサービスの依存関係を取得します。
    """
    try:
        return RedisQueueService(redis_client=redis_client)
    except Exception as e:
        logger.error(f"Redisキューサービスの初期化に失敗しました: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Redisキューサービスの初期化に失敗しました: {str(e)}"
        )
    
def get_recipe_service(db: Session = Depends(deps.get_db)) -> RecipeService:
    """
    レシピサービスの依存関係を取得します。
    """
    try:
        return RecipeService(db=db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"レシピサービスの初期化に失敗しました: {str(e)}"
        )


@router.get("/my-session")
async def get_my_session(
    current_user: Users =Depends(deps.get_current_user),
    mongodb: AsyncIOMotorDatabase = Depends(deps.get_mongodb)
):
    """
    現在のユーザーのWebSocketのセッション情報を取得するエンドポイント
    """
    logger.info(f"Fetching session for user: {current_user.id}")

    mongo_service = MongoDBRecipeGenerationService(mongodb)
    
    try:
        session = await mongo_service.get_user_sessions(current_user.id)
        if not session:
            logger.warning(f"No active session found for user: {current_user.id}")
            return None
        
        logger.info(f"Session found for user {current_user.id}: {session.session_id}")
        return session
    
    except Exception as e:
        logger.error(f"Error retrieving session for user {current_user.id}: {str(e)}")
        return None

@router.websocket("/recipe-gen")
async def recipe_gen(
    websocket: WebSocket,
    session_id: Optional[str] = Query(None, description="Session ID for the recipe generation"),
    token: Optional[str] = Query(None, description="Authentication token for the user"),
    url: Optional[str] = Query(None, description="URL of the video to process"),
    mongodb: AsyncIOMotorDatabase = Depends(deps.get_mongodb),
    db: Session = Depends(deps.get_db),
    redis_queue_service: RedisQueueService = Depends(get_redis_queue_service)
):
    """
    レシピ生成のWebSocketエンドポイント
    """
    logger.warning(f"WebSocket connection request: session_id={session_id}, url={url}")

    # await websocket.accept()
    
    try:
        mongo_service = MongoDBRecipeGenerationService(mongodb)

        # トークンの検証
        user = None
        if token:
            try:
                user = deps.get_current_user(db=db, token=token)
                logger.info(f"User authenticated: {user.id}")
            except Exception as e:
                logger.error(f"Authentication failed: {str(e)}")
                await websocket.close(code=1008, reason="Invalid authentication token")
                return
        else:
            logger.warning("No authentication token provided")
            await websocket.close(code=1008, reason="Authentication token is required")
            return

        # セッションの処理
        current_session = None
        is_fast_connect = False
        if session_id and session_id != "":
            # 既存セッションの検証
            try:
                existing_session = await mongo_service.get_session(session_id)
                if not existing_session:
                    logger.warning(f"Session not found: {session_id}")
                    await websocket.close(code=1008, reason="Invalid session ID")
                    return
                current_session = existing_session
                logger.info(f"Using existing session: {session_id}")
            except Exception as e:
                logger.error(f"Error retrieving session: {str(e)}")
                await websocket.close(code=1011, reason="Session retrieval error")
                return
        else:
            # 新しいセッションを作成
            try:
                is_fast_connect = True
                current_session = await mongo_service.create_session(user_id=user.id)
                session_id = current_session.session_id
                logger.info(f"Created new session: {session_id}")
            except Exception as e:
                logger.error(f"Error creating session: {str(e)}")
                await websocket.close(code=1011, reason="Session creation error")
                return

        # WebSocket接続をマネージャーに登録
        connection_id = await ws_manager.connect(websocket, session_id)
        logger.info(f"WebSocket connected: connection_id={connection_id}, session_id={session_id}")

        # セッション履歴を送信
        await send_session_history(websocket, mongo_service, session_id)

        if is_fast_connect:
            # 接続確立メッセージを送信
            await ws_manager.send_personal_message({
                "type": "connection_established",
                "data": {
                    "content": "BAE-RECIPE AIにて動画からレシピを生成します。",
                    "session_id": session_id,
                    "connection_id": connection_id,
                    "status": current_session.status,
                },
                "timestamp": datetime.utcnow().isoformat()
            }, session_id)
        
            # 接続をログに記録
            await mongo_service.add_message_to_history(
                session_id=session_id,
                message_type="system_response",
                content="BAE-RECIPE AIにて動画からレシピを生成します。",
                metadata={"connection_id": connection_id, "user_id": user.id}
            )

            task_id = await redis_queue_service.enqueue_recipe_generation_task(
                session_id=session_id,
                url=url,
                user_id=user.id
            )

            await ws_manager.send_personal_message({
                "type": "system_response",
                "data": {
                    "content": "BAE-RECIPE AIにて動画からレシピを開始します。",
                    "session_id": session_id,
                    "task_id": task_id,
                },
                "timestamp": datetime.utcnow().isoformat()
            }, session_id)

            # タスクIDをセッションに保存
            await mongo_service.add_message_to_history(
                session_id=session_id,
                message_type="system_response",
                content="BAE-RECIPE AIにて動画からレシピを開始します。",
                metadata={
                    "connection_id": connection_id,
                    "user_id": user.id,
                    "task_id": task_id
                }
            )
        else:
            # 既存セッションの接続確立メッセージを送信
            await ws_manager.send_personal_message({
                "type": "connection_established",
                "data": {
                    "content": "BAE-RECIPE AIに再接続します。",
                    "session_id": session_id,
                    "connection_id": connection_id,
                    "status": current_session.status,
                },
                "timestamp": datetime.utcnow().isoformat()
            }, session_id)

            # 接続をログに記録
            await mongo_service.add_message_to_history(
                session_id=session_id,
                message_type="system_response",
                content="BAE-RECIPE AIに再接続します。",
                metadata={"connection_id": connection_id, "user_id": user.id}
            )

        # メッセージループ
        while True:
            try:
                raw_data = await websocket.receive_text()
                logger.info(f"Received message: {raw_data}")

                try:
                    message_data = json.loads(raw_data)
                    logger.info(f"Parsed message data: {message_data}")
                    ws_message = WebSocketMessage(**message_data)
                    logger.info(f"Parsed WebSocket message: {ws_message}")
                    
                    # メッセージを履歴に保存
                    # message_id = await mongo_service.add_message_to_history(
                    #     session_id=session_id,
                    #     message_type="user_input",
                    #     content=ws_message.data.get("content", raw_data),
                    #     metadata={
                    #         "message_type": ws_message.type,
                    #         "raw_data": message_data,
                    #         "user_id": user.id
                    #     }
                    # )
                    
                    # エコーレスポンス（実際の処理に置き換える）
                    # await send_response(websocket, mongo_service, session_id, "message_received", {
                    #     "message_id": message_id,
                    #     "content": ws_message.data.get("content", raw_data)
                    # })
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {str(e)}")
                    await send_error_message(websocket, mongo_service, session_id, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Message processing error: {str(e)}")
                    await send_error_message(websocket, mongo_service, session_id, f"Message processing error: {str(e)}")
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session: {session_id}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception as e:
            logger.error(f"Error closing WebSocket: {str(e)}")
    finally:
        # クリーンアップ処理
        try:
            if 'connection_id' in locals() and 'session_id' in locals():
                ws_manager.disconnect(connection_id, session_id)
                if 'mongo_service' in locals():
                    await mongo_service.add_message_to_history(
                        session_id=session_id,
                        message_type="system_response",
                        content="接続が切断されました。",
                        metadata={"connection_id": connection_id}
                    )
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

@router.websocket("/recipe-gen/celery")
async def recipe_gen_celery(
    websocket: WebSocket,
    session_id: Optional[str] = Query(None, description="Session ID for the recipe generation"),
    mongodb: AsyncIOMotorDatabase = Depends(deps.get_mongodb),
    recipe_service: RecipeService = Depends(get_recipe_service),
):
    """
    Celery接続用のWebSocketエンドポイント
    """
    logger.warning(f"WebSocket connection request: session_id={session_id}")

    if session_id is None or session_id == "":
        logger.error("Session ID is required for Celery WebSocket connection")
        await websocket.close(code=1008, reason="Session ID is required")
        return
    
    mongo_service = MongoDBRecipeGenerationService(mongodb)
    
    try:
        existing_session = await mongo_service.get_session(session_id)
        if not existing_session:
            logger.error(f"Session not found: {session_id}")
            await websocket.close(code=1008, reason="Invalid session ID")
            return
    except Exception as e:
        logger.error(f"Error retrieving session: {str(e)}")
        await websocket.close(code=1011, reason="Session retrieval error")  
        return
    
    # WebSocket接続をマネージャーに登録
    connection_id = await ws_manager.connect(websocket, session_id)
    logger.info(f"WebSocket connected: connection_id={connection_id}, session_id={session_id}")

    # celeryからのメッセージ受信ループ
    try:
        while True:
            raw_data = await websocket.receive_text()
            logger.info(f"Received message: {raw_data}")

            try:
                message_data = json.loads(raw_data)
                logger.info(f"Parsed message data: {message_data}")

                # Celeryからのメッセージをセッション履歴に保存
                await mongo_service.add_message_to_history(
                    session_id=session_id,
                    message_type="system_response",
                    content=message_data.get("content", raw_data),
                    metadata={
                        "raw_data": message_data,
                        "connection_id": connection_id
                    }
                )

                # メッセージをWebSocketで送信
                await ws_manager.send_personal_message(message_data, session_id)

                if message_data.get("type") == "task_completed":


                    # レシピの作成
                    results = message_data.get("data", {}).get("result", {})
                    logger.info(f"Processing task completed results: {results}")
                    if results:
                        
                        recipe = await recipe_service.create_recipe(
                            Recipe(
                                recipe_name=results.get("recipes", {}).get("recipe_name", "No Recipe Name"),
                                url=results.get("recipes", {}).get("url", ""),
                                status_id=1,  # デフォルトステータスは「生成後」
                                external_service_id=results.get("recipes", {}).get("external_service_id", None)
                            )
                        )

                        logger.info(f"Recipe created: {recipe.id}")

                        user_recipe = await recipe_service.create_user_recipe(
                            UserRecipe(
                                user_id=results.get("user_recipes", {}).get("user_id", None),
                                recipe_id=recipe.id,
                                is_favorite=False  # デフォルトはお気に入りではない
                            )
                        )

                        logger.info(f"UserRecipe created: {user_recipe.id}")

                        # 材料の作成
                        ingredients = await recipe_service.create_ingredients(
                            [Ingredient(
                                recipe_id=recipe.id,
                                ingredient=ing.get("ingredient", ""),
                                amount=ing.get("amount", ""),
                            ) for ing in results.get("ingredients", [])]
                        )

                        logger.info(f"Ingredients created: {[ing.id for ing in ingredients]}")

                        # 調理手順の作成
                        processes = await recipe_service.create_processes(
                            [Process(
                                recipe_id=recipe.id,
                                process=proc.get("process", ""),
                                process_number=proc.get("process_number", "")
                            ) for proc in results.get("processes", [])]
                        )

                        logger.info(f"Processes created: {[proc.id for proc in processes]}")

                    await mongo_service.delete_session(session_id)


            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Invalid JSON format"},
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Message processing error: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Message processing error: {str(e)}"},
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        ws_manager.disconnect(connection_id, session_id)
    finally:
        # クリーンアップ処理
        try:
            if 'connection_id' in locals() and 'session_id' in locals():
                ws_manager.disconnect(connection_id, session_id)
                if 'mongo_service' in locals():
                    await mongo_service.add_message_to_history(
                        session_id=session_id,
                        message_type="system_response",
                        content="Celery接続が切断されました。",
                        metadata={"connection_id": connection_id}
                    )
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

async def send_session_history(websocket: WebSocket, mongo_service: MongoDBRecipeGenerationService, session_id: str):
    """セッション履歴を送信"""
    try:
        messages = await mongo_service.get_session_messages(session_id)
        
        if messages:
            history_response = {
                "type": "session_history",
                "data": {
                    "messages": [
                        {
                            "message_id": msg.message_id,
                            "type": msg.message_type,
                            "content": msg.content,
                            "metadata": msg.metadata,
                            "timestamp": msg.timestamp.isoformat()
                        }
                        for msg in messages
                    ]
                },
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send_json(history_response)
            logger.info(f"Sent session history for session: {session_id}")
    except Exception as e:
        logger.error(f"Error sending session history: {str(e)}")

async def send_response(
    websocket: WebSocket, 
    mongo_service: MongoDBRecipeGenerationService,
    session_id: str, 
    message_type: str, 
    data: dict
):
    """レスポンスメッセージを送信"""
    try:
        response = {
            "type": message_type,
            "data": data,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # メッセージを送信
        if await ws_manager.send_personal_message(response, session_id):
            # 送信成功時は履歴に保存
            await mongo_service.add_message_to_history(
                session_id=session_id,
                message_type="system_response",
                content=f"Sent {message_type}",
                metadata={"response_data": data}
            )
            logger.info(f"Sent response: {message_type} to session: {session_id}")
    except Exception as e:
        logger.error(f"Error sending response: {str(e)}")

async def send_error_message(
    websocket: WebSocket, 
    mongo_service: MongoDBRecipeGenerationService,
    session_id: str, 
    error_message: str
):
    """エラーメッセージを送信"""
    await send_response(websocket, mongo_service, session_id, "error", {
        "message": error_message,
        "timestamp": datetime.utcnow().isoformat()
    })