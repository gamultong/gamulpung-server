from event.broker import EventBroker
from event.message import Message

from data.conn.event import ServerEvent, Empty

from data.cursor import Cursor
from data.score import Score

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call
from ..test_tools import get_cur_set, assertMulticast
from tests.utils import PathPatch, cases, override, MockSet, Wrapper as Wp
from utils.config import SCOREBOARD_SIZE

from receiver.internal.score.utils import (
    multicast_scoreboard_state,
)

MOCK_PATH = "receiver.internal.score.utils"
patch = PathPatch(MOCK_PATH)


class MulticastScoreboardState_TestCase(AsyncTestCase):
    @patch("multicast")
    async def test_normal(self, multicast: AsyncMock):
        cursor = Cursor.create("main")
        score = Score(cursor_id="main", value=1, rank=1)

        await multicast_scoreboard_state(
            target_conns=[cursor],
            scores=[score]
        )

        multicast.assert_called_once()

        event = ServerEvent.ScoreboardState(
            scores=[ServerEvent.ScoreboardState.Elem(
                rank=score.rank,
                score=score.value,
                before_rank=Empty
            )]
        )
        assertMulticast(self, multicast.mock_calls[0], target_conns=[cursor.id], event=event)
