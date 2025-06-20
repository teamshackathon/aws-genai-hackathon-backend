from pydantic import BaseModel, Field


class BaseInput(BaseModel):
    """Base input schema for all chains"""

    pass


class BaseOutput(BaseModel):
    """Base output schema for all chains"""

    pass

class VoiceRecognitionOutput(BaseOutput):
    """Input schema for voice recognition chain"""

    status: str = Field(...,
        description="The status of the voice recognition command, e.g., 'next', 'previous', 'play', or 'None'"
    )