from data.payload import DataPayload
from data.score import Score
from datetime import datetime, timedelta

from event.message import Message

from receiver import CursorDeathReceiver

from handler.cursor import CursorEvent

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from tests.utils import PathPatch
from unittest.mock import AsyncMock, MagicMock, call
from ..test_tools import get_cur_set


MOCK_PATH = "receiver.internal.cursor.death"
patch = PathPatch(MOCK_PATH)


class CursorReceiver_TestCase(AsyncTestCase):
    @patch("ScoreHandler.get")
    @patch("move_to_persistent_scores")
    @patch("reserve_revival")
    async def test_cursor_death(self, reserve: AsyncMock, persist: AsyncMock, get: AsyncMock):
        (cursor,) = get_cur_set(1)

        cursor.revive_at = datetime.now() + timedelta(hours=1)
        score = Score(cursor_id=cursor.id, value=10, rank=None)

        get.return_value = score

        message = Message(
            event=CursorEvent.DEATH,
            payload=DataPayload(id=cursor.id, data=cursor)
        )

        await CursorDeathReceiver.cursor_death(message)

        reserve.assert_called_once_with(cursor)
        persist.assert_called_once_with(score)


class MoveToPersistentScores_TestCase(AsyncTestCase):
    async def test_normal(self):
        # TODO: 추가
        pass


class ReserveRevival_TestCase(AsyncTestCase):
    async def test_normal(self):
        # TODO: 추가
        pass
