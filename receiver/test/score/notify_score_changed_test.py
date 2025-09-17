from event.broker import EventBroker
from event.message import Message
from event.payload import Empty

from data.conn.event import ServerEvent

from data.cursor import Cursor
from data.score import Score

from data.payload import DataPayload

from handler.score import ScoreEvent

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call
from ..test_tools import get_cur_set, assertMulticast
from tests.utils import PathPatch, cases, override, MockSet, Wrapper as Wp
from config import SCOREBOARD_SIZE

from receiver.internal.score.notify_score_changed import (
    NotifyScoreChangedReceiver,
    fetch_scoreboard,
    get_rank_changed_range
)

MOCK_PATH = "receiver.internal.score.notify_score_changed"
patch = PathPatch(MOCK_PATH)


# scoreboard size 넘기면 -> scoreboard만큼만 줘야함
SCOREBOARD_STUB = [
    Score(f"id_{i}", i, i)
    for i in range(1, SCOREBOARD_SIZE + 3)  # SCOREBOARD_SIZE 보다 2개 많음
]


def get_by_rank_stub(start: int, end: int | None = None) -> tuple[Score]:
    return SCOREBOARD_STUB[start-1:end]


class GetRankChangedRange_TestCase(AsyncTestCase):
    @patch("ScoreHandler.length")
    async def test_normal(self, mock: AsyncMock):
        old, new = Score(cursor_id="A", rank=1, value=0), Score(cursor_id="B", rank=2, value=0)

        start, end = await get_rank_changed_range(old, new)

        self.assertEqual(start, 1)
        self.assertEqual(end, 2)

    @patch("ScoreHandler.length")
    async def test_reversed(self, mock: AsyncMock):
        old, new = Score(cursor_id="B", rank=2, value=0), Score(cursor_id="A", rank=1, value=0)

        start, end = await get_rank_changed_range(old, new)

        self.assertEqual(start, 1)
        self.assertEqual(end, 2)

    @patch("ScoreHandler.length")
    async def test_old_none(self, mock: AsyncMock):
        last = 5
        mock.return_value = last

        old, new = None, Score(cursor_id="A", rank=1, value=0)

        start, end = await get_rank_changed_range(old, new)

        self.assertEqual(start, 1)
        self.assertEqual(end, min(last, SCOREBOARD_SIZE))

    @patch("ScoreHandler.length")
    async def test_new_none(self, mock: AsyncMock):
        last = 5
        mock.return_value = last

        old, new = Score(cursor_id="A", rank=1, value=0), None

        start, end = await get_rank_changed_range(old, new)

        self.assertEqual(start, 1)
        self.assertEqual(end, min(last, SCOREBOARD_SIZE))


class FetchScoreboard_TestCase(AsyncTestCase):
    @patch("ScoreHandler.get_by_rank")
    async def test_normal(self, mock: AsyncMock):
        mock.side_effect = get_by_rank_stub

        result = await fetch_scoreboard(1, SCOREBOARD_SIZE-3)

        self.assertEqual(result, SCOREBOARD_STUB[0: SCOREBOARD_SIZE-3])

        mock.assert_called_once_with(
            1, SCOREBOARD_SIZE-3
        )


(cursor_a, ) = get_cur_set(1)
scoreboard = []
changed_range = (Score("a", 1, 1), Score("b", 0, 2))
current_score = Score("cur", 1, 1)


class NotifiyScoreChanged_MockSet(MockSet):
    __path__ = MOCK_PATH

    fetch_scoreboard: Wp[AsyncMock] = override("fetch_scoreboard", return_value=scoreboard)
    get_rank_changed_range: Wp[AsyncMock] = override("get_rank_changed_range", return_value=changed_range)
    get_current_score: Wp[AsyncMock] = override("get_current_score", return_value=current_score)
    broadcast_scoreboard_state: Wp[AsyncMock] = override("broadcast_scoreboard_state")


class NotifiyScoreChanged_TestCase(AsyncTestCase):
    def setUp(self):
        self.input_message = Message(
            event=ScoreEvent.UPDATED,
            payload=DataPayload(
                id=cursor_a.id,
                data=Score(
                    cursor_id=cursor_a.id,
                    rank=1,
                    value=0
                )
            )
        )

    @cases([
        {"event": ScoreEvent.DELETED},
        {"event": ScoreEvent.UPDATED},
        {"event": ScoreEvent.CREATED}
    ])
    @NotifiyScoreChanged_MockSet.patch()
    async def test_normal(
        self,
        mock: NotifiyScoreChanged_MockSet,
        event: ScoreEvent,
    ):
        self.input_message.event = event

        await NotifyScoreChangedReceiver.notify_score_changed(self.input_message)

        mock.broadcast_scoreboard_state.assert_called_once_with(scoreboard)
