# models.py
from pydantic import BaseModel
from typing import Literal
from uuid import uuid4
from time import time


MessageRole = Literal["user", "bot"]


class Message(BaseModel):
    id: str
    role: MessageRole = "bot"
    content: str
    timestamp: int


class MessagePayload(BaseModel):
    message: Message
    selectedList: list[str]


def make_bot_reply(text: str) -> Message:
    """Упаковываем ответ парсера в такую же структуру Message."""
    return Message(
        id=str(uuid4()),
        role="bot",
        content=text,
        timestamp=int(time() * 1000),
    )