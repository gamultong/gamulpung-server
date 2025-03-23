from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, 
    OpenTilePayload, TilesOpenedPayload,
    YouDiedPayload, CursorReviveAtPayload, CursorsPayload
)

from handler.board import BoardHandler
from handler.cursor import CursorHandler

from data.board import Point, Tile, Tiles, PointRange
from data.cursor import Cursor

from config import MINE_KILL_DURATION_SECONDS

from datetime import datetime, timedelta


from receiver.internal.open_tile import (
    OpenTileReceiver,
    get_tile_if_openable, detonate_mine, get_revive_at,
    get_nearby_alive_cursors, get_watchers_all, open_tile,
    multicast_tiles_opened, multicast_you_died, multicast_cursors_died
)

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call
from .test_tools import get_cur_set
from tests.utils import PathPatch

patch = PathPatch("receiver.internal.open_tile")


class GetTileIfOpenable_TestCase(AsyncTestCase):
    def setUp(self):
        self.cursor = Cursor.create("main")

        self.check_interactable_mock = MagicMock()
        self.cursor.check_interactable = self.check_interactable_mock
        self.cursor.check_interactable.return_value = True

        self.open_tile = Tile.create(
            is_open=True,
            is_mine=False,
            is_flag=False,
            color=None,
            number=1
        )
        self.closed_tile = Tile.create(
            is_open=False,
            is_mine=False,
            is_flag=False,
            color=None,
            number=1
        )

        self.closed_flag_tile = self.closed_tile.copy()
        self.closed_flag_tile.is_flag = True
        self.closed_flag_tile.color = self.cursor.color

        self.open_tile_tiles = Tiles(data=bytearray([self.open_tile.data]))
        self.closed_tile_tiles = Tiles(data=bytearray([self.closed_tile.data]))
        self.closed_flag_tile_tiles = Tiles(data=bytearray([self.closed_flag_tile.data]))

    @patch("BoardHandler.fetch")
    async def test_normal(self, fetch_mock: AsyncMock):
        fetch_mock.return_value = self.closed_tile_tiles

        result = await get_tile_if_openable(self.cursor)
        self.assertEqual(result, self.closed_tile)

    @patch("BoardHandler.fetch")
    async def test_not_interactable(self, fetch_mock: AsyncMock):
        self.cursor.check_interactable.return_value = False

        result = await get_tile_if_openable(self.cursor)
        self.assertIsNone(result)

    @patch("BoardHandler.fetch")
    async def test_tile_already_open(self, fetch_mock: AsyncMock):
        fetch_mock.return_value = self.open_tile_tiles

        result = await get_tile_if_openable(self.cursor)
        self.assertIsNone(result)

    @patch("BoardHandler.fetch")
    async def test_tile_has_flag(self, fetch_mock: AsyncMock):
        fetch_mock.return_value = self.closed_flag_tile_tiles

        result = await get_tile_if_openable(self.cursor)
        self.assertIsNone(result)


class GetReviveAt_TestCase(TestCase):
    @patch("datetime")
    def test_normal(self, datetime: MagicMock):
        time = datetime.now()
        datetime.now.return_value = time

        result = get_revive_at()
        self.assertEqual(result, time + MINE_KILL_DURATION_SECONDS)


class DetonateMine_TestCase(TestCase):
    def setUp(self):
        self.cur_a, self.cur_b = get_cur_set(2)
        self.cur_a.pointer = Point(1, 1)
        self.cur_b.pointer = Point(2, 1)

    @patch("get_nearby_alive_cursors")
    @patch("get_revive_at")
    def test_normal(self, get_revive_at: MagicMock, get_nearby_alive_cursors: MagicMock):
        now = datetime.now() + timedelta(days=1)
        point = Point(1, 1)

        get_nearby_alive_cursors.return_value = [self.cur_a, self.cur_b]
        get_revive_at.return_value = now

        result = detonate_mine(point)

        self.assertEqual(result, [self.cur_a, self.cur_b])

        self.assertEqual(self.cur_a.revive_at, now)
        self.assertEqual(self.cur_b.revive_at, now)
        self.assertIsNone(self.cur_a.pointer)
        self.assertIsNone(self.cur_b.pointer)


class GetNearbyAliveCursors_TestCase(TestCase):
    def setUp(self):
        self.cur_alive, self.cur_dead = get_cur_set(2)
        self.cur_dead.revive_at = datetime.now() + timedelta(days=1)

    @patch("CursorHandler.exists_range")
    def test_normal(self, exists_range: MagicMock):
        point = Point(0, 0)
        start_p, end_p = Point(-1, 1), Point(1, -1)

        exists_range.return_value = [self.cur_alive, self.cur_dead]

        result = get_nearby_alive_cursors(point)

        self.assertEqual(result, [self.cur_alive])

        exists_range.assert_called_once_with(start=start_p, end=end_p)


class GetWatchersAll_TestCase(TestCase):
    def setUp(self):
        self.cur_a, self.cur_b, self.cur_c, self.cur_d = get_cur_set(4)

        self.all_cursors = [self.cur_a, self.cur_b, self.cur_c, self.cur_d]
        self.cur_a_watcher_ids = [self.cur_c.id]
        self.cur_b_watcher_ids = [self.cur_d.id]

    @patch("CursorHandler.get_watchers_id")
    @patch("CursorHandler.get_cursor")
    def test_normal(self, get_cursor: MagicMock, get_watchers_id: MagicMock):
        def find_cursor_with_id(id: str):
            for cursor in self.all_cursors:
                if cursor.id == id:
                    return cursor

        get_cursor.side_effect = find_cursor_with_id
        get_watchers_id.side_effect = [self.cur_a_watcher_ids, self.cur_b_watcher_ids]

        result = get_watchers_all([self.cur_a, self.cur_b])
        self.assertCountEqual(result, self.all_cursors)

        self.assertEqual(len(get_cursor.mock_calls), len(self.all_cursors))
        get_watchers_id.assert_has_calls(
            calls=[
                call(cursor_id=self.cur_a.id),
                call(cursor_id=self.cur_b.id)
            ]
        )


class MulticastOpenTile_TestCase(AsyncTestCase):
    @patch("multicast")
    async def test_multicast_tiles_opened(self, mock: AsyncMock):
        cur_a, cur_b = get_cur_set(2)
        point_range = PointRange(Point(-1, 1), Point(1, -1))
        tiles_str = "fake"

        await multicast_tiles_opened(
            target_conns=[cur_a, cur_b],
            point_range=point_range,
            tiles_str=tiles_str
        )

        mock.assert_called_once_with(
            target_conns=[cur.id for cur in [cur_a, cur_b]],
            message=Message(
                event=EventCollection.TILES_OPENED,
                payload=TilesOpenedPayload(
                    start_p=point_range.top_left,
                    end_p=point_range.bottom_right,
                    tiles=tiles_str
                )
            )
        )

    @patch("multicast")
    async def test_multicast_you_died(self, mock: AsyncMock):
        cur_a, cur_b = get_cur_set(2)
        time = datetime.now() + timedelta(days=1)
        cur_a.revive_at, cur_b.revive_at = time, time

        await multicast_you_died(target_conns=[cur_a, cur_b])

        mock.assert_has_calls(calls=[
            call(
                target_conns=[cur_a.id],
                message=Message(
                    event=EventCollection.YOU_DIED,
                    payload=YouDiedPayload(revive_at=cur_a.revive_at.astimezone().isoformat())
                )
            ),
            call(
                target_conns=[cur_b.id],
                message=Message(
                    event=EventCollection.YOU_DIED,
                    payload=YouDiedPayload(revive_at=cur_b.revive_at.astimezone().isoformat())
                )
            )
        ])

    @patch("multicast")
    async def test_multicast_cursors_died(self, mock: AsyncMock):
        cur_a, cur_b = get_cur_set(2)
        target_conns = [cur_a, cur_b]
        cursors = [cur_a, cur_b]

        await multicast_cursors_died(target_conns=target_conns, cursors=cursors)

        mock.assert_called_once_with(
            target_conns=[cur.id for cur in [cur_a, cur_b]],
            message=Message(
                event=EventCollection.CURSORS_DIED,
                payload=CursorsPayload(
                    cursors=[CursorReviveAtPayload(
                        id=cursor.id,
                        position=cursor.position,
                        color=cursor.color,
                        revive_at=cursor.revive_at,
                        pointer=cursor.pointer
                    ) for cursor in cursors]
                )
            )
        )


class OpenTile_TestCase(AsyncTestCase):
    @patch("BoardHandler.open_tiles")
    async def test_normal(self, open_tiles: AsyncMock):
        tiles_str = "tiles string"
        start_p, end_p = Point(-1, 0), Point(0, -1)
        point = Point(0, 0)

        mock_tiles = MagicMock(Tiles)
        mock_tiles.to_str.return_value = tiles_str

        open_tiles.return_value = (start_p, end_p, mock_tiles)

        point_range, result_str = await open_tile(point)

        self.assertEqual(point_range, PointRange(start_p, end_p))
        self.assertEqual(result_str, tiles_str)

        open_tiles.assert_called_once_with(point)
        mock_tiles.hide_info.assert_called_once()
        mock_tiles.to_str.assert_called_once()


cursor_a = Cursor.create("A")
cursor_a.pointer = Point(1, 1)

view_cursors = get_cur_set(1)
dead_cursors = get_cur_set(2)
dead_cursor_watchers = get_cur_set(3)

normal_tile = Tile.create(
    is_open=True,
    is_mine=False,
    is_flag=False,
    color=None,
    number=1
)
mine_tile = normal_tile.copy()
mine_tile.is_mine = True
mine_tile.number = None

tiles_str = "tiles string"
open_range = PointRange(Point(0, 0), Point(0, 0))

example_message = Message(
    event=EventCollection.OPEN_TILE,
    header={"sender": cursor_a.id},
    payload=OpenTilePayload()
)


def mock_open_tile_receiver_dependency(func):
    func = patch("CursorHandler.get_cursor", return_value=cursor_a)(func)
    func = patch("get_tile_if_openable", return_value=normal_tile)(func)
    func = patch("open_tile", return_value=(open_range, tiles_str))(func)
    func = patch("CursorHandler.view_includes_range", return_value=view_cursors)(func)
    func = patch("multicast_tiles_opened")(func)
    func = patch("detonate_mine", return_value=dead_cursors)(func)
    func = patch("multicast_you_died")(func)
    func = patch("get_watchers_all", return_value=dead_cursor_watchers)(func)
    func = patch("multicast_cursors_died")(func)

    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


class OpenTileReceiver_TestCase(AsyncTestCase):
    @mock_open_tile_receiver_dependency
    async def test_normal(
        self,
        get_cursor: MagicMock,
        get_tile_if_openable: AsyncMock,
        open_tile: AsyncMock,
        view_includes_range: MagicMock,
        multicast_tiles_opened: AsyncMock,
        detonate_mine: AsyncMock,
        multicast_you_died: AsyncMock,
        get_watchers_all: MagicMock,
        multicast_cursors_died: AsyncMock
    ):
        await OpenTileReceiver.receive_open_tile(example_message)

        open_tile.assert_called_once_with(point=cursor_a.pointer)
        multicast_tiles_opened.assert_called_once_with(
            target_conns=view_cursors,
            point_range=open_range,
            tiles_str=tiles_str
        )

        detonate_mine.assert_not_called()
        multicast_you_died.assert_not_called()
        multicast_cursors_died.assert_not_called()

    @mock_open_tile_receiver_dependency
    async def test_tile_not_openable(
        self,
        get_cursor: MagicMock,
        get_tile_if_openable: AsyncMock,
        open_tile: AsyncMock,
        view_includes_range: MagicMock,
        multicast_tiles_opened: AsyncMock,
        detonate_mine: AsyncMock,
        multicast_you_died: AsyncMock,
        get_watchers_all: MagicMock,
        multicast_cursors_died: AsyncMock
    ):
        get_tile_if_openable.return_value = None

        await OpenTileReceiver.receive_open_tile(example_message)

        open_tile.assert_not_called()
        multicast_tiles_opened.assert_not_called()
        detonate_mine.assert_not_called()
        multicast_you_died.assert_not_called()
        multicast_cursors_died.assert_not_called()

    @mock_open_tile_receiver_dependency
    async def test_tile_is_mine(
        self,
        get_cursor: MagicMock,
        get_tile_if_openable: AsyncMock,
        open_tile: AsyncMock,
        view_includes_range: MagicMock,
        multicast_tiles_opened: AsyncMock,
        detonate_mine: MagicMock,
        multicast_you_died: AsyncMock,
        get_watchers_all: MagicMock,
        multicast_cursors_died: AsyncMock
    ):
        get_tile_if_openable.return_value = mine_tile

        await OpenTileReceiver.receive_open_tile(example_message)

        open_tile.assert_called_once_with(point=cursor_a.pointer)
        multicast_tiles_opened.assert_called_once_with(
            target_conns=view_cursors,
            point_range=open_range,
            tiles_str=tiles_str
        )
        detonate_mine.assert_called_once_with(point=cursor_a.pointer)
        multicast_you_died.assert_called_once_with(target_conns=dead_cursors)
        multicast_cursors_died.assert_called_once_with(target_conns=dead_cursor_watchers, cursors=dead_cursors)
