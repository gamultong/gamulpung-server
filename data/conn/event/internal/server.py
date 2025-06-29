from .base import event, ServerEvent
from event.payload import Empty
from data.base import DataObj

from dataclasses import dataclass
from typing import Type

from data.board import PointRange, Point
from data.cursor import Color
from datetime import datetime


@event
class Error(ServerEvent):
    event_name = "error"

    msg: str


@event
class MyCursor(ServerEvent):
    event_name = "my-cursor"

    id: str


@event
class TilesState(ServerEvent):
    event_name = "tiles-state"

    @dataclass
    class Elem(DataObj):
        range: PointRange
        data: str

    tiles: list[Elem]


@event
class CursorsState(ServerEvent):
    event_name = "cursors-state"

    @dataclass
    class Elem(DataObj):
        id: str
        position: Type[Empty] | Point
        pointer: Type[Empty] | Point | None
        color: Type[Empty] | Color
        revive_at: Type[Empty] | datetime | None
        score: Type[Empty] | int

    cursors: list[Elem]


@event
class ScoreboardState(ServerEvent):
    event_name = "scoreboard-state"

    @dataclass
    class Elem(DataObj):
        rank: int
        score: int
        before_rank: Type[Empty] | int

    scores: list[Elem]


@event
class Chat(ServerEvent):
    event_name = "chat"

    @dataclass
    class Elem(DataObj):
        cursor_id: str
        content: str

    chats: list[Elem]


@event
class Explosion(ServerEvent):
    event_name = "explosion"

    position: Point
