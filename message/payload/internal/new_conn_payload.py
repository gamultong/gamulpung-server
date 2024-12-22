from board.data import Point
from cursor.data import Color
from dataclasses import dataclass
from .base_payload import Payload
from .parsable_payload import ParsablePayload
from enum import Enum


class NewConnEvent(str, Enum):
    NEW_CONN = "new-conn"
    NEW_CURSOR_CANDIDATE = "new-cursor-candidate"
    CURSORS = "cursors"
    MY_CURSOR = "my-cursor"
    CONN_CLOSED = "conn-closed"
    CURSOR_QUIT = "cursor-quit"
    SET_VIEW_SIZE = "set-view-size"


@dataclass
class NewConnPayload(Payload):
    conn_id: str
    width: int
    height: int


@dataclass
class NewCursorCandidatePayload(Payload):
    conn_id: str
    width: int
    height: int
    position: ParsablePayload[Point]


@dataclass
class CursorPayload(Payload):
    position: ParsablePayload[Point]
    pointer: ParsablePayload[Point] | None
    color: Color


@dataclass
class CursorsPayload(Payload):
    cursors: list[CursorPayload]


class MyCursorPayload(CursorPayload):
    pass


@dataclass
class ConnClosedPayload(Payload):
    pass


@dataclass
class CursorQuitPayload(CursorPayload):
    pass


@dataclass
class SetViewSizePayload(Payload):
    width: int
    height: int
