from data.board import Point, PointRange, Tile, Tiles
from data.cursor import Cursor, Color
from data.conn.event import ServerEvent
from data.payload import DataPayload
from data.score import Score

from event.message import Message

from receiver import CursorReceiver

from handler.cursor import CursorEvent
from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from tests.utils import PathPatch
from unittest.mock import AsyncMock, MagicMock, call
from .test_tools import get_cur_set


MOCK_PATH = "receiver.internal.cursor"
patch = PathPatch(MOCK_PATH)


class CursorReceiver_TestCase(AsyncTestCase):
    @patch("multicast_my_cursor")
    @patch("ScoreHandler.create")
    async def test_normal(self, create: AsyncMock, multicast_my_cursor: AsyncMock):
        (cursor,) = get_cur_set(1)

        message = Message(
            event=CursorEvent.CREATED,
            payload=DataPayload(id=cursor.id, data=cursor)
        )

        await CursorReceiver.cursor_created(message)

        create.assert_called_once_with(id=cursor.id)
        multicast_my_cursor.assert_called_once_with(cursor)
