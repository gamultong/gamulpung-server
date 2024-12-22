from cursor.data import Cursor, Color
from cursor.data.handler import (
    CursorHandler,
    NoMatchingCursorException,
    AlreadyWatchingException,
    NotWatchableException,
    NotWatchingException
)
from board.data import Point
import unittest


class CursorHandlerTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # /docs/example/cursor-location.png
        CursorHandler.cursor_dict = {
            "A": Cursor(
                conn_id="A",
                position=Point(-3, 3),
                pointer=None,
                height=6,
                width=6,
                color=Color.BLUE,
                revive_at=None
            ),
            "B": Cursor(
                conn_id="B",
                position=Point(-3, -4),
                pointer=None,
                height=7,
                width=7,
                color=Color.BLUE,
                revive_at=None
            ),
            "C": Cursor(
                conn_id="C",
                position=Point(2, -1),
                pointer=None,
                height=4,
                width=4,
                color=Color.BLUE,
                revive_at=None
            )
        }

    def tearDown(self):
        CursorHandler.cursor_dict = {}
        CursorHandler.watchers = {}
        CursorHandler.watching = {}

    def test_create(self):
        conn_id = "example_conn_id"
        _ = CursorHandler.create_cursor(conn_id)

        self.assertIn(conn_id, CursorHandler.cursor_dict)
        self.assertEqual(type(CursorHandler.cursor_dict[conn_id]), Cursor)
        self.assertEqual(CursorHandler.cursor_dict[conn_id].conn_id, conn_id)

    def test_get_cursor(self):
        a_cur: Cursor | None = CursorHandler.get_cursor("A")
        d_cur: Cursor | None = CursorHandler.get_cursor("D")

        self.assertIsNotNone(a_cur)
        self.assertEqual(type(a_cur), Cursor)
        self.assertEqual(a_cur.conn_id, "A")
        self.assertEqual(a_cur.position.x, -3)
        self.assertEqual(a_cur.position.y, 3)
        self.assertIsNone(a_cur.pointer)
        self.assertEqual(a_cur.height, 6)
        self.assertEqual(a_cur.width, 6)
        self.assertEqual(a_cur.color, Color.BLUE)

        self.assertIsNone(d_cur)

    def test_remove_cursor(self):
        CursorHandler.remove_cursor("A")
        self.assertNotIn("A", CursorHandler.cursor_dict)
        self.assertEqual(len(CursorHandler.cursor_dict), 2)

    def test_exists_range(self):
        result = CursorHandler.exists_range(start=Point(-3, 3), end=Point(3, -3))

        result = [c.conn_id for c in result]

        self.assertEqual(len(result), 2)
        self.assertIn("A", result)
        self.assertIn("C", result)

    def test_exists_range_exclude_id(self):
        result = CursorHandler.exists_range(start=Point(-3, 3), end=Point(3, -3), exclude_ids=["A"])

        result = [c.conn_id for c in result]

        self.assertEqual(len(result), 1)
        self.assertIn("C", result)

    def test_exists_range_exclude_range(self):
        result = CursorHandler.exists_range(
            start=Point(-3, 3), end=Point(3, -3),
            exclude_start=Point(-4, 3), exclude_end=Point(0, 1)
        )

        result = [c.conn_id for c in result]

        self.assertEqual(len(result), 1)
        self.assertIn("C", result)

    def test_view_includes_point(self):
        result = CursorHandler.view_includes_point(p=Point(-3, 0))

        result = [c.conn_id for c in result]

        self.assertEqual(len(result), 2)
        self.assertIn("A", result)
        self.assertIn("B", result)

    def test_view_includes_point_exclude_id(self):
        result = CursorHandler.view_includes_point(p=Point(-3, 0), exclude_ids=["A"])

        result = [c.conn_id for c in result]

        self.assertEqual(len(result), 1)
        self.assertIn("B", result)

    def test_view_includes_range(self):
        start = Point(-3, 1)
        end = Point(-2, 0)
        result = CursorHandler.view_includes_range(start=start, end=end)

        result = [c.conn_id for c in result]

        self.assertEqual(len(result), 3)
        self.assertIn("A", result)
        self.assertIn("B", result)
        self.assertIn("C", result)

    def test_view_includes_range__exclude_id(self):
        start = Point(-3, 1)
        end = Point(-2, 0)
        result = CursorHandler.view_includes_range(start=start, end=end, exclude_ids=["A"])

        result = [c.conn_id for c in result]

        self.assertEqual(len(result), 2)
        self.assertIn("B", result)
        self.assertIn("C", result)

    def test_add_watcher(self):
        CursorHandler.add_watcher(
            watcher=CursorHandler.cursor_dict["B"],
            watching=CursorHandler.cursor_dict["A"]
        )

        self.assertIn("A", CursorHandler.watchers)
        self.assertIn("B", CursorHandler.watchers["A"])

        self.assertIn("B", CursorHandler.watching)
        self.assertIn("A", CursorHandler.watching["B"])

    def test_add_watcher_not_watchable(self):
        with self.assertRaises(NotWatchableException):
            CursorHandler.add_watcher(
                watcher=CursorHandler.cursor_dict["C"],
                watching=CursorHandler.cursor_dict["A"]
            )

    def test_add_watcher_already_watching(self):
        CursorHandler.add_watcher(
            watcher=CursorHandler.cursor_dict["B"],
            watching=CursorHandler.cursor_dict["A"]
        )

        with self.assertRaises(AlreadyWatchingException):
            CursorHandler.add_watcher(
                watcher=CursorHandler.cursor_dict["B"],
                watching=CursorHandler.cursor_dict["A"]
            )

    def test_add_watcher_no_matching_cursor(self):
        with self.assertRaises(NoMatchingCursorException):
            CursorHandler.add_watcher(
                watcher=Cursor.create("D"),
                watching=CursorHandler.cursor_dict["A"]
            )

    def test_remove_watcher(self):
        CursorHandler.watchers["A"] = ["B"]
        CursorHandler.watching["B"] = ["A", None]

        CursorHandler.remove_watcher(
            watcher=CursorHandler.cursor_dict["B"],
            watching=CursorHandler.cursor_dict["A"]
        )

        self.assertNotIn("A", CursorHandler.watching["B"])
        self.assertNotIn("A", CursorHandler.watchers)

    def test_remove_watcher_not_watching(self):
        with self.assertRaises(NotWatchingException):
            CursorHandler.remove_watcher(
                watcher=CursorHandler.cursor_dict["B"],
                watching=CursorHandler.cursor_dict["A"]
            )

    def test_remove_watcher_no_matching_cursor(self):
        with self.assertRaises(NoMatchingCursorException):
            CursorHandler.remove_watcher(
                watcher=Cursor.create("D"),
                watching=CursorHandler.cursor_dict["A"]
            )

    def test_get_watchers(self):
        CursorHandler.add_watcher(
            watcher=CursorHandler.cursor_dict["B"],
            watching=CursorHandler.cursor_dict["A"]
        )

        a_watchers = CursorHandler.get_watchers("A")
        b_watchers = CursorHandler.get_watchers("B")

        self.assertEqual(len(a_watchers), 1)
        self.assertEqual(a_watchers[0], "B")

        self.assertEqual(len(b_watchers), 0)

    def test_get_watchers_no_matching_cursor(self):
        with self.assertRaises(NoMatchingCursorException):
            CursorHandler.get_watchers("D")

    def test_get_watching(self):
        CursorHandler.add_watcher(
            watcher=CursorHandler.cursor_dict["B"],
            watching=CursorHandler.cursor_dict["A"]
        )

        a_watching = CursorHandler.get_watching("A")
        b_watching = CursorHandler.get_watching("B")

        self.assertEqual(b_watching[0], "A")
        self.assertEqual(len(b_watching), 1)

        self.assertEqual(len(a_watching), 0)

    def test_get_watching_no_matching_cursor(self):
        with self.assertRaises(NoMatchingCursorException):
            CursorHandler.get_watching("D")
