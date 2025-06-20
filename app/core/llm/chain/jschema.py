# 次へ進む、前へ戻る、音声を再生の3つのstatusを持つJSchemaクラス
STATUS_SCHEMA = """{
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["next", "previous", "play", "None"]
        }
    },
    "required": ["status"]
}"""