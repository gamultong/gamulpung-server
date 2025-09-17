from data.board import Point, PointRange, Tile, Tiles
from data.cursor import Cursor, Color
from data.conn.event import ServerEvent
from data.payload import DataPayload
from data.score import Score

from event.message import Message

from receiver import CursorReceiver
from receiver.internal.cursor import validate

from handler.cursor import CursorEvent
from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from tests.utils import PathPatch, cases, override, MockSet, Wrapper as Wp
from unittest.mock import AsyncMock, MagicMock, call

"""
1. window 변경에 대한 validate 
2. 추가적 Tile이 tiles-state의 총합에 포함되야함
3. 추가적 Cursor가 cursors-state에 포함되어야함
"""

# C -> Cursor(position -> 0, 0)
# width 변화  : 1 -> 2
# height 변화 : 1 -> 2

NEW_TILE = 0b11111111  # O
OLD_TILE = 0b00000000  # X
# OOOOO
# OXXXO
# OXCXO
# OXXXO
# OOOOO

MOCK_PATH = "receiver.internal.cursor"
patch = PathPatch(MOCK_PATH)

TILES_DATA = bytearray([
    NEW_TILE, NEW_TILE, NEW_TILE, NEW_TILE, NEW_TILE,
    NEW_TILE, OLD_TILE, OLD_TILE, OLD_TILE, NEW_TILE,
    NEW_TILE, OLD_TILE, OLD_TILE, OLD_TILE, NEW_TILE,
    NEW_TILE, OLD_TILE, OLD_TILE, OLD_TILE, NEW_TILE,
    NEW_TILE, NEW_TILE, NEW_TILE, NEW_TILE, NEW_TILE
])


EXAMPLE_TILES = Tiles(TILES_DATA)
EXAMPLE_OLD_CURSOR = Cursor(
    conn_id="example",
    position=Point(0, 0),
    pointer=Point(0, 0),
    color=Color.BLUE,
    width=1,
    height=1
)

old_cur_1 = EXAMPLE_OLD_CURSOR.copy()
old_cur_1.conn_id = "old_1"

old_cur_2 = EXAMPLE_OLD_CURSOR.copy()
old_cur_2.conn_id = "old_2"
old_cur_2.position = Point(1, 1)

new_cur_1 = EXAMPLE_OLD_CURSOR.copy()
new_cur_1.conn_id = "new_1"
new_cur_1.position = Point(2, 2)

OLD_TARGETS_R = Cursor.Targets(
    _id=EXAMPLE_OLD_CURSOR.id,
    relations=["old_1", "old_2"]
)

OLD_TARGETS = [
    old_cur_1,
    old_cur_2
]

EXAMPLE_OLD_CURSOR.sub[Cursor.Targets] = OLD_TARGETS_R

NEW_TARGETS_R = Cursor.Targets(
    _id=EXAMPLE_OLD_CURSOR.id,
    relations=["old_1", "old_2", "new_1"]
)

NEW_TARGETS = [
    old_cur_1,
    old_cur_2,
    new_cur_1
]

EXAMPLE_NEW_CURSOR = EXAMPLE_OLD_CURSOR.copy()
EXAMPLE_NEW_CURSOR.width = 2
EXAMPLE_NEW_CURSOR.height = 2

CUR_DICT = {
    cur.id: cur
    for cur in [
        EXAMPLE_NEW_CURSOR,
        old_cur_1,
        old_cur_2,
        new_cur_1
    ]
}


def get_cursor_stub(id: str):
    return CUR_DICT[id]


class Validate_TestCase(TestCase):
    # move
    case_1 = EXAMPLE_OLD_CURSOR.copy()
    case_1.position = Point(1, 1)

    # window scale_up 1
    case_2 = EXAMPLE_OLD_CURSOR.copy()
    case_2.width = 2

    # window scale_up 2
    case_3 = EXAMPLE_OLD_CURSOR.copy()
    case_3.height = 2

    @cases(
        [
            {"new_cur": case_1},
            {"new_cur": case_2},
            {"new_cur": case_3},
        ]
    )
    def test_pass_vaildate(self, new_cur: Cursor):
        res = validate(EXAMPLE_OLD_CURSOR, new_cur)

        self.assertTrue(res)

    # same
    case_1_OLD = EXAMPLE_OLD_CURSOR.copy()
    case_1_new = EXAMPLE_OLD_CURSOR.copy()

    # window scale_down
    case_2_OLD = EXAMPLE_OLD_CURSOR.copy()
    case_2_OLD.width = 2
    case_2_OLD.height = 2
    case_2_new = EXAMPLE_OLD_CURSOR.copy()

    @cases(
        [
            {"new_cur": case_1_new, "OLD_cur": case_1_OLD},
            {"new_cur": case_2_new, "OLD_cur": case_2_OLD},
        ]
    )
    def test_invaild(self, new_cur: Cursor, OLD_cur: Cursor):
        res = validate(OLD_cur, new_cur)

        self.assertFalse(res)


class TilesStateEvent_TestCase(AsyncTestCase):
    @patch("multicast")
    @patch("CursorHandler.get_targets", return_value=[])
    @patch("CursorHandler.get", side_effect=get_cursor_stub)
    @patch("BoardHandler.fetch", return_value=EXAMPLE_TILES)
    async def test_normal(
        self,
        fetch: AsyncMock,
        get_cursor: AsyncMock,
        get_targets: AsyncMock,
        multicast: AsyncMock
    ):
        exp_event_elem = ServerEvent.TilesState.Elem(
            range=PointRange(Point(-2, 2), Point(2, -2)),
            data=EXAMPLE_TILES.to_str()
        )

        exp_event = ServerEvent.TilesState(
            tiles=[exp_event_elem]
        )

        exp_call = call(

        )

        message = Message(
            event=CursorEvent.WINDOW_SIZE_SET,
            payload=DataPayload(
                id=EXAMPLE_OLD_CURSOR.id,
                data=EXAMPLE_OLD_CURSOR
            )
        )
        await CursorReceiver.notify_window_changed(message)

        multicast.assert_awaited_with(
            target_conns=[EXAMPLE_OLD_CURSOR.id],
            event=exp_event
        )


def get_score_stub(cur_id: str):
    return Score(
        cursor_id=cur_id,
        rank=0,
        value=0
    )


class CursorState_TestCase(AsyncTestCase):

    @patch("multicast")
    @patch("ScoreHandler.get", side_effect=get_score_stub)
    @patch("CursorHandler.get_targets", return_value=NEW_TARGETS)
    @patch("CursorHandler.get", side_effect=get_cursor_stub)
    @patch("BoardHandler.fetch", return_value=EXAMPLE_TILES)
    async def test_normal(
        self,
        fetch: AsyncMock,
        get_cursor: AsyncMock,
        get_targets: AsyncMock,
        get_score: AsyncMock,
        multicast: AsyncMock
    ):
        exp_event_elem_1 = ServerEvent.CursorsState.Elem(
            id=new_cur_1.id,
            position=new_cur_1.position,
            pointer=new_cur_1.pointer,
            color=new_cur_1.color,
            revive_at=new_cur_1.revive_at,
            score=0
        )
        exp_event = ServerEvent.CursorsState(
            cursors=[exp_event_elem_1]
        )

        message = Message(
            event=CursorEvent.WINDOW_SIZE_SET,
            payload=DataPayload(
                id=EXAMPLE_OLD_CURSOR.id,
                data=EXAMPLE_OLD_CURSOR
            )
        )
        await CursorReceiver.notify_window_changed(message)

        multicast.assert_awaited_with(
            target_conns=[EXAMPLE_OLD_CURSOR.id],
            event=exp_event
        )
