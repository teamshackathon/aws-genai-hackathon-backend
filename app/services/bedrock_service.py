import logging

from app.core.aws.bedrock_client import BedrockClient
from app.core.llm.chain.voice_recognition_chain import VoiceRecognitionChain
from app.schemas.base import VoiceRecognitionOutput

logger = logging.getLogger(__name__)

class BedrockService:
    """Amazon Bedrockサービスを利用するためのクラス"""

    def __init__(self, bedrock_client: BedrockClient):
        self.bedrock_client = bedrock_client.get_client()
        self.chain = VoiceRecognitionChain(chat_llm=self.bedrock_client)

    async def invoke(self, input: str, **kwargs) -> VoiceRecognitionOutput:
        """音声認識チェーンを呼び出して応答を得る

        Args:
            input: 音声認識されたテキスト
            **kwargs: その他のキーワード引数

        Returns:
            チェーンの応答
        """
        try:
            response = self.chain.invoke(input, **kwargs)
            return VoiceRecognitionOutput(**response)
        except Exception as e:
            logging.error(f"Error invoking Bedrock service: {str(e)}")
            return VoiceRecognitionOutput(status="error", message=str(e))
