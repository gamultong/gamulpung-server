from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventEnum, CursorQuitPayload, ConnClosedPayload
)

from data.cursor import Cursor


from receiver.internal.conn_closed import (
    ConnClosedReceiver,
    get_watchers, get_watchings, multicast_cursor_quit
)

from .test_tools import get_cur_set, PathPatch

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call

patch = PathPatch("receiver.internal.conn_closed")


class MulticastCursorQuit_TestCase(AsyncTestCase):
    @patch("multicast")
    async def test_multicast_cursor_quit(self, mock: AsyncMock):
        cur_a, cur_b, cur_c = get_cur_set(3)

        await multicast_cursor_quit(
            target_conns=[cur_a, cur_b],
            cursor=cur_c
        )

        mock.assert_called_once_with(
            target_conns=[cur_a.id, cur_b.id],
            message=Message(
                event=EventEnum.CURSOR_QUIT,
                payload=CursorQuitPayload(id=cur_c.id)
            )
        )


class GetWatchers_TestCase(TestCase):
    @patch("CursorHandler.get_watchers_id")
    @patch("CursorHandler.get_cursor")
    def test_get_watchers(self, get_cursor: MagicMock, get_watchers_id: MagicMock):
        cur_main = Cursor.create("main")
        watchers = get_cur_set(3)

        get_watchers_id.return_value = [c.id for c in watchers]
        get_cursor.side_effect = watchers

        result = get_watchers(cur_main)

        self.assertListEqual(result, watchers)

        get_watchers_id.assert_called_once_with(cur_main.id)
        get_cursor.assert_has_calls(calls=[call(c.id) for c in watchers])


class GetWatchings_TestCase(TestCase):
    @patch("CursorHandler.get_watching_id")
    @patch("CursorHandler.get_cursor")
    def test_get_watchings(self, get_cursor: MagicMock, get_watching_id: MagicMock):
        cur_main = Cursor.create("main")
        watchers = get_cur_set(3)

        get_watching_id.return_value = [c.id for c in watchers]
        get_cursor.side_effect = watchers

        result = get_watchings(cur_main)

        self.assertListEqual(result, watchers)

        get_watching_id.assert_called_once_with(cur_main.id)
        get_cursor.assert_has_calls(calls=[call(c.id) for c in watchers])


cursor_a = Cursor.create("A")
cursors = get_cur_set(3)


def mock_conn_closed_receiver_dependency(func):
    func = patch("CursorHandler.get_cursor", return_value=cursor_a)(func)
    func = patch("CursorHandler.remove_cursor")(func)
    func = patch("get_watchers", return_value=cursors)(func)
    func = patch("get_watchings", return_value=cursors)(func)
    func = patch("unwatch")(func)
    func = patch("multicast_cursor_quit")(func)

    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


class ConnClosedReceiver_TestCase(AsyncTestCase):
    def setUp(self):
        self.input_message = Message(
            event=EventEnum.CONN_CLOSED,
            header={"sender": cursor_a.id},
            payload=ConnClosedPayload()
        )

    @mock_conn_closed_receiver_dependency
    async def test_normal(
            self,
            get_cursor: MagicMock,
            remove_cursor: MagicMock,
            get_watchers: MagicMock,
            get_watchings: MagicMock,
            unwatch: MagicMock,
            multicast_cursor_quit: AsyncMock
    ):

        await ConnClosedReceiver.receive_conn_closed(self.input_message)

        unwatch.assert_has_calls([
            call(watchers=[cursor_a], watchings=cursors),
            call(watchers=cursors, watchings=[cursor_a]),
        ])
        remove_cursor.assert_called_once_with(cursor_a.id)
        multicast_cursor_quit.assert_called_once_with(
            target_conns=cursors, cursor=cursor_a
        )
