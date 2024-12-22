import unittest
from unittest.mock import patch, MagicMock
from tests.utils import cases
from board.data import Point, Tile, Section
from board.data.handler import BoardHandler
from cursor.data import Color
from .fixtures import setup_board

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


class BoardHandlerTestCase(unittest.TestCase):
    def setUp(self):
        setup_board()

    @cases(FETCH_CASE)
    def test_fetch(self, data, expect):
        start_p = data["start_p"]
        end_p = data["end_p"]

        tiles = BoardHandler.fetch(start_p, end_p)
        data = tiles.to_str()

        self.assertEqual(data,  expect)

    def test_open_tile(self):
        p = Point(0, -2)

        result = BoardHandler.open_tile(p)

        tiles = BoardHandler.fetch(start=p, end=p)
        tile = Tile.from_int(tiles.data[0])

        self.assertTrue(tile.is_open)
        self.assertEqual(tile, result)

    @patch("board.data.Section.create")
    def test_open_tiles_cascade(self, create_seciton_mock: MagicMock):
        def stub_section_create(p: Point) -> Section:
            return Section(
                data=bytearray([0b10000000 for _ in range(Section.LENGTH ** 2)]),
                p=p
            )
        create_seciton_mock.side_effect = stub_section_create

        p = Point(0, 3)

        start_p, end_p, tiles = BoardHandler.open_tiles_cascade(p)

        self.assertEqual(len(create_seciton_mock.mock_calls), 20)

        self.assertEqual(start_p, Point(-1, 3))
        self.assertEqual(end_p, Point(3, -1))
        self.assertEqual(tiles, BoardHandler.fetch(start=start_p, end=end_p))

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

    def test_set_flag_state_true(self):
        p = Point(0, -2)
        color = Color.BLUE

        result = BoardHandler.set_flag_state(p=p, state=True, color=color)

        tiles = BoardHandler.fetch(start=p, end=p)
        tile = Tile.from_int(tiles.data[0])

        self.assertTrue(tile.is_flag)
        self.assertEqual(tile.color, color)

        self.assertEqual(tile, result)

    def test_set_flag_state_false(self):
        p = Point(1, -1)

        result = BoardHandler.set_flag_state(p=p, state=False)

        tiles = BoardHandler.fetch(start=p, end=p)
        tile = Tile.from_int(tiles.data[0])

        self.assertFalse(tile.is_flag)
        self.assertIsNone(tile.color)

        self.assertEqual(tile, result)


if __name__ == "__main__":
    unittest.main()
