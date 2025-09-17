from data.payload import DataPayload

from event.message import Message

from receiver import NotifyMyCursorReceiver

from handler.cursor import CursorEvent

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from tests.utils import PathPatch
from unittest.mock import AsyncMock, MagicMock, call
from ..test_tools import get_cur_set


MOCK_PATH = "receiver.internal.cursor.notify_my_cursor"
patch = PathPatch(MOCK_PATH)


class NotifyMyCursorReceiver_TestCase(AsyncTestCase):
    @patch("CursorHandler.get_watchers")
    @patch("multicast_cursors_state")
    @patch("multicast_my_cursor")
    async def test_notify_my_cursor(self, my_cursor: AsyncMock, cursors_state: AsyncMock, get_watchers: AsyncMock):
        (cursor, *watchers) = get_cur_set(3)

        get_watchers.return_value = watchers

        message = Message(
            event=CursorEvent.CREATED,
            payload=DataPayload(id=cursor.id, data=cursor)
        )

        await NotifyMyCursorReceiver.notify_my_cursor(message)

        my_cursor.assert_called_once_with(cursor)

        watchers.append(cursor)
        cursors_state.assert_called_once_with(target_conns=watchers, cursor=cursor)
