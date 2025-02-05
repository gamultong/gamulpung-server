from event.message import Message
from data.cursor import Cursor
from data.payload import EventEnum, CursorsPayload, CursorReviveAtPayload

from receiver.internal.utils import (
    multicast, watch, unwatch,
    publish_new_cursors
)

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import patch, AsyncMock, MagicMock

from .test_tools import assertMessageEqual, assertMulticast


class Multicast_TestCase(AsyncTestCase):
    @patch("event.broker.EventBroker.publish")
    async def test_normal(self, publish_mock: AsyncMock):
        target_conns = ["a", "b", "c"]
        message = Message(
            event="example_event",
            payload="example_payload"
        )

        await multicast(target_conns=target_conns, message=message)

        publish_mock.assert_called_once()
        got: Message = publish_mock.mock_calls[0].kwargs["message"]
        assertMessageEqual(
            self, got,
            Message(
                event="multicast",
                header={
                    "target_conns": target_conns,
                    "origin_event": message.event
                },
                payload=message.payload
            )
        )


cur_A = Cursor.create("A")
cur_B = Cursor.create("B")
cur_C = Cursor.create("C")
cur_D = Cursor.create("D")

watchers = [cur_A, cur_B]
watchings = [cur_C, cur_D]


class Watch_TestCase(TestCase):
    @patch("handler.cursor.CursorHandler.add_watcher")
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
    @patch("handler.cursor.CursorHandler.remove_watcher")
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
    @patch("receiver.internal.utils.multicast")
    async def test_normal(self, multicast: AsyncMock):
        cursors = [Cursor.create("A"), Cursor.create("B")]
        target_cursors = [Cursor.create("C"), Cursor.create("D")]

        await publish_new_cursors(
            target_cursors=target_cursors,
            cursors=cursors
        )

        multicast.assert_called_once()

        assertMulticast(
            self, multicast.mock_calls[0],
            target_conns=[cur.id for cur in target_cursors],
            message=Message(
                event=EventEnum.CURSORS,
                payload=CursorsPayload(
                    cursors=[CursorReviveAtPayload(
                        id=cursor.id,
                        position=cursor.position,
                        pointer=cursor.pointer,
                        color=cursor.color,
                        revive_at=cursor.revive_at.astimezone().isoformat() if cursor.revive_at is not None else None
                    ) for cursor in cursors]
                )
            )
        )
