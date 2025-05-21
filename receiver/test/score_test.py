# state 변경

# score create -> score.id -> 새로 들어온 커서
# 새로운 커서 -> 얘는 scoreboad 정보가 하나도 없음
# -> 다 줘야 함

# watched(본인 포함) -> score 전달
# if scoreboard 변동시:
#     fetch scoreboard -> 변경 사항 전달 -> broadcast


from event.broker import EventBroker
from event.message import Message
from event.payload import Empty
from data.payload import (
    EventCollection,
    EventCollection, DataPayload
)

from data.conn.event import ServerEvent

from data.board import Point, Tile, Tiles
from data.cursor import Cursor, Color
from data.score import Score


from handler.score import ScoreEvent

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call
from .test_tools import get_cur_set
from tests.utils import PathPatch, cases, override, MockSet, Wrapper as Wp
from config import SCOREBOARD_SIZE

from receiver.internal.score import (
    ScoreReceiver,
    deliver_whole_scoreboard,
    multicast_scoreboard_state,
    fetch_scoreboard,
    get_rank_changed_range
)

MOCK_PATH = "receiver.internal.score"
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


class MulticastScoreboardState_TestCase(AsyncTestCase):
    @patch("multicast")
    async def test_normal(self, multicast: AsyncMock):
        cursor = Cursor.create("main")
        score = Score(cursor_id="main", value=1, rank=1)

        await multicast_scoreboard_state(
            target_conns=[cursor],
            scores=[score]
        )

        multicast.assert_called_once_with(
            target_conns=[cursor.id],
            message=Message(
                event=EventCollection.SCOREBOARD_STATE,
                payload=ServerEvent.ScoreboardState(
                    scores=[ServerEvent.ScoreboardState.Elem(
                        rank=score.rank,
                        score=score.value,
                        before_rank=Empty
                    )]
                )
            )
        )


# def cal(old, new):
#     return (1, 2)


# scores = fetch_scoreboard(*get_rank_changed_range(None, None))
# await broadcast_scoreboard_state(scores)
cursor_a = Cursor.create("A")
scoreboard = SCOREBOARD_STUB
changed_range = (1, 2)
current_score = Score(
    cursor_id=cursor_a.id,
    rank=1,
    value=0
)


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

        await ScoreReceiver.notify_score_changed(self.input_message)

        mock.broadcast_scoreboard_state.assert_called_once_with(scoreboard)


class SendInitialScoreBoard_MockSet(MockSet):
    __path__ = MOCK_PATH

    get_cursor: Wp[MagicMock] = override("CursorHandler.get_cursor", return_value=cursor_a)
    deliver_whole_scoreboard: Wp[MagicMock] = override("deliver_whole_scoreboard")


class SendInitialScoreBoard_TestCase(AsyncTestCase):
    @SendInitialScoreBoard_MockSet.patch()
    async def test_created(self, mock: SendInitialScoreBoard_MockSet):
        input_message = Message(
            event=ScoreEvent.CREATED,
            payload=DataPayload(id=None),
        )

        await ScoreReceiver.send_initial_scoreboard(input_message)

        mock.deliver_whole_scoreboard.assert_called_once_with(cursor_a)
