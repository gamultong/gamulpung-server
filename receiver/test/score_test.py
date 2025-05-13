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
from tests.utils import PathPatch, cases
from config import SCOREBOARD_SIZE

from receiver.internal.score import (
    ScoreReceiver,
    deliver_whole_scoreboard,
    multicast_scoreboard_state,
    fetch_scoreboard,
    get_rank_changed_range
)

patch = PathPatch("receiver.internal.score")

"""
1. score_id로 score 가져오기
-> scorehandler.get_by_id()

2. watcher 구하기
3. multicast하기


스코어보드에 걸리는 변경
# is_in_scoreboard


DataSet[Score]:
    old_data
    new_data

data -> old, new
receiver -> singleton 
receiver 객체 생성

old_data, new_data -> 객체 state

if -> scoreboard에 표시되는 score인가 <- 이전 혹은 현재가

    # chaged_score_in_scoreboard(DataSet[score]) -> list[score]
    fetch -> 인정 
    fetch -> 인정
    
    range -> 

    # 스코어 보드 포함되는 범위만 fetch
    4. 이전 데이터 랭크 + 현재 데이터 랭크 범위로 score fetch
        데이터 랭크 변경 일어날 시 가장 높은 것 부터 낮은 것 까지 모두 랭크 변경 일어남 -> 이거 다 fetch    
    5. broadcast

+ create면 본인에게 boardscore 전달
"""

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


class DeliverWholeScoreBoard_TestCase(AsyncTestCase):
    @patch("ScoreHandler.get_by_rank")
    @patch("ScoreHandler.length")
    @patch("multicast_scoreboard_state")
    async def test_normal(self, multicast_scoreboard_state: AsyncMock, length: AsyncMock, get_by_rank: AsyncMock):
        cursor = Cursor.create("main")

        length.return_value = SCOREBOARD_SIZE + 2
        get_by_rank.side_effect = get_by_rank_stub

        await deliver_whole_scoreboard(cursor)

        multicast_scoreboard_state.assert_called_once_with(
            target_conns=[cursor],
            scores=SCOREBOARD_STUB[:SCOREBOARD_SIZE]
        )

    @patch("ScoreHandler.get_by_rank")
    @patch("ScoreHandler.length")
    @patch("multicast_scoreboard_state")
    async def test_normal(self, multicast_scoreboard_state: AsyncMock, length: AsyncMock, get_by_rank: AsyncMock):
        cursor = Cursor.create("main")

        length.return_value = SCOREBOARD_SIZE - 2
        get_by_rank.side_effect = get_by_rank_stub

        await deliver_whole_scoreboard(cursor)

        multicast_scoreboard_state.assert_called_once_with(
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


def mock_score_receiver_dependency(func):
    func = patch("CursorHandler.get_cursor", return_value=cursor_a)(func)
    func = patch("deliver_whole_scoreboard")(func)
    func = patch("fetch_scoreboard", return_value=scoreboard)(func)
    func = patch("get_rank_changed_range", return_value=changed_range)(func)
    func = patch("get_current_score", return_value=current_score)(func)
    func = patch("broadcast_scoreboard_state")(func)

    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


class ScoreReceiver_TestCase(AsyncTestCase):
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
        {"event": ScoreEvent.UPDATED}
    ])
    @mock_score_receiver_dependency
    async def test_normal(
        self,
        get_cursor: MagicMock,
        deliver_whole_scoreboard: AsyncMock,
        fetch_scoreboard: AsyncMock,
        get_rank_changed_range: AsyncMock,
        get_current_score: AsyncMock,
        broadcast_scoreboard_state: AsyncMock,
        event: ScoreEvent,
    ):
        self.input_message.event = event

        await ScoreReceiver.notify_score_changed(self.input_message)

        broadcast_scoreboard_state.assert_called_once_with(scoreboard)

    @mock_score_receiver_dependency
    async def test_created(self,
                           get_cursor: MagicMock,
                           deliver_whole_scoreboard: AsyncMock,
                           fetch_scoreboard: AsyncMock,
                           get_rank_changed_range: AsyncMock,
                           get_current_score: AsyncMock,
                           broadcast_scoreboard_state: AsyncMock
                           ):
        self.input_message.event = ScoreEvent.CREATED
        self.input_message.payload.data = None

        await ScoreReceiver.notify_score_changed(self.input_message)

        # deliver_whole_scoreboard.assert_called_once_with(cursor_a)
        broadcast_scoreboard_state.assert_called_once_with(scoreboard)
