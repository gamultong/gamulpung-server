from dataclasses import dataclass
from .base_payload import Payload
from enum import Enum


class ErrorEvent(str, Enum):
    ERROR = "error"


@dataclass
class ErrorPayload(Payload):
    msg: str
