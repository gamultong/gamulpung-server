import unittest
from unittest.mock import patch, MagicMock
from tests.utils import cases
from data.board import Point, Tile, Section
from handler.board import BoardHandler
from data.cursor import Color

from handler.board.storage import SectionStorage
from handler.board.storage.test.fixtures import setup_board, teardown_board

FETCH_CASE = \
    [
        {  # 한개
            "data": {
                "start_p": Point(0, 0),
                "end_p": Point(0, 0)
            },
            "expect": "81"
        },
        {  # 가운데
            "data": {
                "start_p": Point(-2, 1),
                "end_p": Point(1, -2)
            },
            "expect": "82818170818081018281813983680302"
        },
        {  # 전체
            "data": {
                "start_p": Point(-4, 3),
                "end_p": Point(3, -4)
            },
            "expect": "0102020100000000014040010101010001028281817001000121818081010100014082818139010181818368030240018080824003400201c080810102010100"
        }
    ]


class BoardHandlerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await setup_board()

    @cases(FETCH_CASE)
    @patch("data.board.Section.create")
    async def test_fetch(self, mock: MagicMock, data, expect):
        def stub_section_create(p: Point) -> Section:
            return Section(
                data=bytearray([0b00000000 for _ in range(Section.LENGTH ** 2)]),
                p=p
            )
        mock.side_effect = stub_section_create

        start_p = data["start_p"]
        end_p = data["end_p"]

        tiles = await BoardHandler.fetch(start_p, end_p)
        data = tiles.to_str()

        self.assertEqual(data,  expect)

    async def test_open_tile(self):
        p = Point(0, -2)

        result = await BoardHandler.open_tile(p)

        tiles = await BoardHandler.fetch(start=p, end=p)
        tile = Tile.from_int(tiles.data[0])

        self.assertTrue(tile.is_open)
        self.assertEqual(tile, result)

    @patch("data.board.Section.create")
    async def test_open_tiles_cascade(self, create_seciton_mock: MagicMock):
        def stub_section_create(p: Point) -> Section:
            return Section(
                data=bytearray([0b10000000 for _ in range(Section.LENGTH ** 2)]),
                p=p
            )
        create_seciton_mock.side_effect = stub_section_create

        p = Point(0, 3)

        start_p, end_p, tiles = await BoardHandler.open_tiles_cascade(p)

        self.assertEqual(len(create_seciton_mock.mock_calls), 21)

        self.assertEqual(start_p, Point(-1, 3))
        self.assertEqual(end_p, Point(3, -1))
        self.assertEqual(tiles, await BoardHandler.fetch(start=start_p, end=end_p))

        OPEN_0 = 0b10000000
        OPEN_1 = 0b10000001
        CLOSED_1 = 0b00000001
        BLUE_FLAG = 0b01110000
        PURPLE_FLAG = 0b00111001

        expected = bytearray([
            OPEN_1, OPEN_0, OPEN_0, OPEN_0, OPEN_0,
            OPEN_1, OPEN_1, OPEN_1, OPEN_1, OPEN_0,
            OPEN_1, OPEN_1, BLUE_FLAG, OPEN_1, OPEN_0,
            OPEN_0, OPEN_1, CLOSED_1, OPEN_1, OPEN_0,
            OPEN_1, OPEN_1, PURPLE_FLAG, OPEN_1, OPEN_1
        ])
        self.assertEqual(tiles.data, expected)

    async def test_set_flag_state_true(self):
        p = Point(0, -2)
        color = Color.BLUE

        result = await BoardHandler.set_flag_state(p=p, state=True, color=color)

        tiles = await BoardHandler.fetch(start=p, end=p)
        tile = Tile.from_int(tiles.data[0])

        self.assertTrue(tile.is_flag)
        self.assertEqual(tile.color, color)

        self.assertEqual(tile, result)

    async def test_set_flag_state_false(self):
        p = Point(1, -1)

        result = await BoardHandler.set_flag_state(p=p, state=False)

        tiles = await BoardHandler.fetch(start=p, end=p)
        tile = Tile.from_int(tiles.data[0])

        self.assertFalse(tile.is_flag)
        self.assertIsNone(tile.color)

        self.assertEqual(tile, result)

    async def test_get_random_open_position(self):
        for _ in range(10):
            point = await BoardHandler.get_random_open_position()

            tiles = await BoardHandler.fetch(point, point)
            tile = Tile.from_int(tiles.data[0])

            self.assertTrue(tile.is_open)

    async def test_get_random_open_position_one_section_one_open(self):
        sec = await SectionStorage.get(Point(-1, 0))
        sec.applied_flag = 0
        await teardown_board()
        await SectionStorage.set(sec)

        for _ in range(10):
            point = await BoardHandler.get_random_open_position()

            tiles = await BoardHandler.fetch(point, point)
            tile = Tile.from_int(tiles.data[0])

            self.assertTrue(tile.is_open)


if __name__ == "__main__":
    unittest.main()
