from data.board import Point, PointRange, Tile, Tiles
from handler.board import Section
from data.cursor import Color

from handler.board import BoardHandler

POINT = Point(0, 0)
POINTRANGE = PointRange(POINT, POINT)

__default_tile = Tile(
    is_open=False,
    is_mine=False,
    is_flag=False,
    color=Color.BLUE,
    number=None
)

CLOSE_TILE = __default_tile.copy()

OPEN_TILE = __default_tile.copy()
OPEN_TILE.is_open = True

FLAG_ON_TILE = __default_tile.copy()
FLAG_ON_TILE.is_flag = True


def get_sec(tile: Tile):
    return Section(
        point=POINT,
        tiles=Tiles(
            data=bytearray([tile.data]),
            width=1,
            height=1
        )
    )


def setup_sec(sec: Section):
    BoardHandler.section_dict = {
        sec.point: sec
    }
