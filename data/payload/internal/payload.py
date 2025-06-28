from typing import Generic, TypeVar

from dataclasses import dataclass
from event.payload import Payload

from data.base import DataObj
from enum import Enum

DATA_TYPE = TypeVar(
    "DATA_TYPE",
    bound=DataObj
)


class EventEnum(str, Enum):
    pass


@dataclass
class DataPayload(Generic[DATA_TYPE], Payload):
    id: str
    data: DATA_TYPE | None = None
