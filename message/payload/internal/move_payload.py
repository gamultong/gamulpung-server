from board.data import Point
from cursor.data import Color
from dataclasses import dataclass
from .base_payload import Payload
from .parsable_payload import ParsablePayload
from enum import Enum


class MoveEvent(str, Enum):
    MOVING = "moving"
    MOVED = "moved"
    CHECK_MOVABLE = "check-movable"
    MOVABLE_RESULT = "movable-result"


@dataclass
class MovingPayload(Payload):
    position: ParsablePayload[Point]


@dataclass
class MovedPayload(Payload):
    id: str
    new_position: ParsablePayload[Point]


@dataclass
class CheckMovablePayload(Payload):
    position: ParsablePayload[Point]


@dataclass
class MovableResultPayload(Payload):
    position: ParsablePayload[Point]
    movable: bool
