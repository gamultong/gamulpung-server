from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventEnum, ClickType, PointingPayload,PointerSetPayload,
    ErrorPayload, OpenTilePayload, SetFlagPayload
)

from handler.cursor import CursorHandler

from data.cursor import Cursor
from data.board import Point, Tiles, Tile

from config import VIEW_SIZE_LIMIT

from receiver.internal.pointing import (
    PointingReceiver,
    publish_open_tile, publish_set_flag,
    multicast_pointer_set,
    validate_pointable,
    get_watchers
)

from .test_tools import get_cur_set, PathPatch

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call

from datetime import datetime, timedelta

patch = PathPatch("receiver.internal.pointing")

class MulticastPointerSet_TestCase(AsyncTestCase):
    @patch("multicast")
    async def test_multicast_pointer_set(self, mock:AsyncMock):
        cur_a, cur_b, cur_c = get_cur_set(3)
        cur_c.pointer = Point(1,1)

        await multicast_pointer_set(
            target_conns=[cur_a, cur_b],
            cursor=cur_c
        )

        mock.assert_called_once_with(
            target_conns=[cur_a.id, cur_b.id],
            message=Message(
                event=EventEnum.POINTER_SET,
                payload=PointerSetPayload(
                    id=cur_c.id,
                    pointer=cur_c.pointer
                )
            )    
        )

class ValidatePointable_TestCase(TestCase):
    def setUp(self):
        self.cursor = Cursor.create("A")
        
        self.check_in_view_func = MagicMock()
        self.check_in_view_func.return_value = True
        self.cursor.check_in_view = self.check_in_view_func

    def test_normal(self):
        result = validate_pointable(cursor=self.cursor, point=Point(0, 0))
        self.assertIsNone(result)

    def test_dead_cursor(self):
        self.cursor.revive_at = datetime.now() + timedelta(hours=1)

        result = validate_pointable(cursor=self.cursor, point=Point(0, 0))

        self.assertEqual(
            result,
            Message(
                event=EventEnum.ERROR,
                payload=ErrorPayload(msg="dead cursor cannot do pointing")
            )
        )

    def test_out_of_range(self):
        self.check_in_view_func.return_value = False        

        result = validate_pointable(cursor=self.cursor, point=Point(0, 0))

        self.assertEqual(
            result,
            Message(
                event=EventEnum.ERROR,
                payload=ErrorPayload(msg="pointer is out of cursor view")
            )
        )

class PublishPointing_TestCase(AsyncTestCase):
    @patch("EventBroker.publish")
    async def test_publish_open_tile(self, mock:AsyncMock):
        cur = Cursor.create("A")
        
        await publish_open_tile(cur)

        mock.assert_called_once_with(
            message=Message(
                event=EventEnum.OPEN_TILE,
                header={"sender": cur.id},
                payload=OpenTilePayload()
            )
        )

    @patch("EventBroker.publish")
    async def test_publish_set_flag(self, mock:AsyncMock):
        cur = Cursor.create("A")
        
        await publish_set_flag(cur)

        mock.assert_called_once_with(
            message=Message(
                event=EventEnum.SET_FLAG,
                header={"sender": cur.id},
                payload=SetFlagPayload()
            )
        )


class GetWatchers_TestCase(TestCase):
    @patch("CursorHandler.get_watchers_id")
    @patch("CursorHandler.get_cursor")
    def test_get_watchers(self, get_cursor:MagicMock, get_watchers_id: MagicMock):
        cur_main = Cursor.create("main")
        watchers = get_cur_set(3)

        get_watchers_id.return_value = [c.id for c in watchers]
        get_cursor.side_effect = watchers

        result = get_watchers(cur_main)

        self.assertListEqual(result, watchers)

        get_watchers_id.assert_called_once_with(cur_main.id)
        get_cursor.assert_has_calls(calls=[call(c.id) for c in watchers])


cursor_a = Cursor.create("A")

def mock_pointing_receiver_dependency(func):
    func = patch("CursorHandler.get_cursor", return_value=cursor_a)(func)
    func = patch("get_watchers", return_value=[])(func)
    func = patch("validate_pointable", return_value=None)(func)
    func = patch("multicast")(func)
    func = patch("multicast_pointer_set")(func)
    func = patch("publish_open_tile")(func)
    func = patch("publish_set_flag")(func)

    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper

class PointingReceiver_TestCase(AsyncTestCase):
    def setUp(self):
        self.input_message = Message(
            event=EventEnum.POINTING,
            header={"sender": cursor_a.id},
            payload=PointingPayload(
                click_type=None,
                position=Point(1, 1)
            )
        )


    @mock_pointing_receiver_dependency
    async def test_normal(
            self,
            get_cursor: MagicMock,
            get_watchers: MagicMock,
            validate_pointable: MagicMock,
            multicast: AsyncMock,
            multicast_pointer_set: AsyncMock,
            publish_open_tile: AsyncMock,
            publish_set_flag: AsyncMock
    ):
        
        await PointingReceiver.receive_pointing(self.input_message)

        multicast.assert_not_called()
        multicast_pointer_set.assert_not_called()
        publish_open_tile.assert_not_called()
        publish_set_flag.assert_not_called()

    @mock_pointing_receiver_dependency
    async def test_invalid(
            self,
            get_cursor: MagicMock,
            get_watchers: MagicMock,
            validate_pointable: MagicMock,
            multicast: AsyncMock,
            multicast_pointer_set: AsyncMock,
            publish_open_tile: AsyncMock,
            publish_set_flag: AsyncMock
    ):
        error_msg = Message(event=EventEnum.ERROR, payload=None)
        validate_pointable.return_value = error_msg

        await PointingReceiver.receive_pointing(self.input_message)

        multicast.assert_called_once_with(
            target_conns=[cursor_a.id],
            message=error_msg
        )
        multicast_pointer_set.assert_not_called()
        publish_open_tile.assert_not_called()
        publish_set_flag.assert_not_called()

    @mock_pointing_receiver_dependency
    async def test_watchers(
            self,
            get_cursor: MagicMock,
            get_watchers: MagicMock,
            validate_pointable: MagicMock,
            multicast: AsyncMock,
            multicast_pointer_set: AsyncMock,
            publish_open_tile: AsyncMock,
            publish_set_flag: AsyncMock
    ):
        watchers = get_cur_set(3)
        get_watchers.return_value = watchers


        await PointingReceiver.receive_pointing(self.input_message)

        multicast_pointer_set.assert_called_once_with(
            target_conns=[cursor_a]+watchers,
            cursor=cursor_a
        )
        multicast.assert_not_called()
        publish_open_tile.assert_not_called()
        publish_set_flag.assert_not_called()

    @mock_pointing_receiver_dependency
    async def test_general_click(
            self,
            get_cursor: MagicMock,
            get_watchers: MagicMock,
            validate_pointable: MagicMock,
            multicast: AsyncMock,
            multicast_pointer_set: AsyncMock,
            publish_open_tile: AsyncMock,
            publish_set_flag: AsyncMock
    ):
        self.input_message.payload.click_type = ClickType.GENERAL_CLICK

        await PointingReceiver.receive_pointing(self.input_message)

        multicast_pointer_set.assert_not_called()
        multicast.assert_not_called()
        publish_open_tile.assert_called_once_with(cursor=cursor_a)
        publish_set_flag.assert_not_called()

    @mock_pointing_receiver_dependency
    async def test_special_click(
            self,
            get_cursor: MagicMock,
            get_watchers: MagicMock,
            validate_pointable: MagicMock,
            multicast: AsyncMock,
            multicast_pointer_set: AsyncMock,
            publish_open_tile: AsyncMock,
            publish_set_flag: AsyncMock
    ):
        self.input_message.payload.click_type = ClickType.SPECIAL_CLICK

        await PointingReceiver.receive_pointing(self.input_message)

        multicast_pointer_set.assert_not_called()
        multicast.assert_not_called()
        publish_open_tile.assert_not_called()
        publish_set_flag.assert_called_once_with(cursor=cursor_a)