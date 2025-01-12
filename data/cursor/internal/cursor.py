from data.base import DataObj

from data.board import Point
from .color import Color
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Cursor(DataObj):
    conn_id: str
    position: Point
    pointer: Point | None
    color: Color
    width: int
    height: int
    _revive_at: datetime | None = None

    @property
    def id(self) -> str:
        return self.conn_id

    @property
    def revive_at(self) -> datetime | None:
        if (self._revive_at is not None) and (self._revive_at <= datetime.now()):
            self._revive_at = None

        return self._revive_at

    @revive_at.setter
    def revive_at(self, v: datetime) -> None:
        self._revive_at = v

    def set_size(self, width: int, height: int):
        self.width = width
        self.height = height

    def check_in_view(self, p: Point):
        leftmost = self.position.x - self.width
        rightmost = self.position.x + self.width
        top = self.position.y + self.height
        bottom = self.position.y - self.height

        return \
            p.x >= leftmost and p.x <= rightmost and \
            p.y >= bottom and p.y <= top

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
