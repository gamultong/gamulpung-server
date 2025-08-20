from data.base import DataObj
from dataclasses import dataclass
from .point import Point, PointRange
from .tile import Tile


"""
123
456
789
-> 123456789
"""


@dataclass
class Tiles(DataObj):
    # range 추가
    # data에서 Tile접근 가능하게 해야함
    # property로 width, height 하면 편할 듯?
    data: bytearray
    width: int
    height: int

    def at_tile(self, point: Point) -> Tile:
        assert 0 <= point.x <= self.width
        assert 0 <= point.y <= self.height

        idx = (self.height - point.y) - 1
        idx *= self.width
        idx += point.x

        law = self.data[idx]
        tile = Tile.from_int(law)

        return tile

    def at_tiles(self, point_range: PointRange):
        assert 0 <= point_range.top_left.x <= point_range.bottom_right.x <= self.width
        assert 0 <= point_range.bottom_right.y <= point_range.top_left.y <= self.width

        data = bytearray()
        width = point_range.width
        height = point_range.height

        for y in range(height):
            y = self.height - (point_range.top_left.y - y) - 1
            y *= self.width
            x_start = y+point_range.bottom_left.x
            x_end = y+point_range.bottom_right.x
            law = self.data[x_start:x_end+1]

            data += law

        return Tiles(
            data=data,
            width=width,
            height=height
        )

    def update_at(self, point: Point, tile: Tile):
        x, y = point.x, self.height - point.y - 1
        idx = x + (y * self.width)
        self.data[idx] = tile.data

    def to_str(self):
        return self.data.hex()

    def hide_info(self):
        # 불변 객체 반환으로 변경 필요
        """
        타일들의 mine, number 정보를 제거한다.
        타일의 상태가 CLOSED일 때만 해당한다.

        주의: Tiles 데이터가 변형된다.
        """
        opened = 0b10000000
        mask = 0b10111000
        for idx in range(len(self.data)):
            b = self.data[idx]
            if b & opened:
                continue

            b &= mask
            self.data[idx] = b
