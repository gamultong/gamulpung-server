from data.board import PointRange, Tiles, Point
from .section import Section, Config

from handler.storage.interface import KeyValueInterface
from handler.storage.dict import DictSpace

# section 좌표 기준으로 절대 좌표가 어디에 존재하는지 분석


def abs_to_rel(abs_point: Point, section_point: Point):
    def abs_to_rel_int(abs: int, sec: int):
        res = abs - (sec * Config.LENGTH)
        if res > Config.LENGTH - 1:
            res = Config.LENGTH - 1
        elif res < 0:
            res = 0
        return res

    return Point(
        abs_to_rel_int(abs_point.x, section_point.x),
        abs_to_rel_int(abs_point.y, section_point.y)
    )


def abs_to_sec(abs_point: Point):
    return Point(
        abs_point.x // Config.LENGTH,
        abs_point.y // Config.LENGTH
    )


def h_merge_tiles(left_tiles: Tiles, right_tiles: Tiles):
    assert left_tiles.height == right_tiles.height

    data = bytearray()
    for i in range(left_tiles.height):
        left_index = left_tiles.width * i
        left_index_end = left_index + left_tiles.width
        left_data = left_tiles.data[left_index:left_index_end]

        right_index = right_tiles.width * i
        right_index_end = right_index + right_tiles.width
        right_data = right_tiles.data[right_index:right_index_end]

        data += (left_data + right_data)

    return Tiles(
        data=data,
        width=left_tiles.width+right_tiles.width,
        height=left_tiles.height
    )


def v_merge_tiles(top_tile: Tiles, bottom_tile: Tiles):
    assert top_tile.width == bottom_tile.width

    data = top_tile.data + bottom_tile.data

    return Tiles(
        data=data,
        width=top_tile.width,
        height=top_tile.height+bottom_tile.height
    )


class BoardHandler:
    """
    Method 
    - fetch(PointRange) -> Tiles

    - open_tiles(Point)
    - togle_flag(Point)
    """
    section_dict: dict[Point, Section] = {}

    @staticmethod
    async def fetch(point_range: PointRange):
        # 반환할 데이터 공간 미리 할당
        out_width = point_range.width
        out_height = point_range.height

        section_top_left = abs_to_sec(point_range.top_left)
        section_bottom_right = abs_to_sec(point_range.bottom_right)

        section_top = section_top_left.y
        section_bottom = section_bottom_right.y
        section_left = section_top_left.x
        section_right = section_bottom_right.x

        result = Tiles(bytearray(), out_width, 0)

        # top -> bottom 탐색
        for y in range(section_top, section_bottom - 1, -1):
            h_tiles: Tiles | None = None

            # left -> right 탐색
            for x in range(section_left, section_right + 1):
                sec_point = Point(x, y)

                out_point_range = PointRange(
                    abs_to_rel(point_range.top_left, sec_point),
                    abs_to_rel(point_range.bottom_right, sec_point)
                )
                sec = BoardHandler.section_dict[Point(x, y)]

                out_tiles = sec.tiles.at_tiles(out_point_range)
                if h_tiles is None:
                    h_tiles = out_tiles
                else:
                    h_tiles = h_merge_tiles(h_tiles, out_tiles)

            assert h_tiles
            result = v_merge_tiles(result, h_tiles)

        assert result.width == out_width
        assert result.height == out_height

        return result

    @staticmethod
    async def togle_flag(point: Point):
        sec_p = abs_to_sec(point)
        rel_p = abs_to_rel(point, sec_p)

        section = BoardHandler.section_dict[sec_p]
        tile = section.tiles.at_tile(rel_p)

        if tile.is_open:
            return

        tile.is_flag = not tile.is_flag

        section.tiles.update_at(rel_p, tile)

    @staticmethod
    async def open_tiles(point: Point):
        sec_p = abs_to_sec(point)
        rel_p = abs_to_rel(point, sec_p)

        section = BoardHandler.section_dict[sec_p]
        tile = section.tiles.at_tile(rel_p)

        if tile.is_open:
            return

        if tile.is_flag:
            return

        tile.is_open = True

        section.tiles.update_at(rel_p, tile)
