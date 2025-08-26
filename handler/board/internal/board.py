from data.board import PointRange, Tiles, Point
from .section import Section, Config

from handler.storage.interface import KeyValueInterface
from handler.storage.dict import DictSpace

# section 좌표 기준으로 절대 좌표가 어디에 존재하는지 분석


def point_set(abs_point, section_point):
    result = abs_point - (section_point * Config.LENGTH)

    if result > Config.LENGTH - 1:
        result = Config.LENGTH - 1
    elif result < 0:
        result = 0

    return result


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

        top = point_range.top_left.y
        bottom = point_range.bottom_right.y
        left = point_range.top_left.x
        right = point_range.bottom_right.x

        section_top = top // Config.LENGTH
        section_bottom = bottom // Config.LENGTH
        section_left = left // Config.LENGTH
        section_right = right // Config.LENGTH

        result = Tiles(bytearray(), out_width, 0)

        # top -> bottom 탐색
        for y in range(section_top, section_bottom - 1, -1):
            out_top = point_set(top, y)
            out_bottom = point_set(bottom, y)

            h_tiles = Tiles(
                bytearray(),
                0,
                abs(out_top-out_bottom) + 1
            )

            # left -> right 탐색
            for x in range(section_left, section_right + 1):
                out_left = point_set(left, x)
                out_right = point_set(right, x)

                out_point_range = PointRange(
                    Point(out_left, out_top), Point(out_right, out_bottom)
                )

                sec = BoardHandler.section_dict[Point(x, y)]

                out_tiles = sec.tiles.at_tiles(out_point_range)
                h_tiles = h_merge_tiles(h_tiles, out_tiles)

            result = v_merge_tiles(result, h_tiles)

        assert result.width == out_width
        assert result.height == out_height

        return result
