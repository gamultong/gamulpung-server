from data.board import Point, PointRange, Tile, Tiles
from data.cursor import Cursor, Color
from data.conn.event import ServerEvent
from data.payload import DataPayload

from event.message import Message

from receiver import CursorReceiver

from handler.cursor import CursorEvent
from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from tests.utils import PathPatch, cases, override, MockSet, Wrapper as Wp
from unittest.mock import AsyncMock, MagicMock, call

MOCK_PATH = "receiver.internal.notify_cursor_state_changed"
patch = PathPatch(MOCK_PATH)


EXAMPLE_OLD_CURSOR = Cursor(
    conn_id="example",
    position=Point(0, 0),
    pointer=Point(0, 0),
    color=Color.BLUE,
    width=2,
    height=2
)

EXAMPLE_NEW_CURSOR = Cursor(
    conn_id="example",
    position=Point(0, 0),
    pointer=Point(0, 0),
    color=Color.RED,
    width=2,
    height=2
)

other_1 = EXAMPLE_OLD_CURSOR.copy()
other_1.conn_id = "other_1"

other_2 = EXAMPLE_OLD_CURSOR.copy()
other_2.conn_id = "other_2"
other_2.position = Point(1, 1)

other_3 = EXAMPLE_OLD_CURSOR.copy()
other_3.conn_id = "other_3"
other_3.position = Point(2, 2)

TARGETS = [
    other_1,
    other_2
]


class TilesStateEvent_TestCase(AsyncTestCase):
    @patch("multicast")
    @patch("CursorHandler.get_targets", return_value=TARGETS)
    @patch("CursorHandler.get", return_value=EXAMPLE_NEW_CURSOR)
    async def test_normal(
        self,
        get_cursor: AsyncMock,
        get_targets: AsyncMock,
        multicast: AsyncMock
    ):
        event_elem = ServerEvent.CursorsState.Elem(
            id=EXAMPLE_NEW_CURSOR.id,
            color=EXAMPLE_NEW_CURSOR.color
        )

        event = ServerEvent.CursorsState(
            cursors=[event_elem]
        )

        CursorReceiver.notify_cursor_state_changed(
            message=Message(
                CursorEvent.MOVED,
                payload=DataPayload(
                    id=EXAMPLE_OLD_CURSOR.id,
                    data=EXAMPLE_OLD_CURSOR
                )
            )
        )

        targets = [EXAMPLE_NEW_CURSOR.id]
        for cur in TARGETS:
            targets.append(cur.id)

        multicast.assert_called_once()
        call = multicast.mock_calls[0]
        self.assertCountEqual(
            call.kwargs["target_conns"],
            targets
        )

        self.assertEqual(
            call.kwargs["event"],
            event
        )
