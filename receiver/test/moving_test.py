from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, MovingPayload, MovedPayload, ErrorPayload
)

from data.cursor import Cursor
from data.board import Point, Tiles, Tile, PointRange

from config import WINDOW_SIZE_LIMIT

from receiver.internal.moving import (
    MovingReceiver,
    validate_new_position,
    get_new_watchers,
    get_old_watchers,
    multicast_moved,
    pick_unwatching_cursors,
    get_new_cursors_on_sight,
    give_reward,
)

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call

from .test_tools import get_cur_set
from tests.utils import PathPatch

patch = PathPatch("receiver.internal.moving")

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

    @patch("BoardHandler.fetch")
    async def test_normal(self, mock: AsyncMock):
        mock.return_value = self.get_tiles(is_open=True)

        result = await validate_new_position(self.cursor, self.point)
        self.assertIsNone(result)

    @patch("BoardHandler.fetch")
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
        
    @patch("BoardHandler.fetch")
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
        
    @patch("BoardHandler.fetch")
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

    @patch("CursorHandler.view_includes_point")
    def test_new_watchers(self, mock: MagicMock):
        mock.return_value = self.example_cursors_1

        result = get_new_watchers(self.cur_main, self.example_cursors_2)
        mock.assert_called_once_with(p=self.cur_main.position, exclude_ids=[self.cur_main.id])
        
        self.assertListEqual(result, [self.cur_b])


    @patch("CursorHandler.get_watchers_id")
    @patch("CursorHandler.get_cursor")
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
    @patch("multicast")
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

class GiveReward_TestCase(AsyncTestCase):
    @patch("ScoreHandler.increase")
    async def test_normal(self, mock: AsyncMock):
        #TODO: 필요할 때 하기
        pass


class GetNewCursorsOnSight_TestCase(TestCase):
    @patch("CursorHandler.exists_range")
    def test_normal(self, mock: MagicMock):
        # Given
        cursor = Cursor.create("main")
        cursor.height, cursor.width = 1, 1
        cursor.position = Point(0, 0)
        old_position = Point(1, 1)

        old_range = PointRange(Point(0, 2), Point(2, 0))
        cur_range = PointRange(Point(-1, 1), Point(1, -1))

        expected_cursors = get_cur_set(2)
        mock.return_value = expected_cursors

        # When
        result = get_new_cursors_on_sight(cursor, old_position)

        # Then
        self.assertEqual(expected_cursors, result)
        mock.assert_called_once_with(
            start=cur_range.top_left, end=cur_range.bottom_right,
            exclude_start=old_range.top_left, exclude_end=old_range.bottom_right,
            exclude_ids=[cursor.id]
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

cur_main = Cursor.create("main")
other_cursors = get_cur_set(3)
position = Point(0, 0)
message = Message(
    event=EventCollection.MOVING,
    header={"sender" : cur_main.id},
    payload=MovingPayload(
        position=position
    )
)

def mock_moving_receiver_dependency(func):
    func = patch("CursorHandler.get_cursor", return_value=cur_main)(func)
    func = patch("validate_new_position", return_value=None)(func)
    func = patch("multicast")(func)

    func = patch("multicast_moved")(func)
    func = patch("give_reward")(func)

    func = patch("get_old_watchers", return_value=other_cursors)(func)
    func = patch("get_new_watchers", return_value=other_cursors)(func)
    func = patch("get_new_cursors_on_sight", return_value=other_cursors)(func)
    func = patch("pick_unwatching_cursors", return_value=other_cursors)(func)
    func = patch("find_cursors_to_unwatch", return_value=other_cursors)(func)

    func = patch("unwatch")(func)
    func = patch("watch")(func)
    func = patch("publish_new_cursors")(func)

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
        multicast_moved: AsyncMock,
        give_reward: AsyncMock,
        get_old_watchers: MagicMock,
        get_new_watchers: MagicMock,
        get_new_cursors_on_sight: MagicMock,
        pick_unwatching_cursors: MagicMock,
        find_cursors_to_unwatch: MagicMock,
        unwatch: MagicMock,
        watch: MagicMock,
        publish_new_cursors: AsyncMock
    ):
        await MovingReceiver.receive_moving(message)
        
        multicast.assert_not_called()

        multicast_moved.assert_called_once_with(target_conns=other_cursors, cursor=cur_main)
        give_reward.assert_called_once_with(cur_main)

        watch.assert_has_calls([
            call(watchers=[cur_main], watchings=other_cursors),
            call(watchers=other_cursors, watchings=[cur_main])
        ], any_order=True)

        unwatch.assert_has_calls([
            call(watchers=other_cursors, watchings=[cur_main]),
            call(watchers=[cur_main], watchings=other_cursors)
        ], any_order=True) 

        publish_new_cursors.assert_has_calls([
            call(target_cursors=[cur_main], cursors=other_cursors),
            call(target_cursors=other_cursors, cursors=[cur_main])
        ], any_order=True)
        

    @mock_moving_receiver_dependency
    async def test_invalid_input(
        self,
        get_cursor: MagicMock,
        validate_new_position: AsyncMock,
        multicast: AsyncMock,
        multicast_moved: AsyncMock,
        give_reward: AsyncMock,
        get_old_watchers: MagicMock,
        get_new_watchers: MagicMock,
        get_new_cursors_on_sight: MagicMock,
        pick_unwatching_cursors: MagicMock,
        find_cursors_to_unwatch: MagicMock,
        unwatch: MagicMock,
        watch: MagicMock,
        publish_new_cursors: AsyncMock
    ):
        err_message = Message(event="", payload=None)
        validate_new_position.return_value = err_message 

        await MovingReceiver.receive_moving(message)
        
        multicast.assert_called_once_with(target_conns=[cur_main.id], message=err_message)

        multicast_moved.assert_not_called()
        give_reward.assert_not_called()
        publish_new_cursors.assert_not_called()
        unwatch.assert_not_called()
        watch.assert_not_called()
        publish_new_cursors.assert_not_called()
