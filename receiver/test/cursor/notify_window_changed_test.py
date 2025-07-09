from data.board import Point, PointRange, Tile, Tiles
from data.cursor import Cursor, Color
from data.conn.event import ServerEvent
from data.payload import DataPayload
from data.score import Score
from data.base.utils import Relation

from event.message import Message

from receiver import NotifyWindowChangedReceiver
from receiver.internal.cursor.notify_window_changed import (
    is_omittable, multicast_cursor_state_event, multicast_tiles_state_event,
    get_new_targets, fetch_delta_tiles,
)

from handler.cursor import CursorEvent
from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from tests.utils import PathPatch,  override, MockSet, Wrapper as Wp
from unittest.mock import AsyncMock, MagicMock, call

from ..test_tools import get_cur_set

MOCK_PATH = "receiver.internal.cursor.notify_window_changed"
patch = PathPatch(MOCK_PATH)


(CURSOR, CURSOR2) = get_cur_set(2)


class IsOmittable_TestCase(TestCase):
    def test_different_position(self):
        temp = CURSOR.copy()
        temp.position = Point(1, 1)

        self.assertFalse(is_omittable(CURSOR, temp))

    def test_width_grow(self):
        temp = CURSOR.copy()
        temp.width = temp.width + 1

        self.assertFalse(is_omittable(CURSOR, temp))

    def test_height_grow(self):
        temp = CURSOR.copy()
        temp.height = temp.height + 1

        self.assertFalse(is_omittable(CURSOR, temp))

    def test_omittable(self):
        temp = CURSOR.copy()
        temp.width = temp.width - 1  # shrink -> omittable

        self.assertTrue(is_omittable(CURSOR, temp))


class MulticastCursorStateEvent_TestCase(AsyncTestCase):
    @patch("multicast")
    @patch("ScoreHandler.get", return_value=Score(cursor_id="", value=1))
    async def test_normal(self, score_get: AsyncMock, multicast: AsyncMock):
        [cursor, *target_conns] = get_cur_set(4)

        await multicast_cursor_state_event(target_conns=target_conns, cursors=[cursor])

        expected_event = ServerEvent.CursorsState(
            cursors=[
                ServerEvent.CursorsState.Elem(
                    id=cursor.id,
                    color=cursor.color,
                    pointer=cursor.pointer,
                    position=cursor.position,
                    revive_at=cursor.revive_at,
                    score=1,
                )
            ]
        )

        multicast.assert_called_once_with(
            target_conns=[c.id for c in target_conns],
            event=expected_event
        )


class GetNewTargets_TestCase(AsyncTestCase):
    @patch("CursorHandler.get_targets", return_value=[CURSOR2.copy()])
    async def test_normal(self, get_targets: AsyncMock):
        old_cursor = CURSOR.copy()
        old_cursor.sub[Cursor.Targets] = Relation(_id=old_cursor.id, relations=[])

        new_cursor = CURSOR.copy()  # doesn't matter

        new_targets = await get_new_targets(old_cursor=old_cursor, new_cursor=new_cursor)

        self.assertEqual(new_targets, [CURSOR2.copy()])


NEW_TILE = 0b11111111  # O
OLD_TILE = 0b00000000  # X
# OOOOO
# OXXXO
# OXCXO
# OXXXO
# OOOOO

EXAMPLE_TILES = Tiles(bytearray([
    NEW_TILE, NEW_TILE, NEW_TILE, NEW_TILE, NEW_TILE,
    NEW_TILE, OLD_TILE, OLD_TILE, OLD_TILE, NEW_TILE,
    NEW_TILE, OLD_TILE, OLD_TILE, OLD_TILE, NEW_TILE,
    NEW_TILE, OLD_TILE, OLD_TILE, OLD_TILE, NEW_TILE,
    NEW_TILE, NEW_TILE, NEW_TILE, NEW_TILE, NEW_TILE
]))


class FetchDeltaTiles_TestCase(AsyncTestCase):
    @patch("BoardHandler.fetch", return_value=EXAMPLE_TILES.copy())
    async def test_normal(self, fetch: AsyncMock):
        range = PointRange(Point(0, 0), Point(0, 0))

        tiles = await fetch_delta_tiles(range)

        self.assertEqual(tiles, EXAMPLE_TILES.copy())
        fetch.assert_called_once_with(range.top_left, range.bottom_right)


class MulticastTilesStateEvent_TestCase(AsyncTestCase):
    @patch("multicast")
    async def test_normal(self, multicast: AsyncMock):
        target_conns = get_cur_set(2)
        range = PointRange(Point(0, 0), Point(0, 0))
        tiles = EXAMPLE_TILES.copy()

        await multicast_tiles_state_event(target_conns=target_conns, range=range, tiles_list=[tiles])

        expected_event = ServerEvent.TilesState(
            tiles=[
                ServerEvent.TilesState.Elem(
                    range=range,
                    data=tiles.to_str()
                )
            ]
        )

        multicast.assert_called_once_with(
            target_conns=[c.id for c in target_conns],
            event=expected_event
        )


class NotifyWindowChangedReceiver_MockSet(MockSet):
    __path__ = MOCK_PATH

    cursor_get: Wp[AsyncMock] = override("CursorHandler.get", return_value=CURSOR.copy())
    fetch_delta_tiles: Wp[AsyncMock] = override("fetch_delta_tiles", return_value=Tiles(data=bytearray()))
    multicast_tiles_state_event: Wp[AsyncMock] = override("multicast_tiles_state_event")
    multicast_cursor_state_event: Wp[AsyncMock] = override("multicast_cursor_state_event")
    get_new_targets: Wp[AsyncMock] = override("get_new_targets", return_value=[CURSOR2.copy()])


class NotifyWindowChangedReceiver_TestCase(AsyncTestCase):
    @NotifyWindowChangedReceiver_MockSet.patch()
    async def test_normal(self, mock: NotifyWindowChangedReceiver_MockSet):
        old_cur = CURSOR.copy()
        old_cur.position = Point(1, 1)

        message = Message(
            event=CursorEvent.WINDOW_SIZE_SET,
            payload=DataPayload(id=old_cur.id, data=old_cur)
        )

        await NotifyWindowChangedReceiver.notify_window_changed(message)

        mock.multicast_tiles_state_event.assert_called_once_with(
            target_conns=[CURSOR.copy()],
            range=CURSOR.copy().view_range,
            tiles_list=[Tiles(data=bytearray())]
        )
        mock.multicast_cursor_state_event.assert_called_once_with(
            target_conns=[CURSOR.copy()],
            cursors=[CURSOR2.copy()]
        )
