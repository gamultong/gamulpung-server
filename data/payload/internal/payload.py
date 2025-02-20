from event.payload import Payload, ParsablePayload

from data.board import Point
from data.cursor import Color

from dataclasses import dataclass
from enum import Enum


class EventEnum(str, Enum):
    ERROR = "error"
    SEND_CHAT = "send-chat"
    CHAT = "chat"
    POINTING = "pointing"
    POINTER_SET = "pointer-set"
    SET_FLAG = "set-flag"
    FLAG_SET = "flag-set"
    OPEN_TILE = "open-tile"
    YOU_DIED = "you-died"
    CURSORS_DIED = "cursors-died"
    SINGLE_TILE_OPENED = "single-tile-opened"
    TILES_OPENED = "tiles-opened"
    MOVING = "moving"
    MOVED = "moved"
    NEW_CONN = "new-conn"
    CURSORS = "cursors"
    MY_CURSOR = "my-cursor"
    CONN_CLOSED = "conn-closed"
    CURSOR_QUIT = "cursor-quit"
    SET_VIEW_SIZE = "set-view-size"
    FETCH_TILES = "fetch-tiles"
    TILES = "tiles"


class ClickType(str, Enum):
    GENERAL_CLICK = "GENERAL_CLICK"
    SPECIAL_CLICK = "SPECIAL_CLICK"


@dataclass
class ErrorPayload(Payload):
    msg: str


@dataclass
class FetchTilesPayload(Payload):
    start_p: ParsablePayload[Point]
    end_p: ParsablePayload[Point]


@dataclass
class TilesPayload(Payload):
    start_p: ParsablePayload[Point]
    end_p: ParsablePayload[Point]
    tiles: str


@dataclass
class SendChatPayload(Payload):
    message: str


@dataclass
class ChatPayload(Payload):
    message: str
    cursor_id: str


@dataclass
class MovingPayload(Payload):
    position: ParsablePayload[Point]


@dataclass
class MovedPayload(Payload):
    id: str
    new_position: ParsablePayload[Point]


@dataclass
class PointingPayload(Payload):
    position: ParsablePayload[Point]
    click_type: ClickType


@dataclass
class PointerSetPayload(Payload):
    id: str
    pointer: ParsablePayload[Point] | None


@dataclass
class SingleTileOpenedPayload(Payload):
    position: ParsablePayload[Point]
    tile: str


@dataclass
class TilesOpenedPayload(Payload):
    start_p: ParsablePayload[Point]
    end_p: ParsablePayload[Point]
    tiles: str


@dataclass
class FlagSetPayload(Payload):
    position: ParsablePayload[Point]
    is_set: bool
    color: Color | None


@dataclass
class NewConnPayload(Payload):
    conn_id: str
    width: int
    height: int


@dataclass
class ConnClosedPayload(Payload):
    pass


@dataclass
class CursorQuitPayload(Payload):
    id: str

@dataclass
class CursorReviveAtPayload(Payload):
    id: str
    position: ParsablePayload[Point]
    pointer: ParsablePayload[Point] | None
    color: Color
    revive_at: str | None


@dataclass
class CursorsPayload(Payload):
    cursors: list[CursorReviveAtPayload]

@dataclass
class MyCursorPayload(Payload):
    id: str
    position: ParsablePayload[Point]
    pointer: ParsablePayload[Point] | None
    color: Color


@dataclass
class YouDiedPayload(Payload):
    revive_at: str

@dataclass
class SetViewSizePayload(Payload):
    width: int
    height: int

@dataclass
class SetFlagPayload(Payload):
    pass

@dataclass
class OpenTilePayload(Payload):
    pass