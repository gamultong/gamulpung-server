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

from receiver.internal.score.send_initial_scoreboard import (
    SendInitialScoreboardReceiver,
    deliver_whole_scoreboard,
)


MOCK_PATH = "receiver.internal.score.send_initial_scoreboard"
patch = PathPatch(MOCK_PATH)


# scoreboard size 넘기면 -> scoreboard만큼만 줘야함
SCOREBOARD_STUB = [
    Score(f"id_{i}", i, i)
    for i in range(1, SCOREBOARD_SIZE + 3)  # SCOREBOARD_SIZE 보다 2개 많음
]


def get_by_rank_stub(start: int, end: int | None = None) -> tuple[Score]:
    return SCOREBOARD_STUB[start-1:end]


class DeliverWholeScoreBoard_MockSet(MockSet):
    __path__ = MOCK_PATH

    get_by_rank: Wp[AsyncMock] = override("ScoreHandler.get_by_rank")
    length: Wp[AsyncMock] = override("ScoreHandler.length")
    multicast_scoreboard_state: Wp[AsyncMock] = override("multicast_scoreboard_state")


class DeliverWholeScoreBoard_TestCase(AsyncTestCase):
    @DeliverWholeScoreBoard_MockSet.patch(
        override("length", return_value=SCOREBOARD_SIZE + 2),
        override("get_by_rank", side_effect=get_by_rank_stub)
    )
    async def test_normal(self, mock: DeliverWholeScoreBoard_MockSet):
        cursor = Cursor.create("main")

        await deliver_whole_scoreboard(cursor)

        mock.multicast_scoreboard_state.assert_called_once_with(
            target_conns=[cursor],
            scores=SCOREBOARD_STUB[:SCOREBOARD_SIZE]
        )

    @DeliverWholeScoreBoard_MockSet.patch(
        override("length", return_value=SCOREBOARD_SIZE - 2),
        override("get_by_rank", side_effect=get_by_rank_stub),
    )
    async def test_normal(self, mock: DeliverWholeScoreBoard_MockSet):
        cursor = Cursor.create("main")

        await deliver_whole_scoreboard(cursor)

        mock.multicast_scoreboard_state.assert_called_once_with(
            target_conns=[cursor],
            scores=SCOREBOARD_STUB[:SCOREBOARD_SIZE-2]
        )


(cursor_a,) = get_cur_set(1)


class SendInitialScoreBoard_MockSet(MockSet):
    __path__ = MOCK_PATH

    get_cursor: Wp[AsyncMock] = override("CursorHandler.get", return_value=cursor_a)
    deliver_whole_scoreboard: Wp[MagicMock] = override("deliver_whole_scoreboard")


class SendInitialScoreBoard_TestCase(AsyncTestCase):
    @SendInitialScoreBoard_MockSet.patch()
    async def test_created(self, mock: SendInitialScoreBoard_MockSet):
        input_message = Message(
            event=ScoreEvent.CREATED,
            payload=DataPayload(id=None),
        )

        await SendInitialScoreboardReceiver.send_initial_scoreboard(input_message)

        mock.deliver_whole_scoreboard.assert_called_once_with(cursor_a)
