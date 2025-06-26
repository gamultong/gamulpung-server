from data.base import DomainObj
from data.base.utils import HaveId, Relation

from data.board import Point, PointRange
from .color import Color
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVarTuple, Unpack

Ts = TypeVarTuple("Ts") 

@dataclass
class Cursor(DomainObj[Unpack[Ts]], HaveId[str]):
    conn_id: str
    position: Point
    pointer: Point | None
    color: Color
    width: int
    height: int
    revive_at: datetime | None = None

    class Watchers(Relation[str]): pass
    
    class Targets(Relation[str]): pass

    @property
    def id(self) -> str:
        return self.conn_id

    def set_size(self, width: int, height: int):
        self.width = width
        self.height = height

    def check_in_view(self, p: Point):
        return self.view_range.is_in(p)

    def check_interactable(self, p: Point) -> bool:
        """
        p가 커서의 인터랙션 범위에 포함되는지 확인한다.
        인터랙션 가능하면 True.
        """
        return \
            p.x >= self.position.x - 1 and \
            p.x <= self.position.x + 1 and \
            p.y >= self.position.y - 1 and \
            p.y <= self.position.y + 1

    @property
    def view_range(self) -> PointRange:
        top = self.position.y + self.height
        bottom = self.position.y - self.height
        left = self.position.x - self.width
        right = self.position.x + self.width

        return PointRange(
            top_left=Point(left, top),
            bottom_right=Point(right, bottom)
        )

    @staticmethod
    def create(conn_id: str):
        return Cursor(
            conn_id=conn_id,
            position=Point(0, 0),
            pointer=None,
            color=Color.get_random(),
            width=0,
            height=0
        )
