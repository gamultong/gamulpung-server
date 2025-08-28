from data.board import Tiles, Point, PointRange, Tile
from data.cursor import Color
from handler.board import Section, BoardHandler

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call
from tests.utils import PathPatch, cases, override, MockSet, Wrapper as Wp
from .tiles_mock import POINT, POINTRANGE, CLOSE_TILE, get_sec, setup_sec

patch = PathPatch("handler.board.internal.board")


class BoardHandler_TestCase(AsyncTestCase):
    @patch("Config")
    @cases([
        {"sec": get_sec(CLOSE_TILE)},
    ])
    async def test_open_tile(self, config, sec: Section):
        setup_sec(sec)
        config.LENGTH = 1

        await BoardHandler.open_tiles(
            POINT
        )

        closed_tiles = await BoardHandler.fetch(
            POINTRANGE
        )

        self.assertTrue(closed_tiles.at_tile(POINT).is_open)


if __name__ == "__main__":
    from unittest import main
    main()
