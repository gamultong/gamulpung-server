from data_layer.cursor import Color
from data_layer.board import Tile, InvalidTileException

import unittest
from tests.utils import cases

"""
Color
0: RED
1: YELLOW
2: BLUE
3: PURPLE
"""
TILE_FROM_INT_TEST_CASE = [
    {
        "b": 0b10000011,
        "is_open": True,
        "is_mine": False,
        "is_flag": False,
        "color": None,
        "number": 3,
        "exception": None
    },
    {
        "b": 0b11000000,
        "is_open": True,
        "is_mine": True,
        "is_flag": False,
        "color": None,
        "number": None,
        "exception": None
    },
    {
        "b": 0b00000111,
        "is_open": False,
        "is_mine": False,
        "is_flag": False,
        "color": None,
        "number": 7,
        "exception": None
    },
    {
        "b": 0b01101000,
        "is_open": False,
        "is_mine": True,
        "is_flag": True,
        "color": Color.YELLOW,
        "number": None,
        "exception": None
    },
    {
        "b": 0b00110001,
        "is_open": False,
        "is_mine": False,
        "is_flag": True,
        "color": Color.BLUE,
        "number": 1,
        "exception": None
    },
    {
        # open flag
        "b": 0b10110000,
        "is_open": True,
        "is_mine": False,
        "is_flag": True,
        "color": Color.BLUE,
        "number": None,
        "exception": InvalidTileException
    }
]

TILE_CREATE_TEST_CASE = [
    {
        # default case
        "is_open": False,
        "is_mine": False,
        "is_flag": True,
        "color": Color.BLUE,
        "number": None,
        "exception": None
    },
    {
        # mine number
        "is_open": False,
        "is_mine": True,
        "is_flag": False,
        "color": None,
        "number": 6,
        "exception": InvalidTileException
    },
    {
        # open flag
        "is_open": True,
        "is_mine": False,
        "is_flag": True,
        "color": Color.PURPLE,
        "number": 1,
        "exception": InvalidTileException
    },
    {
        # flag no color
        "is_open": False,
        "is_mine": False,
        "is_flag": True,
        "color": None,
        "number": 1,
        "exception": InvalidTileException
    },
    {
        # color no flag
        "is_open": False,
        "is_mine": False,
        "is_flag": False,
        "color": Color.PURPLE,
        "number": 1,
        "exception": InvalidTileException
    },
    {
        # number overflow
        "is_open": False,
        "is_mine": False,
        "is_flag": False,
        "color": None,
        "number": 8,
        "exception": InvalidTileException
    },
    {
        # number underflow
        "is_open": False,
        "is_mine": False,
        "is_flag": False,
        "color": None,
        "number": -1,
        "exception": InvalidTileException
    },
]


class TileTestCase(unittest.TestCase):
    @cases(TILE_CREATE_TEST_CASE)
    def test_tile_create(self, is_open, is_mine, is_flag, color, number, exception):
        if exception:
            with self.assertRaises(exception):
                tile = Tile.create(
                    is_open=is_open,
                    is_mine=is_mine,
                    is_flag=is_flag,
                    color=color,
                    number=number
                )
            return

        tile = Tile.create(
            is_open=is_open,
            is_mine=is_mine,
            is_flag=is_flag,
            color=color,
            number=number
        )

        self.assertEqual(tile.is_open, is_open)
        self.assertEqual(tile.is_mine, is_mine)
        self.assertEqual(tile.is_flag, is_flag)
        self.assertEqual(tile.color, color)
        self.assertEqual(tile.number, number)

    @cases(TILE_FROM_INT_TEST_CASE)
    def test_tile_from_int(self, b, is_open, is_mine, is_flag, color, number, exception):
        if exception:
            with self.assertRaises(exception):
                tile = Tile.from_int(b)
            return

        tile = Tile.from_int(b)

        self.assertEqual(tile.is_open, is_open)
        self.assertEqual(tile.is_mine, is_mine)
        self.assertEqual(tile.is_flag, is_flag)
        self.assertEqual(tile.color, color)
        self.assertEqual(tile.number, number)

        self.assertEqual(tile.data, b)

    def test_tile_copy(self):
        tile = Tile.create(
            is_open=False,
            is_mine=True,
            is_flag=True,
            color=Color.RED,
            number=None
        )

        copied = tile.copy()
        self.assertEqual(tile, copied)

        hidden = tile.copy(hide_info=True)
        expected = tile.create(
            is_open=tile.is_open,
            is_mine=False,
            is_flag=tile.is_flag,
            color=tile.color,
            number=None
        )
        self.assertEqual(hidden, expected)
