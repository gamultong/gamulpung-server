from event.message import Message

from data.board import Point, Tiles, Tile
from data.cursor import Cursor
from data.payload import (
    NewConnPayload, EventCollection,
    MyCursorPayload, TilesPayload
)
from config import WINDOW_SIZE_LIMIT

from receiver.internal.new_conn import (
    NewConnReceiver,
    new_cursor, fetch_with_view_including, fetch_cursors_in_view,
    multicast_my_cursor, multicast_tiles
)

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call
from .test_tools import get_cur_set
from tests.utils import PathPatch

patch = PathPatch("receiver.internal.new_conn")

example_cursors = get_cur_set(4)

class FetchWithviewIncluding_TestCase(TestCase):
    @patch("CursorHandler.view_includes_point")
    def test_normal(self, mock:MagicMock):
        cursor = example_cursors[0]

        mock.return_value = example_cursors

        result = fetch_with_view_including(cursor)

        mock.assert_called_once_with(cursor.position, exclude_ids=[cursor.id])
        
        self.assertEqual(result, example_cursors)
        


class FetchCursorsInView_TestCase(TestCase):
    @patch("CursorHandler.exists_range")
    @patch("get_view_range_points")
    def test_normal(self, get_view_range_points:MagicMock, exists_range:MagicMock):
        cursor = example_cursors[0]
        start, end = Point(0, 0), Point(1, -1)

        get_view_range_points.return_value = (start, end)
        exists_range.return_value = example_cursors

        result = fetch_cursors_in_view(cursor)

        get_view_range_points.assert_called_once_with(cursor.position, cursor.width, cursor.height)
        exists_range.assert_called_once_with(start=start, end=end, exclude_ids=[cursor.id])

        self.assertEqual(result, example_cursors)

class NewCursor_TestCase(AsyncTestCase):
    @patch("CursorHandler.create_cursor")
    @patch("BoardHandler.get_random_open_position")
    @patch("ScoreHandler.create")
    async def test_normal(
            self, 
            create_score: AsyncMock,
            get_random_open_position:AsyncMock, 
            create_cursor:MagicMock
        ):
        cursor_id = "A"
        position = Point(1, 1)
        width, height = 1, 1

        cursor = Cursor.create(cursor_id)

        get_random_open_position.return_value = position
        create_cursor.return_value = cursor

        result = await new_cursor(cursor_id, width, height)

        get_random_open_position.assert_called_once()
        create_cursor.assert_called_once_with(
            conn_id=payload.conn_id,
            position=position,
            width=payload.width, 
            height=payload.height
        )
        create_score.assert_called_once_with(cursor_id)

        self.assertEqual(result, cursor)

class NewConnMulticast_TestCase(AsyncTestCase):
    @patch("multicast")
    async def test_multicast_my_cursor(self, mock:AsyncMock):
        cursor_a = Cursor.create("A")
        cursor_b = Cursor.create("B")

        expected_message = Message(
            event=EventCollection.MY_CURSOR,
            payload=MyCursorPayload(
                id=cursor_a.id,
                color=cursor_a.color,
                pointer=cursor_a.pointer,
                position=cursor_a.position
            )
        )

        await multicast_my_cursor(
            target_conns=[cursor_b],
            cursor=cursor_a
        )

        mock.assert_called_once_with(
            target_conns=[cursor_b.id],
            message=expected_message
        )
    
    @patch("multicast")
    async def test_multicast_tiles(self, mock:AsyncMock):
        cursor = Cursor.create("A")
        start, end = Point(0, 0), Point(1, 1)
        tiles = Tiles(data=bytearray())

        expected_message = Message(
            event=EventCollection.TILES,
            payload=TilesPayload(
                start_p=start,
                end_p=end,
                tiles=tiles.to_str()
            )
        )

        await multicast_tiles(
            target_conns=[cursor],
            start=start, end=end, tiles=tiles
        )

        mock.assert_called_once_with(
            target_conns=[cursor.id],
            message=expected_message
        )

# ============================================================

cursor_a = Cursor.create("A")
start, end = Point(0, 0), Point(1, -1)
tiles = Tiles(data=bytearray())
payload = NewConnPayload(conn_id="A", width=1, height=1)
example_input = Message(
    event=EventCollection.NEW_CONN,
    payload=payload
)

cursor_b = Cursor.create("B")
cursor_c = Cursor.create("C")
cursor_d = Cursor.create("D")

cursors_in_view = [cursor_b, cursor_c]
cursors_with_view_including = [cursor_c, cursor_d]

def mock_new_conn_receiver_dependency(func):
    func = patch("new_cursor", return_value=cursor_a)(func)
    func = patch("get_view_range_points", return_value=(start, end))(func)
    func = patch("fetch_cursors_in_view", return_value=cursors_in_view)(func)
    func = patch("fetch_with_view_including", return_value=cursors_with_view_including)(func)
    func = patch("publish_new_cursors")(func)
    func = patch("fetch_tiles", return_value=tiles)(func)
    func = patch("watch")(func)
    func = patch("multicast_my_cursor")(func)
    func = patch("multicast_tiles")(func)

    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper

class NewConnReceiver_TestCase(AsyncTestCase):
    @mock_new_conn_receiver_dependency
    async def test_common(
        self,
        new_cursor:AsyncMock,
        get_view_range_points:MagicMock,
        fetch_cursors_in_view:MagicMock,
        fetch_with_view_including:MagicMock,
        publish_new_cursors:AsyncMock,
        fetch_tiles:AsyncMock,
        watch:MagicMock,
        multicast_my_cursor:AsyncMock,
        multicast_tiles:AsyncMock
    ): 
        await NewConnReceiver.receive_new_conn(example_input)
        
        new_cursor.assert_called_once_with(payload.conn_id, payload.width, payload.height)

        multicast_my_cursor.assert_called_once_with(target_conns=[cursor_a], cursor=cursor_a)
        

        watch.assert_has_calls(
            (
                call(watchers=[cursor_a], watchings=cursors_in_view),
                call(watchers=cursors_with_view_including, watchings=[cursor_a])
            )
        )
        publish_new_cursors.assert_has_calls(
            (
                call(target_cursors=[cursor_a],cursors=cursors_in_view),
                call(target_cursors=cursors_with_view_including,cursors=[cursor_a])
            )
        )

        multicast_tiles.assert_called_once_with(
            target_conns=[cursor_a], 
            start=start, end=end, tiles=tiles
        )