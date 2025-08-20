from data.board import PointRange, Tiles, Point
from handler.board import Section, Config


class BoardHandler:
    section_dict: dict[Point, Section] = {}

    @staticmethod
    async def fetch(point_range: PointRange):
        # 반환할 데이터 공간 미리 할당
        out_width = point_range.width
        out_height = point_range.height
        top, bottom = point_range.top_left.y, point_range.bottom_right.y,
        left, right = point_range.top_left.x, point_range.bottom_right.x
        out = bytearray(out_width * out_height)

        for y in range(top // Config.LENGHT, bottom // Config.LENGHT - 1, -1):
            for x in range(left // Config.LENGHT, bottom // Config.LENGHT + 1):
                sec = section_dict[Point(x, y)]

        return Tiles(out, out_width, out_height)
