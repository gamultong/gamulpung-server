from data.board import PointRange, Tiles, Point
from handler.board import Section, Config

def point_set(length: int, coordinate:int):
    if coordinate > length - 1:
        coordinate =  length - 1
    elif coordinate < 0:
        coordinate = 0
    return coordinate


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
            out_top = point_set(Config.LENGHT, top - y * out_width)
            out_bottom = point_set(Config.LENGHT, bottom - y * out_width)
            for x in range(left // Config.LENGHT, right // Config.LENGHT + 1):
                sec = BoardHandler.section_dict[Point(x, y)]

                out_left = point_set(Config.LENGHT, left - x * out_width)
                out_right = point_set(Config.LENGHT, right - x * out_width)

                out_point_range = PointRange(
                    Point(out_left, out_top), Point(out_right, out_bottom)
                )

                out_tiles = sec.tiles.at_tiles(out_point_range)
                out += out_tiles.data

        return Tiles(out, out_width, out_height)
