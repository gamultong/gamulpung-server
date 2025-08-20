from data.board import Tile, Tiles, Point, PointRange
from data.cursor import Color

import unittest


class TilesTestCase(unittest.TestCase):
    def test_to_str(self):
        data = bytearray().join([bytearray.fromhex("abcd") for _ in range(3)])
        tiles = Tiles(data, 4, 4)

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

        tiles = Tiles(bytearray([open_tile.data, closed_tile.data]), 2, 1)

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

        tiles = Tiles(bytearray([flag_tile.data]), 1, 1)

        tiles.hide_info()
        data = tiles.data

        self.assertEqual(flag_tile.copy(hide_info=True).data, data[0])

    def test_at_tile(self):
        """
rrr
rbr
rrr
-> at_tile(1, 1) -> b
        """
        tile_list = [
            Tile.create(
                is_open=False,
                is_mine=True,
                is_flag=True,
                color=Color.RED,
                number=None
            )
            for _ in range(9)
        ]
        tile_list[4].color = Color.BLUE

        tiles = Tiles(bytearray([
            t.data
            for t in tile_list
        ]), 3, 3)

        res = tiles.at_tile(
            point=Point(1, 1)
        )

        self.assertEqual(res.color, Color.BLUE)

    def test_at_tiles(self):
        """
1111
1221
1221
1111
---
at_tiles(p(1, 1), p(2,2))
->
22
22
        """

        tiles = Tiles(bytearray([1, 1, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1]), 4, 4)

        res = tiles.at_tiles(
            point_range=PointRange(
                top_left=Point(1, 2),
                bottom_right=Point(2, 1)
            )
        )

        self.assertEqual(res.data, bytearray([2, 2, 2, 2]))

    def test_update_at(self):
        """
1111
1221
1221
1111
---
update_at(p(1, 1), 3)
->
1111
1221
1321
1111
        """
        tiles = Tiles(bytearray([1, 1, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1]), 4, 4)
        expected = Tiles(bytearray([1, 1, 1, 1, 1, 2, 2, 1, 1, 3, 2, 1, 1, 1, 1, 1]), 4, 4)
        tiles.update_at(Point(1, 1), Tile.from_int(3))

        self.assertEqual(tiles, expected)


if __name__ == "__main__":
    from unittest import main
    main()
