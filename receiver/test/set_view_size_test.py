from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventEnum, SetViewSizePayload, ErrorPayload
)

from handler.cursor import CursorHandler

from data.cursor import Cursor
from data.board import Point

from config import VIEW_SIZE_LIMIT

from receiver.internal.set_view_size import (
    SetViewSizeReceiver,
    validate_view_size,
    find_new_watchings
)

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import patch, AsyncMock, MagicMock

class ValidateViewSize_TestCase(TestCase):
    def test_normal(self):
        cursor = Cursor.create("A")
        new_width, new_height = cursor.width + 1, cursor.height + 1

        result = validate_view_size(cursor, new_width, new_height)

        self.assertIsNone(result)

    def test_not_changed_case(self):
        cursor = Cursor.create("A")
        cursor.set_size(1, 1)

        result = validate_view_size(cursor, cursor.width, cursor.height)
        expected_message = Message(
            event=EventEnum.ERROR,
            payload=ErrorPayload(msg=f"view size is same as current size")
        )

        self.assertEqual(result, expected_message)

    def test_over_view_limit_case(self):
        cursor = Cursor.create("A")
        new_width, new_height = VIEW_SIZE_LIMIT+1, VIEW_SIZE_LIMIT+1

        result = validate_view_size(cursor, new_width, new_height)
        expected_message = Message(
            event=EventEnum.ERROR,
            payload=ErrorPayload(msg=f"view width or height should be more than 0 and less than {VIEW_SIZE_LIMIT}")
        )

        self.assertEqual(result, expected_message)

class FindNewWatchings_TestCase(TestCase):
    @patch("handler.cursor.CursorHandler.exists_range")
    def test_normal(self, exists_range: MagicMock):
        cursor = Cursor.create("A")
        cursor.set_size(2, 2)

        old_width, old_height = 1, 1
        
        expected_watchings = [Cursor.create("B")]
        start, end = Point(-cursor.width, cursor.height), Point(cursor.width, -cursor.height)
        ex_start, ex_end = Point(-old_width, old_height), Point(old_width, -old_height)

        exists_range.return_value = expected_watchings

        result = find_new_watchings(cursor=cursor, old_width=old_width,old_height=old_height)

        exists_range.assert_called_once_with(
            start=start, end=end,
            exclude_start=ex_start, exclude_end=ex_end,
        )
        self.assertListEqual(expected_watchings, result)
        


    def test_is_not_grown(self):
        cursor = Cursor.create("A")
        cursor.set_size(2, 2)

        result = find_new_watchings(cursor=cursor, old_width=1, old_height=1)

        self.assertListEqual(
            [],
            result
        )

cursor = Cursor.create("A")
other_cursor = Cursor.create("B")
new_width, new_height = 2,2

example_input = Message(
    event=EventEnum.SET_VIEW_SIZE,
    header={"sender": cursor.id},
    payload=SetViewSizePayload(height=new_height, width=new_width)
)

def mock_set_view_size_receiver_dependency(func):
    prefix = "receiver.internal.set_view_size."
    func = patch(prefix+"CursorHandler.get_cursor", return_value=cursor)(func)
    func = patch(prefix+"validate_view_size", return_value=None)(func)
    func = patch(prefix+"multicast")(func)
    func = patch(prefix+"find_new_watchings", return_value=[])(func)
    func = patch(prefix+"find_cursors_to_unwatch", return_value=[])(func)
    func = patch(prefix+"watch")(func)
    func = patch(prefix+"unwatch")(func)
    func = patch(prefix+"publish_new_cursors")(func)

    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


class SetViewSizeReceiver_TestCase(AsyncTestCase):
    def setUp(self):
        cursor.set_size(1, 1)

    @mock_set_view_size_receiver_dependency
    async def test_normal(
        self,
        get_cursor:MagicMock,
        validate_view_size:MagicMock,
        multicast:AsyncMock,
        find_new_watchings:MagicMock,
        find_cursors_to_unwatch:MagicMock,
        watch:MagicMock,
        unwatch:MagicMock,
        publish_new_cursors:AsyncMock
    ):
        await SetViewSizeReceiver.receive_set_view_size(example_input)

        self.assertEqual(cursor.width, new_width)
        self.assertEqual(cursor.height, new_height)
        
        multicast.assert_not_called()
        watch.assert_not_called()
        publish_new_cursors.assert_not_called()
        unwatch.assert_not_called()

    @mock_set_view_size_receiver_dependency
    async def test_view_size_invaild(
        self,
        get_cursor:MagicMock,
        validate_view_size:MagicMock,
        multicast:AsyncMock,
        find_new_watchings:MagicMock,
        find_cursors_to_unwatch:MagicMock,
        watch:MagicMock,
        unwatch:MagicMock,
        publish_new_cursors:AsyncMock
    ):
        message = Message(event="example", payload=None)
        validate_view_size.return_value = message

        await SetViewSizeReceiver.receive_set_view_size(example_input)

        multicast.assert_called_once_with(
            target_conns=[cursor.id],
            message=message
        )
    
    @mock_set_view_size_receiver_dependency
    async def test_new_watchings(
        self,
        get_cursor:MagicMock,
        validate_view_size:MagicMock,
        multicast:AsyncMock,
        find_new_watchings:MagicMock,
        find_cursors_to_unwatch:MagicMock,
        watch:MagicMock,
        unwatch:MagicMock,
        publish_new_cursors:AsyncMock
    ):

        new_watchings = [other_cursor]
        find_new_watchings.return_value = new_watchings

        await SetViewSizeReceiver.receive_set_view_size(example_input)
        watch.assert_called_once_with(
            watchers=[cursor.id], 
            watchings=new_watchings
        )
        publish_new_cursors.assert_called_once_with(
            target_cursors=[cursor], 
            cursors=new_watchings
        )    

    @mock_set_view_size_receiver_dependency
    async def test_unwatching(
        self,
        get_cursor:MagicMock,
        validate_view_size:MagicMock,
        multicast:AsyncMock,
        find_new_watchings:MagicMock,
        find_cursors_to_unwatch:MagicMock,
        watch:MagicMock,
        unwatch:MagicMock,
        publish_new_cursors:AsyncMock
    ):
        unwatchings = [other_cursor]
        find_cursors_to_unwatch.return_value = unwatchings

        await SetViewSizeReceiver.receive_set_view_size(example_input)
        
        unwatch.assert_called_once_with(
            watchers=[cursor.id], 
            watchings=unwatchings
        )