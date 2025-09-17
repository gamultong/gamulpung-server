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
from .tiles_mock import POINT, POINTRANGE, CLOSE_TILE, FLAG_ON_TILE, get_sec, setup_sec

patch = PathPatch("handler.board.internal.board")


class BoardHandler_TestCase(AsyncTestCase):
    @patch("Config")
    @cases([
        {"sec": get_sec(CLOSE_TILE), "exp": True},
        {"sec": get_sec(FLAG_ON_TILE), "exp": False}
    ])
    async def test_togle_flag_togle(self, config, sec: Section, exp: bool):
        setup_sec(sec)

        config.LENGTH = 1

        await BoardHandler.togle_flag(
            Point(0, 0)
        )

        tiles = await BoardHandler.fetch(
            PointRange(
                Point(0, 0), Point(0, 0)
            )
        )

        self.assertIs(tiles.at_tile(Point(0, 0)).is_flag, exp)


if __name__ == "__main__":
    from unittest import main
    main()
