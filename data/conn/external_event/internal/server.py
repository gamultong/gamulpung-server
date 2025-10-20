from .base import ServerPayload
from core.event.frame import Empty
from typing import Type
from data.base import DataObj
from data.board import PointRange, Point
from data.cursor import Color
from datetime import datetime


class Error(ServerPayload):
    msg: str


class MyCursor(ServerPayload):
    id: str


class TilesState(ServerPayload):
    class Elem(DataObj):
        range: PointRange
        data: str

    tiles: list[Elem]


class CursorsState(ServerPayload):
    class Elem(DataObj):
        id: str
        position: Type[Empty] | Point = Empty
        pointer: Type[Empty] | Point | None = Empty
        color: Type[Empty] | Color = Empty
        revive_at: Type[Empty] | datetime | None = Empty
        score: Type[Empty] | int = Empty

    cursors: list[Elem]


class ScoreboardState(ServerPayload):
    class Elem(DataObj):
        rank: int
        score: int
        before_rank: Type[Empty] | int

    scores: list[Elem]


class Chat(ServerPayload):
    class Elem(DataObj):
        cursor_id: str
        content: str

    chats: list[Elem]


class Explosion(ServerPayload):
    position: Point
