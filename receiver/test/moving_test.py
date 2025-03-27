from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, MovingPayload, MovedPayload, ErrorPayload
)

from handler.cursor import CursorHandler

from data.cursor import Cursor
from data.board import Point, Tiles, Tile

from config import VIEW_SIZE_LIMIT

from receiver.internal.moving import (
    MovingReceiver,
    validate_new_position,
    get_new_watchers,
    get_old_watchers,
    multicast_moved,
    pick_unwatching_cursors
)

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import patch, AsyncMock, MagicMock

class ValidateNewPosition_TestCase(AsyncTestCase):
    def setUp(self):
        self.cursor = Cursor.create("A")
        self.cursor.position = Point(0, 0)

        self.point = Point(1, 0)

    def get_tiles(self, is_open: bool):
        tile = Tile.create(
            is_open=is_open, 
            is_mine=True,
            is_flag=False,
            color=None,
            number=None
        )
        return Tiles(data=bytearray([tile.data]))

    @patch("handler.board.BoardHandler.fetch")
    async def test_normal(self, mock: AsyncMock):
        mock.return_value = self.get_tiles(is_open=True)

        result = await validate_new_position(self.cursor, self.point)
        self.assertIsNone(result)

    @patch("handler.board.BoardHandler.fetch")
    async def test_same(self, mock: AsyncMock):
        self.point = self.cursor.position

        result = await validate_new_position(self.cursor, self.point)
        self.assertEqual(
            result,
            Message(
                event=EventCollection.ERROR,
                payload=ErrorPayload(msg="moving to current position is not allowed")
            )
        )
        
    @patch("handler.board.BoardHandler.fetch")
    async def test_not_movable(self, mock: AsyncMock):
        self.point = Point(2, 0)

        result = await validate_new_position(self.cursor, self.point)
        self.assertEqual(
            result,
            Message(
                event=EventCollection.ERROR,
                payload=ErrorPayload(msg="only moving to 8 nearby tiles is allowed")
            )
        )
        
    @patch("handler.board.BoardHandler.fetch")
    async def test_not_open_tile(self, mock: AsyncMock):
        mock.return_value = self.get_tiles(is_open=False)

        result = await validate_new_position(self.cursor, self.point)
        self.assertEqual(
            result,
            Message(
                event=EventCollection.ERROR,
                payload=ErrorPayload(msg="moving to closed tile is not available")
            )
        )

class GetWatchers_TestCase(TestCase):
    def setUp(self):
        self.cur_main = Cursor.create("Hey")
        self.cur_a = Cursor.create("A")
        self.cur_b = Cursor.create("B")
        self.cur_c = Cursor.create("C")
        self.example_cursors_1 = [self.cur_a, self.cur_b]    
        self.example_cursors_2 = [self.cur_a, self.cur_c]

    @patch("handler.cursor.CursorHandler.view_includes_point")
    def test_new_watchers(self, mock: MagicMock):
        mock.return_value = self.example_cursors_1

        result = get_new_watchers(self.cur_main, self.example_cursors_2)
        mock.assert_called_once_with(p=self.cur_main.position, exclude_ids=[self.cur_main.id])
        
        self.assertListEqual(result, [self.cur_b])


    @patch("handler.cursor.CursorHandler.get_watchers_id")
    @patch("handler.cursor.CursorHandler.get_cursor")
    def test_old_watchers(self, get_cursor:MagicMock, get_watchers_id:MagicMock):
        get_watchers_id.return_value = [c.id for c in self.example_cursors_1]
        get_cursor.side_effect = self.example_cursors_1

        result = get_old_watchers(self.cur_main)
        get_watchers_id.assert_called_once_with(
            cursor_id=self.cur_main.id
        )
        self.assertListEqual(
            result,
            self.example_cursors_1
        )


class MovingMulticast_TestCase(AsyncTestCase):
    @patch("receiver.internal.moving.multicast")
    async def multicast_moved(self, mock:AsyncMock):
        cursor_a = Cursor.create("A")
        cursor_b = Cursor.create("B")
        cursor_c = Cursor.create("C")
        
        await multicast_moved(target_conns=[cursor_a, cursor_b], cursor=cursor_c)

        mock.assert_called_once_with(
            target_conns=[cursor_a, cursor_b],
            message=Message(
                event=EventCollection.MOVED,
                payload=MovedPayload(
                    id=cursor_c.id,
                    new_position=cursor_c.position
                )
            )
        )

class PickUnwatchingCursors_TestCase(TestCase):
    def test_normal(self):
        cur_main = Cursor.create("main")
        cur_main.position = Point(0, 0)

        cur_a = Cursor.create("A")
        cur_a.width, cur_a.height = 1, 1
        cur_a.position = Point(1, 1) # 포함

        cur_b = Cursor.create("B")
        cur_b.width, cur_b.height = 1, 1
        cur_b.position = Point(2, 1) # 불포함

        result = pick_unwatching_cursors(cur_main, [cur_a, cur_b])
        self.assertListEqual(result, [cur_b])

cur_a = Cursor.create("A")
position = Point(0, 0)
message = Message(
    event=EventCollection.MOVING,
    header={"sender" : cur_a.id},
    payload=MovingPayload(
        position=position
    )
)

def mock_moving_receiver_dependency(func):
    prefix = "receiver.internal.moving."
    
    func = patch("handler.cursor.CursorHandler.get_cursor", return_value=cur_a)(func)
    func = patch(prefix+"validate_new_position", return_value=None)(func)
    func = patch(prefix+"multicast")(func)
    
    func = patch(prefix+"get_old_watchers", return_value=[])(func)
    func = patch(prefix+"multicast_moved")(func)
    func = patch(prefix+"pick_unwatching_cursors", return_value=[])(func)

    func = patch(prefix+"unwatch")(func)
    func = patch(prefix+"get_new_watchers", return_value=[])(func)
    func = patch(prefix+"watch")(func)

    func = patch(prefix+"publish_new_cursors")(func)
    func = patch("handler.cursor.CursorHandler.exists_range", return_value=[])(func)
    func = patch(prefix+"find_cursors_to_unwatch", return_value=[])(func)

    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper

class MovingReceiver_TestCase(AsyncTestCase):
    @mock_moving_receiver_dependency
    async def test_normal(
        self,
        get_cursor: MagicMock,
        validate_new_position: AsyncMock,
        multicast: AsyncMock,
        get_old_watchers: MagicMock,
        multicast_moved: AsyncMock,
        pick_unwatching_cursors: MagicMock,
        unwatch: MagicMock,
        get_new_watchers: MagicMock,
        watch: MagicMock,
        publish_new_cursors: AsyncMock,
        exists_range: MagicMock,
        find_cursors_to_unwatch: MagicMock
    ):
        await MovingReceiver.receive_moving(message)
        
        multicast.assert_not_called()
        multicast_moved.assert_not_called()
        watch.assert_not_called()
        publish_new_cursors.assert_not_called()
        unwatch.assert_not_called()

    @mock_moving_receiver_dependency
    async def test_invalid_input(
        self,
        get_cursor: MagicMock,
        validate_new_position: AsyncMock,
        multicast: AsyncMock,
        get_old_watchers: MagicMock,
        multicast_moved: AsyncMock,
        pick_unwatching_cursors: MagicMock,
        unwatch: MagicMock,
        get_new_watchers: MagicMock,
        watch: MagicMock,
        publish_new_cursors: AsyncMock,
        exists_range: MagicMock,
        find_cursors_to_unwatch: MagicMock
    ):
        err_message = Message(event="", payload=None)
        validate_new_position.return_value = err_message 

        await MovingReceiver.receive_moving(message)
        
        multicast.assert_called_once_with(target_conns=[cur_a.id], message=err_message)

    @mock_moving_receiver_dependency
    async def test_get_old_watchers(
        self,
        get_cursor: MagicMock,
        validate_new_position: AsyncMock,
        multicast: AsyncMock,
        get_old_watchers: MagicMock,
        multicast_moved: AsyncMock,
        pick_unwatching_cursors: MagicMock,
        unwatch: MagicMock,
        get_new_watchers: MagicMock,
        watch: MagicMock,
        publish_new_cursors: AsyncMock,
        exists_range: MagicMock,
        find_cursors_to_unwatch: MagicMock
    ):
        example_cursors = [Cursor.create("B"),Cursor.create("C")]
        get_old_watchers.return_value = example_cursors

        await MovingReceiver.receive_moving(message)
        
        multicast_moved.assert_called_once_with(target_conns=example_cursors, cursor=cur_a)

    @mock_moving_receiver_dependency
    async def test_pick_unwatching_cursors(
        self,
        get_cursor: MagicMock,
        validate_new_position: AsyncMock,
        multicast: AsyncMock,
        get_old_watchers: MagicMock,
        multicast_moved: AsyncMock,
        pick_unwatching_cursors: MagicMock,
        unwatch: MagicMock,
        get_new_watchers: MagicMock,
        watch: MagicMock,
        publish_new_cursors: AsyncMock,
        exists_range: MagicMock,
        find_cursors_to_unwatch: MagicMock
    ):
        example_cursors = [Cursor.create("B"),Cursor.create("C")]
        pick_unwatching_cursors.return_value = example_cursors

        await MovingReceiver.receive_moving(message)
        
        unwatch.assert_called_once_with(watchers=example_cursors, watchings=[cur_a])

    @mock_moving_receiver_dependency
    async def test_get_new_watchers(
        self,
        get_cursor: MagicMock,
        validate_new_position: AsyncMock,
        multicast: AsyncMock,
        get_old_watchers: MagicMock,
        multicast_moved: AsyncMock,
        pick_unwatching_cursors: MagicMock,
        unwatch: MagicMock,
        get_new_watchers: MagicMock,
        watch: MagicMock,
        publish_new_cursors: AsyncMock,
        exists_range: MagicMock,
        find_cursors_to_unwatch: MagicMock
    ):
        example_cursors = [Cursor.create("B"),Cursor.create("C")]
        get_new_watchers.return_value = example_cursors

        await MovingReceiver.receive_moving(message)
        
        watch.assert_called_once_with(watchers=example_cursors, watchings=[cur_a])
        publish_new_cursors.assert_called_once_with(target_cursors=example_cursors, cursors=[cur_a])

    @mock_moving_receiver_dependency
    async def test_new_watchings(
        self,
        get_cursor: MagicMock,
        validate_new_position: AsyncMock,
        multicast: AsyncMock,
        get_old_watchers: MagicMock,
        multicast_moved: AsyncMock,
        pick_unwatching_cursors: MagicMock,
        unwatch: MagicMock,
        get_new_watchers: MagicMock,
        watch: MagicMock,
        publish_new_cursors: AsyncMock,
        exists_range: MagicMock,
        find_cursors_to_unwatch: MagicMock
    ):
        example_cursors = [Cursor.create("B"),Cursor.create("C")]
        exists_range.return_value = example_cursors

        await MovingReceiver.receive_moving(message)
        
        watch.assert_called_once_with(watchers=[cur_a], watchings=example_cursors)
        publish_new_cursors.assert_called_once_with(target_cursors=[cur_a], cursors=example_cursors)

    @mock_moving_receiver_dependency
    async def test_find_cursors_to_unwatch(
        self,
        get_cursor: MagicMock,
        validate_new_position: AsyncMock,
        multicast: AsyncMock,
        get_old_watchers: MagicMock,
        multicast_moved: AsyncMock,
        pick_unwatching_cursors: MagicMock,
        unwatch: MagicMock,
        get_new_watchers: MagicMock,
        watch: MagicMock,
        publish_new_cursors: AsyncMock,
        exists_range: MagicMock,
        find_cursors_to_unwatch: MagicMock
    ):
        example_cursors = [Cursor.create("B"),Cursor.create("C")]
        find_cursors_to_unwatch.return_value = example_cursors

        await MovingReceiver.receive_moving(message)
        
        unwatch.assert_called_once_with(watchers=[cur_a], watchings=example_cursors)
        