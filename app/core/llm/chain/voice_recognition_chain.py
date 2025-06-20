import json
import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

from app.core.llm.chain.base import BaseChain
from app.core.llm.chain.jschema import STATUS_SCHEMA


class VoiceRecognitionChain(BaseChain):
    """音声認識したテキストをLLMに渡して応答を得るチェーン"""

    def __init__(self, chat_llm: BaseChatModel):
        self.chat_llm = chat_llm
        self.prompt = PromptTemplate(
            input_variables=["input", "schema"],
            template='''以下は、ユーザーが音声で発した言葉を文字列として渡したものです。このコマンドが以下のいずれかに該当するかを判定してください：

・「次へ」「次に進む」「進め」「次」など → "next"
・「前に戻る」「戻して」「前へ」など → "previous"
・「再生して」「音声を再生」「聴かせて」など → "play"
・どれにも該当しない場合は "None" としてください。

入力: """
{input}
"""

- 出力形式は必ず **以下の JSON スキーマ形式のみ** に従ってください。
- **テキスト出力や説明文、Markdownは絶対に含めないでください。**
- JSON 以外の文字を含むとエラーとなります。

出力形式："""
{schema}
"""
'''
        )

        self.chain = self.prompt | self.chat_llm | StrOutputParser() | RunnableLambda(self.replaced2json)

    def get_prompt(self, input: str, **kwargs) -> PromptTemplate:

        formatted_input = {"input": input, "schema": STATUS_SCHEMA}

        return self.prompt.invoke(formatted_input, **kwargs).to_string()
    
    def invoke(self, input: str, **kwargs) -> Any:
        """Invoke the chain with given input

        Args:
            input: Input text to be processed by the chain
            **kwargs: Additional keyword arguments

        Returns:
            Processed output from the chain
        """
        formatted_input = {"input": input, "schema": STATUS_SCHEMA}

        response = self.chain.invoke(formatted_input, **kwargs)

        print(f"ChatChain response: {response}")

        return json.loads(response)

    @staticmethod
    def replaced2json(output: str) -> str:
        replaced_output = output.replace('```json', '').replace('```', '')
        # 正規表現を使って空白行（改行だけや空白のみの行）を削除
        replaced_output = re.sub(r'^\s*\n', '', replaced_output, flags=re.MULTILINE)
        # 正規表現を使って最後のカンマを削除
        replaced_output = re.sub(r',\s*$', '', replaced_output)
        # replaced_output = json.loads(replaced_output) # これを加えるとdict型になってしまう
        return replaced_output