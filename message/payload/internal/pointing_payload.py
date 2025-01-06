from .parsable_payload import ParsablePayload
from .base_payload import Payload
from board.data import Point
from dataclasses import dataclass
from cursor.data import Color
from enum import Enum


class PointEvent(str, Enum):
    POINTING = "pointing"
    TRY_POINTING = "try-pointing"
    POINTING_RESULT = "pointing-result"
    POINTER_SET = "pointer-set"


class ClickType(str, Enum):
    GENERAL_CLICK = "GENERAL_CLICK"
    SPECIAL_CLICK = "SPECIAL_CLICK"


@dataclass
class PointingPayload(Payload):
    position: ParsablePayload[Point]
    click_type: ClickType


@dataclass
class TryPointingPayload(Payload):
    cursor_position: ParsablePayload[Point]
    color: Color
    new_pointer: ParsablePayload[Point]
    click_type: ClickType


@dataclass
class PointingResultPayload(Payload):
    pointer: ParsablePayload[Point]
    pointable: bool


@dataclass
class PointerSetPayload(Payload):
    id: str
    pointer: ParsablePayload[Point] | None
