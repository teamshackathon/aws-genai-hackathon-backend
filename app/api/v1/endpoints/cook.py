import asyncio
import logging
from typing import List, Optional

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorDatabase
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_mongodb
from app.core.aws.bedrock_client import BedrockClient
from app.core.websocket_manager import ws_manager
from app.schemas.mongo import CookingHistoryDocument, CookingHistoryRequest
from app.services.bedrock_service import BedrockService
from app.services.mongodb_cooking_service import MongoDBCookingService

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter()

def get_bedrock_client():
    """
    Amazon Bedrockクライアントの依存関係を取得します。
    """
    try:
        return BedrockClient()
    except Exception as e:
        logger.error(f"Bedrock Client initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Bedrock Client initialization failed: {str(e)}"
        )

def get_transcribe_client():
    """
    Amazon Transcribeクライアントの依存関係を取得します。
    """
    try:
        return TranscribeStreamingClient(
            region='ap-northeast-1',  # 東京リージョン
        )
    except Exception as e:
        logger.error(f"Transcribe Client initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcribe Client initialization failed: {str(e)}"
        )

def get_cooking_service(mongodb: AsyncIOMotorDatabase = Depends(get_mongodb)) -> MongoDBCookingService:
    """
    MongoDBの料理サービスの依存関係を取得します。
    """
    try:
        return MongoDBCookingService(mongodb=mongodb)
    except Exception as e:
        logger.error(f"MongoDB Cooking Service initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"MongoDB Cooking Service initialization failed: {str(e)}"
        )
    
def get_bedrock_service(
        bedrock_client: BedrockClient = Depends(get_bedrock_client)
):
    """
    Amazon Bedrockサービスの依存関係を取得します。
    """
    try:
        return BedrockService(bedrock_client=bedrock_client)
    except Exception as e:
        logger.error(f"Bedrock Service initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Bedrock Service initialization failed: {str(e)}"
        )

@router.post("", response_model=CookingHistoryDocument)
async def add_cooking_history(
    input_data: CookingHistoryRequest,
    current_user = Depends(get_current_user),
    service: MongoDBCookingService = Depends(get_cooking_service)
) -> CookingHistoryDocument:
    """
    料理履歴を追加します。
    """
    try:
        history = await service.add_cooking_history(user_id=current_user.id, recipe_id=input_data.recipe_id)
        return history
    except Exception as e:
        logger.error(f"Failed to add cooking history for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add cooking history: {str(e)}"
        )
    
@router.get("/history/{recipe_id}", response_model=List[CookingHistoryDocument])
async def get_cooking_history(
    recipe_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    service: MongoDBCookingService = Depends(get_cooking_service)
) -> List[CookingHistoryDocument]:
    """
    ユーザーの料理履歴を取得します。
    """
    try:
        history = await service.get_cooking_history(user_id=current_user.id, recipe_id=recipe_id)
        return history
    except Exception as e:
        logger.error(f"Failed to get cooking history for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cooking history: {str(e)}"
        )

@router.websocket("/ws")
async def cook_conversation(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="Authentication token for the user"),
    mongodb: AsyncIOMotorDatabase = Depends(get_mongodb),
    db: Session = Depends(get_db),
    bedrock_service: BedrockService = Depends(get_bedrock_service),
    transcribe_client: TranscribeStreamingClient = Depends(get_transcribe_client),
):
    logger.info("WebSocket connection established")

    CHUNK_SIZE = 1024
    INACTIVITY_TIMEOUT = 10

    try:
        # MongoDB初期化
        cooking_service = MongoDBCookingService(mongodb=mongodb)

        # トークンの検証
        user = None
        if token:
            try:
                user = get_current_user(db=db, token=token)
                logger.info(f"User authenticated: {user.id}")
            except Exception as e:
                logger.error(f"Authentication failed: {str(e)}")
                await websocket.close(code=1008, reason="Invalid authentication token")
                return
        else:
            logger.warning("No authentication token provided")
            await websocket.close(code=1008, reason="Authentication token is required")
            return

        # セッションの作成
        try:
            current_session = await cooking_service.create_session(user_id=user.id)
            session_id = current_session.session_id
            logger.info(f"Session created: {current_session.session_id}")
        except Exception as e:
            logger.error(f"Error creating session: {str(e)}")
            await websocket.close(code=1011, reason="Session creation error")
            return

        connection_id = await ws_manager.connect(websocket, session_id)
        logger.info(f"WebSocket connected: connection_id={connection_id}, session_id={session_id}")

        audio_queue = asyncio.Queue()
        stream = None
        stream_active = False

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive(), timeout=INACTIVITY_TIMEOUT)
                if "bytes" in data:
                    audio_bytes = data["bytes"]

                    # ストリームが閉じられている場合は再接続
                    if not stream_active:
                        stream = await transcribe_client.start_stream_transcription(
                            language_code='ja-JP',
                            media_encoding='pcm',
                            media_sample_rate_hz=16000,
                        )
                        transcription_task = asyncio.create_task(handle_transcription(stream, audio_queue))
                        logger.info("Started new Transcribe stream")
                        logger.info("Create Task for transcription handler")
                        stream_active = True

                    # チャンクサイズに分割して送信
                    for i in range(0, len(audio_bytes), CHUNK_SIZE):
                        chunk = audio_bytes[i:i + CHUNK_SIZE]
                        await stream.input_stream.send_audio_event(audio_chunk=chunk)

                    # キューから文字起こし結果を取得
                    transcript_text = await audio_queue.get()
                    logger.info(f"Transcripted: {transcript_text}")

                    if transcript_text != "":
                        # 文字起こしをBedrockに送信
                        response = await bedrock_service.invoke(input=transcript_text)
                        logger.info(f"Bedrock response: {response}")
                        transcript_text = None

                        await ws_manager.send_personal_message(
                            {
                                "status": response.status,
                            },
                            session_id=session_id,
                        )

            except asyncio.TimeoutError:
                # タイムアウトが発生した場合、ストリームを閉じる
                if stream_active:
                    await stream.input_stream.end_stream()
                    stream_active = False
                    logger.info("Closed Transcribe stream due to inactivity")
                    stream = None

            except WebSocketDisconnect:
                logger.info("WebSocket connection closed by client")
                break

            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                break

        # クリーンアップ
        if stream_active:
            await stream.input_stream.end_stream()
        if transcription_task:
            transcription_task.cancel()
        await ws_manager.disconnect(websocket, session_id)
        await cooking_service.delete_session(session_id)
        await websocket.close(code=1000, reason="Normal closure")

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed by client")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        try:
            if stream_active:
                await stream.input_stream.end_stream()
        except Exception as e:
            logger.error(f"Error ending Transcribe stream: {str(e)}")
        try:
            if transcription_task:
                transcription_task.cancel()
        except Exception as e:
            logger.error(f"Error cancelling transcription task: {str(e)}")
        try:
            await ws_manager.disconnect(websocket, session_id)
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {str(e)}")
        try:
            await cooking_service.delete_session(session_id)
        except Exception as e:
            logger.error(f"Error deleting session: {str(e)}")
        try:
            await websocket.close(code=1000, reason="Normal closure")
        except Exception as e:
            logger.error(f"Error closing WebSocket: {str(e)}")

async def handle_transcription(audio_stream, queue):
    """
    Amazon Transcribe からの文字起こし結果を処理し、キューに追加する。
    """
    class MyHandler(TranscriptResultStreamHandler):
        async def handle_transcript_event(self, transcript_event):
            results = transcript_event.transcript.results
            for result in results:
                if result.is_partial:
                    continue
                for alt in result.alternatives:
                    transcript_text = alt.transcript
                    logger.info(f"Transcript: {transcript_text}")
                    await queue.put(transcript_text)


    handler = MyHandler(audio_stream.output_stream)
    try:
        await handler.handle_events()
    except asyncio.CancelledError:
        logger.info("Transcription task was cancelled")
    finally:
        logger.info("Transcription stream ended")