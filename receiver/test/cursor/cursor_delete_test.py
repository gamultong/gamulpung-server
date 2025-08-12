from data.payload import DataPayload

from event.message import Message

from receiver import DeleteCursorReceiver

from handler.cursor import CursorEvent

from unittest import IsolatedAsyncioTestCase as AsyncTestCase
from tests.utils import PathPatch
from unittest.mock import AsyncMock
from ..test_tools import get_cur_set

MOCK_PATH = "receiver.internal.cursor.cursor_delete"
patch = PathPatch(MOCK_PATH)


class DeleteCursorReceiver_TestCase(AsyncTestCase):
    @patch("multicast_cursor_delete")
    @patch("ScoreHandler.delete")
    async def test_normal(self, scorehandler_delete: AsyncMock, multicast_cursor_delete: AsyncMock):
        cursor, *_ = get_cur_set(1)

        message = Message(
            event=CursorEvent.DELETE,
            payload=DataPayload(id=cursor.id, data=cursor)
        )

        await DeleteCursorReceiver.cursor_delete(message)

        scorehandler_delete.assert_called_once_with(
            id=cursor.id
        )

        multicast_cursor_delete.assert_awaited_once_with(
            target_conns=[cursor]
        )


if __name__ == "__main__":
    from unittest import main
    main()
