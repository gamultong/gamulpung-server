from .base import event, ServerEvent
from event.payload import Empty
from typing import Type
from data.base import DataObj

from dataclasses import dataclass

from data.board import PointRange, Point
from data.cursor import Color
from datetime import datetime


@event
@dataclass
class Error(ServerEvent):
    event_name = "error"

    msg: str


@event
@dataclass
class MyCursor(ServerEvent):
    event_name = "my-cursor"

    id: str


@event
@dataclass
class TilesState(ServerEvent):
    event_name = "tiles-state"

    @dataclass
    class Elem(DataObj):
        range: PointRange
        data: str

    tiles: list[Elem]


@event
@dataclass
class CursorsState(ServerEvent):
    event_name = "cursors-state"

    @dataclass
    class Elem(DataObj):
        id: str
        position: Type[Empty] | Point = Empty
        pointer: Type[Empty] | Point | None = Empty
        color: Type[Empty] | Color = Empty
        revive_at: Type[Empty] | datetime | None = Empty
        score: Type[Empty] | int = Empty

    cursors: list[Elem]


@event
@dataclass
class ScoreboardState(ServerEvent):
    event_name = "scoreboard-state"

    @dataclass
    class Elem(DataObj):
        rank: int
        score: int
        before_rank: Type[Empty] | int

    scores: list[Elem]


@event
@dataclass
class Chat(ServerEvent):
    event_name = "chat"

    @dataclass
    class Elem(DataObj):
        cursor_id: str
        content: str

    chats: list[Elem]


@event
@dataclass
class Explosion(ServerEvent):
    event_name = "explosion"

    position: Point
