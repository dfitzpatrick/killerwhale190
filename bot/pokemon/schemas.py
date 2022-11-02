from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PersistentGuess(BaseModel):
    """Used as a serializable container for persistent views"""
    name: str
    custom_id: str
    guild_id: int
    channel_id: int
    utf_data: str
    message_id: Optional[int] = None
    created: Optional[datetime] = None
    confidence: Optional[float] = None