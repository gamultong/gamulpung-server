from .base_payload import Payload
from .parsable_payload import ParsablePayload
from .new_conn_payload import CursorInfoPayload
from board.data import Point, Tile
from cursor.data import Color
from dataclasses import dataclass
from enum import Enum


class InteractionEvent(str, Enum):
    YOU_DIED = "you-died"
    CURSORS_DIED = "cursors-died"
    SINGLE_TILE_OPENED = "single-tile-opened"
    TILES_OPENED = "tiles-opened"
    FLAG_SET = "flag-set"


@dataclass
class YouDiedPayload(Payload):
    revive_at: str


@dataclass
class CursorsDiedPayload(Payload):
    revive_at: str
    cursors: list[CursorInfoPayload]


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
