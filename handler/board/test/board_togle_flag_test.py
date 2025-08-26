"""
close tile에만 깃발 꽂기 가능
깃발 있으면 삭제 
"""
from data.board import Tile, Tiles, Point, PointRange
from data.cursor import Color
from handler.board import Section, BoardHandler

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call
from tests.utils import PathPatch, cases, override, MockSet, Wrapper as Wp


OPEN_TILE = Tile(
    is_open=True,
    is_mine=False,
    is_flag=False,
    color=Color.BLUE,
    number=None
)
OPEN_SEC = Section(
    point=Point(0, 0),
    tiles=Tiles(
        data=bytearray([OPEN_TILE.data]),
        width=1,
        height=1
    )
)

CLOSE_TILE = Tile(
    is_open=False,
    is_mine=False,
    is_flag=False,
    color=Color.BLUE,
    number=None
)
CLOSE_SEC = Section(
    point=Point(0, 1),
    tiles=Tiles(
        data=bytearray([CLOSE_TILE.data]),
        width=1,
        height=1
    )
)

patch = PathPatch("handler.board.internal.board")


class BoardHandler_TestCase(AsyncTestCase):
    def setUp(self) -> None:
        BoardHandler.section_dict = {
            OPEN_SEC.point: OPEN_SEC,
            CLOSE_SEC.point: CLOSE_SEC
        }

    @patch("Config")
    def test_togle_flag_opened(self, config):
        config.LENGTH = 1
        await BoardHandler.togle_flag(
            Point(0, 0)
        )
        await BoardHandler.togle_flag(
            Point(0, 1)
        )

        opened_tiles = await BoardHandler.fetch(PointRange(Point(0, 0), Point(0, 0)))
        closed_tiles = await BoardHandler.fetch(PointRange(Point(0, 1), Point(0, 1)))

        self.assertFalse(opened_tiles.at_tile(Point(0, 0)).is_flag)
        self.assertTrue(closed_tiles.at_tile(Point(0, 0)).is_flag)
