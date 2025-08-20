from data.board import Point, PointRange, Tiles
from dataclasses import dataclass


MINE_TILE = 0b01000000
NUM_MASK = 0b00000111


class Config:
    LENGHT = 100
    MINE_RATIO = 0.3


def point_abs_to_relate(abs_p: Point):
    return Point(abs_p.x % Config.LENGHT, abs_p.y % Config.LENGHT)


def point_range_abs_to_relate(abs_pr: PointRange):
    return PointRange(
        point_abs_to_relate(abs_pr.top_left),
        point_abs_to_relate(abs_pr.bottom_right)
    )


@dataclass
class Section():
    point: Point
    tiles: Tiles
    # 00000000 -> 상 하 좌 우 좌상 좌하 우상 우하
    flag: int = 0

    @property
    def abs_range(self):
        return PointRange(
            Point((self.point.x+1) * Config.LENGHT, self.point.y * Config.LENGHT),
            Point(self.point.x * Config.LENGHT, (self.point.y+1) * Config.LENGHT)
        )

    def fetch(self, range: PointRange):
        range = point_range_abs_to_relate(range)
        return self.tiles.at_tiles(range).copy()
