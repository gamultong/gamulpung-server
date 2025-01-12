from data.board import Tile, Tiles
from data.cursor import Color

import unittest


class TilesTestCase(unittest.TestCase):
    def test_to_str(self):
        data = bytearray().join([bytearray.fromhex("abcd") for _ in range(3)])
        tiles = Tiles(data=data)

        s = tiles.to_str()

        self.assertEqual(s, "abcdabcdabcd")

    def test_hide_info(self):
        open_tile = Tile.create(
            is_open=True,
            is_mine=True,
            is_flag=False,
            color=None,
            number=None
        )
        closed_tile = Tile.create(
            is_open=False,
            is_mine=False,
            is_flag=False,
            color=None,
            number=7
        )

        tiles = Tiles(data=bytearray([open_tile.data, closed_tile.data]))

        tiles.hide_info()
        data = tiles.data

        self.assertEqual(open_tile.data, data[0])
        self.assertEqual(closed_tile.copy(hide_info=True).data, data[1])

    def test_hide_info_flag(self):
        flag_tile = Tile.create(
            is_open=False,
            is_mine=True,
            is_flag=True,
            color=Color.RED,
            number=None
        )

        tiles = Tiles(data=bytearray([flag_tile.data]))

        tiles.hide_info()
        data = tiles.data

        self.assertEqual(flag_tile.copy(hide_info=True).data, data[0])
