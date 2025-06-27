from data.cursor import Cursor, Color
from data.board import PointRange
from data.payload import DataPayload
from event.message import Message

from datetime import datetime, timedelta

from handler.cursor import (
    CursorHandler,
    CursorEvent,
    CursorException,
)

from handler.cursor.internal.cursor_handler import diff_cursors


from data.base.utils import Relation
from data.board import Point, PointRange
from data.cursor import Cursor
from unittest import IsolatedAsyncioTestCase as AsyncTest, TestCase
from unittest.mock import call, AsyncMock, MagicMock, patch as _patch

from tests.utils import cases, PathPatch

from handler.storage.dict import DictSpace, DictStorage

patch = PathPatch("handler.cursor.internal.cursor_handler")

DATASET = {
    "A": Cursor(
        conn_id="A",
        position=Point(-3, 3),
        pointer=None,
        height=6,
        width=6,
        color=Color.BLUE
    ),
    "B": Cursor(
        conn_id="B",
        position=Point(-3, -4),
        pointer=None,
        height=7,
        width=7,
        color=Color.BLUE
    ),
    "C": Cursor(
        conn_id="C",
        position=Point(2, -1),
        pointer=None,
        height=4,
        width=4,
        color=Color.BLUE
    )
}

TARGET_DATASET = {
    "A": Relation[str](_id="A", relations=["C"]),
    "B": Relation[str](_id="B", relations=["A", "C"]),
    "C": Relation[str](_id="C", relations=[])
}
WATCHER_DATASET = {
    "A": Relation[str](_id="A", relations=["B"]),
    "B": Relation[str](_id="B", relations=[]),
    "C": Relation[str](_id="C", relations=["A", "B"]),
}

EXTRA_CUR = Cursor(
    conn_id="EX",
    position=Point(2, -1),
    pointer=None,
    height=4,
    width=4,
    color=Color.BLUE
)


class CursorHandler_TestCase(AsyncTest):
    def setUp(self):
        self.cursor_storage = DictSpace[str, Cursor]("cursor", DATASET)
        self.target_storage = DictSpace[str, Relation[str]]("watching", TARGET_DATASET)
        self.watcher_storage = DictSpace[str, Relation[str]]("watcher", WATCHER_DATASET)

        CursorHandler.cursor_storage = self.cursor_storage
        CursorHandler.watcher_storage = self.watcher_storage
        CursorHandler.target_storage = self.target_storage

    @cases([
        {"id": id, "cur": cur} for id, cur in DATASET.items()
    ])
    async def test_get(self, id: str, cur: Cursor):
        got = await CursorHandler.get(id)
        self.assertEqual(got, cur)
        self.assertIsNot(got, cur)

    async def test_get_not_found(self):
        with self.assertRaises(CursorException.NotFound):
            await CursorHandler.get("non-user")

    @cases([
        {"range": PointRange(Point(-3, 3), Point(2, -1)), "curs": [DATASET["A"], DATASET["C"]]},
        {"range": PointRange(Point(-3, 3), Point(-3, 3)), "curs": [DATASET["A"]]},
        {"range": PointRange(Point(0, 0), Point(0, 0)), "curs": []}
    ])
    async def test_get_by_range(self, range: PointRange, curs: list[Cursor]):
        got = await CursorHandler.get_by_range(range)
        self.assertCountEqual(got, curs)

    async def test_get_by_range_filter(self):
        range = PointRange(Point(-3, 3), Point(2, -1))
        # original: [DATASET["A"], DATASET["C"]]

        got = await CursorHandler.get_by_range(range, filters=[lambda c: c.id == "A"])
        self.assertCountEqual(got, [DATASET["A"]])

    @cases([
        {"point": Point(-3, 3), "curs": [DATASET["A"]]},
        {"point": Point(2, -1), "curs": [DATASET["C"], EXTRA_CUR]},
        {"point": Point(0, 0), "curs": []}
    ])
    async def test_get_by_point(self, point: Point, curs: list[Cursor]):
        await self.cursor_storage.set(EXTRA_CUR.id, EXTRA_CUR)

        got = await CursorHandler.get_by_point(point)
        self.assertCountEqual(got, curs, msg=(got, curs))

    @cases([
        {"range": PointRange(Point(4, -5), Point(5, -6)),
         "curs": [DATASET["B"], DATASET["C"]]},
        {"range": PointRange(Point(100, 100), Point(100, 100)),
         "curs": []},
    ])
    async def test_get_by_watching_range(self, range: PointRange, curs: list[Cursor]):
        got = await CursorHandler.get_by_watching_range(range)
        self.assertCountEqual(got, curs, msg=(got, curs))

    @cases([
        {"point": Point(0, 0),
         "curs": [DATASET["A"], DATASET["B"], DATASET["C"]]},
        {"point":  Point(100, 100),
         "curs": []},
    ])
    async def test_get_by_watching_point(self, point: Point, curs: list[Cursor]):
        got = await CursorHandler.get_by_watching_point(point)
        self.assertCountEqual(got, curs, msg=(got, curs))

    @cases([
        {"cursor": cur} for _, cur in DATASET.items()
    ])
    async def test_get_watchers(self, cursor: Cursor):
        got = await CursorHandler.get_watchers(cursor)

        expected = [DATASET[id] for id in WATCHER_DATASET[cursor.id]]
        self.assertCountEqual(got, expected)

    @cases([
        {"cursor": cur} for _, cur in DATASET.items()
    ])
    async def test_get_targets(self, cursor: Cursor):
        got = await CursorHandler.get_targets(cursor)

        expected = [DATASET[id] for id in TARGET_DATASET[cursor.id]]
        self.assertCountEqual(got, expected)

    @patch("publish_data_event")
    async def test_create(self, publish: AsyncMock):
        template = Cursor.create("D")
        created = await CursorHandler.create(template)

        self.assertEqual(created, template)

        fetched = await self.cursor_storage.get("D")
        self.assertEqual(created, fetched)

        publish.assert_called_once_with(CursorEvent.CREATED, id=template.id)

    @patch("publish_data_event")
    async def test_delete(self, publish: AsyncMock):
        existing = await self.cursor_storage.get("A")

        await CursorHandler.delete(existing.id)

        publish.assert_called_once_with(CursorEvent.DELETE, data=existing)

        fetched = await self.cursor_storage.get("A")
        self.assertIsNone(fetched)

    async def test_private_update(self):
        cur_a = await self.cursor_storage.get("A")
        cur_a.pointer = Point(100, 100)

        await CursorHandler._update(cur_a)

        cur_a = await self.cursor_storage.get("A")
        self.assertEqual(cur_a.pointer, Point(100, 100))

    @patch("datetime")
    @patch("CursorHandler._update")
    @patch("publish_data_event")
    async def test_revive(self, publish_data_event: AsyncMock, update: AsyncMock, _datetime: MagicMock):
        _datetime.now.return_value = datetime(year=1, month=1, day=1, hour=0, minute=0, second=1)

        cur_a = await self.cursor_storage.get("A")
        cur_a.revive_at = datetime(year=1, month=1, day=1, hour=0, minute=0, second=0)
        await self.cursor_storage.set("A", cur_a)

        revived = await CursorHandler.revive("A")
        self.assertIsNone(revived.revive_at)

        publish_data_event.assert_called_once_with(CursorEvent.REVIVE, data=revived)
        update.assert_called_once_with(revived)

    @cases([
        {"watcher_id": "B", "target_id": "A"},
        {"watcher_id": "B", "target_id": "C"}
    ])
    @patch("publish_data_event")
    async def test_add_watcher(self, mock: AsyncMock, watcher_id, target_id):
        self.reset_relationship()

        await CursorHandler._add_watcher(watcher=DATASET[watcher_id], target=DATASET[target_id])

        self.assertCountEqual([watcher_id], await self.watcher_storage.get(target_id))
        self.assertCountEqual([target_id], await self.target_storage.get(watcher_id))

        # mock.assert_has_calls(
        #     calls=[
        #         call(CursorEvent.WATCHER_ADDED, id=target_id),
        #         call(CursorEvent.TARGET_ADDED, id=watcher_id),
        #     ],
        #     any_order=True,
        # )

    async def test_add_watcher_not_target(self):
        self.reset_relationship()

        with self.assertRaises(CursorException.NotWatchable):
            await CursorHandler._add_watcher(watcher=DATASET["A"], target=DATASET["B"])

    @cases([
        {"watcher_id": "B", "target_id": "A"},
        {"watcher_id": "B", "target_id": "C"}
    ])
    @patch("publish_data_event")
    async def test_remove_watcher(self, mock: AsyncMock, watcher_id, target_id):
        self.assertIn(watcher_id, await self.watcher_storage.get(target_id))
        self.assertIn(target_id, await self.target_storage.get(watcher_id))

        await CursorHandler._remove_watcher(watcher=DATASET[watcher_id], target=DATASET[target_id])

        self.assertNotIn(watcher_id, await self.watcher_storage.get(target_id))
        self.assertNotIn(target_id, await self.target_storage.get(watcher_id))

        # mock.assert_has_calls(
        #     calls=[
        #         call(CursorEvent.WATCHER_REMOVED, id=target_id),
        #         call(CursorEvent.TARGET_REMOVED, id=watcher_id),
        #     ],
        #     any_order=True,
        # )

    async def test_remove_watcher_not_watching(self):
        with self.assertRaises(CursorException.NotWatching):
            await CursorHandler._remove_watcher(watcher=DATASET["A"], target=DATASET["B"])

    def reset_relationship(self):
        self.watcher_storage = DictSpace[str, Relation[str]]("watcher", {})
        CursorHandler.watcher_storage = self.watcher_storage
        self.target_storage = DictSpace[str, Relation[str]]("target", {})
        CursorHandler.target_storage = self.target_storage

    @patch("publish_data_event")
    async def test_set_window_size(self, publish_data_event: AsyncMock):
        # A:width 4 -> rm C
        # A:height 7 -> add B
        cur = await self.cursor_storage.get("A")
        cur.sub[Cursor.Targets] = await self.target_storage.get("A")

        changed = await CursorHandler.set_window_size(id="A", width=4, height=7)

        self.assertEqual(changed.width, 4)
        self.assertEqual(changed.height, 7)
        self.assertCountEqual(changed.sub[Cursor.Targets], ["B"])
        self.assertCountEqual(changed.sub[Cursor.Targets], await self.target_storage.get("A"))

        publish_data_event.assert_called_once()
        args = publish_data_event.call_args
        self.assertEqual(args[0][0], CursorEvent.WINDOW_SIZE_SET)
        self.assertEqual(args[1]["data"], cur)
        self.assertEqual(args[1]["data"].sub[Cursor.Targets], cur.sub[Cursor.Targets])

    @patch("publish_data_event")
    async def test_move(self, publish_data_event: AsyncMock):
        mover = await self.cursor_storage.get("B")
        mover.sub[Cursor.Targets] = await self.target_storage.get("B")
        mover.sub[Cursor.Watchers] = await self.watcher_storage.get("B")

        position = Point(mover.position.x+1, mover.position.y-1)

        moved = await CursorHandler.move("B", p=position)

        self.assertEqual(moved.position, position)
        self.assertCountEqual(moved.sub[Cursor.Targets], ["C"])
        self.assertCountEqual(moved.sub[Cursor.Targets], await self.target_storage.get("B"))
        self.assertCountEqual(moved.sub[Cursor.Watchers], ["C"])
        self.assertCountEqual(moved.sub[Cursor.Watchers], await self.watcher_storage.get("B"))

        publish_data_event.assert_called_once()
        args = publish_data_event.call_args
        self.assertEqual(args[0][0], CursorEvent.MOVED)
        self.assertEqual(args[1]["data"], mover)
        self.assertEqual(args[1]["data"].sub[Cursor.Targets], mover.sub[Cursor.Targets])
        self.assertEqual(args[1]["data"].sub[Cursor.Watchers], mover.sub[Cursor.Watchers])

    @patch("publish_data_event")
    async def test_move_not_movable(self, publish_data_event: AsyncMock):
        mover = await self.cursor_storage.get("B")
        position = Point(mover.position.x+100, mover.position.y)  # 100을 넘을 일은 아마 없을걸

        with self.assertRaises(CursorException.NotMovable):
            await CursorHandler.move("B", p=position)

    @patch("publish_data_event")
    async def test_set_pointer(self, publish_data_event: AsyncMock):
        cur = await self.cursor_storage.get("A")
        pointer = Point(cur.position.x+1, cur.position.y-1)

        changed = await CursorHandler.set_pointer("A", p=pointer)

        self.assertEqual(changed.pointer, pointer)

        publish_data_event.assert_called_once_with(CursorEvent.POINTING, data=cur)

    @patch("publish_data_event")
    async def test_set_pointer(self, publish_data_event: AsyncMock):
        mover = await self.cursor_storage.get("A")
        pointer = mover.view_range.top_left.copy()
        pointer = Point(pointer.x-1, pointer.y)  # 벗어남

        with self.assertRaises(CursorException.NotPointable):
            await CursorHandler.set_pointer("A", p=pointer)

    @patch("datetime")
    @patch("CursorHandler._update")
    @patch("publish_data_event")
    async def test_kill(self, publish_data_event: AsyncMock, update: AsyncMock, _datetime: MagicMock):
        now = datetime(year=1, month=1, day=1, hour=0, minute=0, second=0)
        _datetime.now.return_value = now

        cur = await self.cursor_storage.get("A")

        duration = timedelta(seconds=60)

        dead = await CursorHandler.kill("A", duration)
        self.assertEqual(dead.revive_at, now+duration)

        publish_data_event.assert_called_once_with(CursorEvent.DEATH, data=cur)
        update.assert_called_once_with(cursor=dead)


class DiffCursor_TestCase(TestCase):
    def test_diff_cursors(self):
        curs = [Cursor.create(f"{i}") for i in range(4)]
        front = curs[:3]
        back = curs[2:]

        front_only, both, back_only = diff_cursors(front, back)
        self.assertEqual(front_only, curs[:2])
        self.assertEqual(both, curs[2:3])
        self.assertEqual(back_only, curs[3:])
