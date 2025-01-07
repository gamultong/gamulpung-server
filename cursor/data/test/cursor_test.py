from data_layer.board import Point
from data_layer.cursor import Cursor, Color
from datetime import datetime, timedelta
import unittest


class CursorTestCase(unittest.TestCase):
    def test_cursor_create(self):
        conn_id = "some id"
        cursor = Cursor.create(conn_id)

        self.assertEqual(cursor.id, conn_id)
        self.assertEqual(cursor.position.x, 0)
        self.assertEqual(cursor.position.y, 0)
        self.assertIsNone(cursor.pointer)
        self.assertIn(cursor.color, Color)
        self.assertEqual(cursor.width, 0)
        self.assertEqual(cursor.height, 0)

    def test_cursor_revive_at(self):
        conn_id = "some id"
        cursor = Cursor.create(conn_id)

        self.assertIsNone(cursor.revive_at)

        # revive_at이 지나지 않음
        hour_later = datetime.now() + timedelta(hours=1)
        cursor.revive_at = hour_later
        self.assertEqual(cursor.revive_at, hour_later)

        # revive_at이 지남
        hour_earlier = datetime.now() - timedelta(hours=1)
        cursor.revive_at = hour_earlier
        self.assertIsNone(cursor.revive_at)

    def test_check_interactable(self):
        # 0, 0
        cursor = Cursor.create("")

        # 본인
        self.assertTrue(cursor.check_interactable(Point(0, 0)))

        # 상하좌우
        self.assertTrue(cursor.check_interactable(Point(0, 1)))
        self.assertTrue(cursor.check_interactable(Point(0, -1)))
        self.assertTrue(cursor.check_interactable(Point(1, 0)))
        self.assertTrue(cursor.check_interactable(Point(-1, 0)))

        # 좌상 우상 좌하 우하
        self.assertTrue(cursor.check_interactable(Point(-1, 1)))
        self.assertTrue(cursor.check_interactable(Point(1, 1)))
        self.assertTrue(cursor.check_interactable(Point(-1, -1)))
        self.assertTrue(cursor.check_interactable(Point(1, -1)))

        # invaild
        self.assertFalse(cursor.check_interactable(Point(-1, 2)))

    def test_check_in_view(self):
        # /docs/example/cursor-location.png
        cur_a = Cursor(
            conn_id="A",
            position=Point(-3, 3),
            pointer=None,
            height=6,
            width=6,
            color=Color.BLUE
        )
        cur_b = Cursor(
            conn_id="B",
            position=Point(-3, -4),
            pointer=None,
            height=7,
            width=7,
            color=Color.BLUE
        )
        cur_c = Cursor(
            conn_id="C",
            position=Point(2, -1),
            pointer=None,
            height=4,
            width=4,
            color=Color.BLUE
        )

        self.assertTrue(cur_a.check_in_view(cur_c.position))
        self.assertFalse(cur_a.check_in_view(cur_b.position))

        self.assertTrue(cur_b.check_in_view(cur_a.position))
        self.assertTrue(cur_b.check_in_view(cur_c.position))

        self.assertFalse(cur_c.check_in_view(cur_a.position))
        self.assertFalse(cur_c.check_in_view(cur_b.position))


if __name__ == "__main__":
    unittest.main()
