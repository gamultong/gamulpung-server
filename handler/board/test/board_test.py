"""
1 -> (-1, 0)
2 -> (0, 0)
3 -> (-1, -1)
4 -> (0, -1)

1122
1122
3344
3344
->
2 -> (0, 0)

fetch(R(P(-1, 0), P(0, -1)))
->
12
34
"""
from data.board import Tiles, Point, PointRange
from handler.board import Section, BoardHandler


from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call
from tests.utils import PathPatch, cases, override, MockSet, Wrapper as Wp


def make_tiles(data):
    return Tiles(
        bytearray([
            data for _ in range(4)
        ]),
        2, 2
    )


patch = PathPatch("handler.board.internal.section")

SEC_1 = Section(Point(-1, 0), make_tiles(1))
SEC_2 = Section(Point(0, 0), make_tiles(2))
SEC_3 = Section(Point(-1, -1), make_tiles(3))
SEC_4 = Section(Point(0, -1), make_tiles(4))

config_mock = MagicMock()
config_mock.LENGHT = 2


class BoardHandler_TestCase(AsyncTestCase):
    def setUp(self) -> None:
        BoardHandler.section_dict = {
            SEC_1.point: SEC_1,
            SEC_2.point: SEC_2,
            SEC_3.point: SEC_3,
            SEC_4.point: SEC_4
        }

    @patch("Config", config_mock)
    async def test_fetch_normal(self, config):
        res = await BoardHandler.fetch(
            PointRange(
                Point(-1, 0),
                Point(0, -1)
            )
        )

        self.assertEqual(
            res.data, bytearray([1, 2, 3, 4])
        )
