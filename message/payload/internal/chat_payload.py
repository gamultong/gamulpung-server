from .base_payload import Payload
from dataclasses import dataclass
from enum import Enum


class ChatEvent(str, Enum):
    SEND_CHAT = "send-chat"
    CHAT = "chat"


@dataclass
class SendChatPayload(Payload):
    message: str


@dataclass
class ChatPayload(Payload):
    message: str
    cursor_id: str
