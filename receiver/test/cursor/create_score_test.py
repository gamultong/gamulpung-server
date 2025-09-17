from data.payload import DataPayload

from event.message import Message

from receiver import CreateScoreReceiver

from handler.cursor import CursorEvent

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from tests.utils import PathPatch
from unittest.mock import AsyncMock, MagicMock, call
from ..test_tools import get_cur_set


MOCK_PATH = "receiver.internal.cursor.create_score"
patch = PathPatch(MOCK_PATH)


class CreateScoreReceiver_TestCase(AsyncTestCase):
    @patch("ScoreHandler.create")
    async def test_create_score(self, create: AsyncMock):
        (cursor,) = get_cur_set(1)

        message = Message(
            event=CursorEvent.CREATED,
            payload=DataPayload(id=cursor.id, data=cursor)
        )

        await CreateScoreReceiver.rcreate_score(message)

        create.assert_called_once_with(id=cursor.id)
