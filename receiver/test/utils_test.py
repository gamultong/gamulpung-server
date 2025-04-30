from event.message import Message
from data.cursor import Cursor
from data.board import Point, Tiles
from data.score import Score
from data.payload import EventCollection, CursorsPayload, CursorPayload

from receiver.internal.utils import (
    multicast, watch, unwatch,
    publish_new_cursors, fetch_tiles, get_watchers
)

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import patch, AsyncMock, MagicMock, call

from .test_tools import assertMulticast
from tests.utils import PathPatch

patch = PathPatch("receiver.internal.utils")

class Multicast_TestCase(AsyncTestCase):
    @patch("EventBroker.publish")
    async def test_normal(self, publish_mock: AsyncMock):
        target_conns = ["a", "b", "c"]
        message = Message(
            event="example_event",
            payload="example_payload"
        )

        await multicast(target_conns=target_conns, message=message)

        publish_mock.assert_called_once()
        got: Message = publish_mock.mock_calls[0].kwargs["message"]
        self.assertEqual(
            got,
            Message(
                event="multicast",
                header={
                    "target_conns": target_conns,
                    "origin_event": message.event
                },
                payload=message.payload
            )
        )

    @patch("EventBroker.publish")
    async def test_no_target_conns(self, publish_mock: AsyncMock):
        target_conns = []
        message = Message(
            event="example_event",
            payload="example_payload"
        )

        await multicast(target_conns=target_conns, message=message)

        publish_mock.assert_not_called()


class FetchTiles_TestCase(AsyncTestCase):
    @patch("BoardHandler.fetch", return_value=MagicMock(Tiles))
    async def test_normal(self, fetch_mock: AsyncMock):
        start, end = Point(0, 0), Point(0, 0)

        tiles = await fetch_tiles(start, end)

        fetch_mock.assert_called_once_with(start, end)
        tiles.hide_info.assert_called_once()


cur_A = Cursor.create("A")
cur_B = Cursor.create("B")
cur_C = Cursor.create("C")
cur_D = Cursor.create("D")

watchers = [cur_A, cur_B]
watchings = [cur_C, cur_D]


class Watch_TestCase(TestCase):
    @patch("CursorHandler.add_watcher")
    def test_normal(self, add_watcher_mock: MagicMock):
        watch(watchers=watchers, watchings=watchings)

        self.assertEqual(
            add_watcher_mock.call_count,
            len(watchers) * len(watchings)
        )

        call_list = [
            (call.kwargs["watcher"], call.kwargs["watching"])
            for call in add_watcher_mock.mock_calls
        ]

        self.assertIn((cur_A, cur_C), call_list)
        self.assertIn((cur_A, cur_D), call_list)
        self.assertIn((cur_B, cur_C), call_list)
        self.assertIn((cur_B, cur_D), call_list)


class Unwatch_TestCase(TestCase):
    @patch("CursorHandler.remove_watcher")
    def test_normal(self, remove_watcher_mock: MagicMock):
        unwatch(watchers=watchers, watchings=watchings)

        self.assertEqual(
            remove_watcher_mock.call_count,
            len(watchers) * len(watchings)
        )

        call_list = [
            (call.kwargs["watcher"], call.kwargs["watching"])
            for call in remove_watcher_mock.mock_calls
        ]

        self.assertIn((cur_A, cur_C), call_list)
        self.assertIn((cur_A, cur_D), call_list)
        self.assertIn((cur_B, cur_C), call_list)
        self.assertIn((cur_B, cur_D), call_list)


class PublishNewCursors_TestCase(AsyncTestCase):
    @patch("multicast")
    @patch("ScoreHandler.get_by_id")
    async def test_normal(self, get_by_id: AsyncMock,multicast: AsyncMock):
        cursors = [Cursor.create("A"), Cursor.create("B")]
        target_cursors = [Cursor.create("C"), Cursor.create("D")]

        expected_score = Score(cursor_id="don't care", value=10)
        get_by_id.return_value = expected_score

        await publish_new_cursors(
            target_cursors=target_cursors,
            cursors=cursors
        )

        multicast.assert_called_once()

        assertMulticast(
            self, multicast.mock_calls[0],
            target_conns=[cur.id for cur in target_cursors],
            message=Message(
                event=EventCollection.CURSORS,
                payload=CursorsPayload(
                    cursors=[CursorPayload(
                        id=cursor.id,
                        position=cursor.position,
                        pointer=cursor.pointer,
                        color=cursor.color,
                        revive_at=cursor.revive_at.astimezone().isoformat() if cursor.revive_at is not None else None,
                        score=expected_score.value
                    ) for cursor in cursors]
                )
            )
        )

        get_by_id.assert_has_calls([call(cursor.id) for cursor in cursors])


class GetWatchers_TestCase(TestCase):
    @patch("CursorHandler.get_watchers_id")
    @patch("CursorHandler.get_cursor")
    def test_get_watchers(self, get_cursor: MagicMock, get_watchers_id: MagicMock):
        cur_main = Cursor.create("main")
        watchers = [Cursor.create("A"), Cursor.create("B")]

        get_watchers_id.return_value = [c.id for c in watchers]
        get_cursor.side_effect = watchers

        result = get_watchers(cur_main)

        self.assertListEqual(result, watchers)

        get_watchers_id.assert_called_once_with(cur_main.id)
        get_cursor.assert_has_calls(calls=[call(c.id) for c in watchers])
