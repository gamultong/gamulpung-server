from data.board import Point
from dataclasses import dataclass
from .base_payload import Payload
from .parsable_payload import ParsablePayload
from enum import Enum


class TilesEvent(str, Enum):
    FETCH_TILES = "fetch-tiles"
    TILES = "tiles"


@dataclass
class FetchTilesPayload(Payload):
    start_p: ParsablePayload[Point]
    end_p: ParsablePayload[Point]


@dataclass
class TilesPayload(Payload):
    start_p: ParsablePayload[Point]
    end_p: ParsablePayload[Point]
    tiles: str
