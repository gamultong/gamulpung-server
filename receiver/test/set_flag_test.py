from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventEnum, SetFlagPayload,FlagSetPayload
)

from handler.board import BoardHandler
from handler.cursor import CursorHandler

from data.board import Point, Tile, Tiles
from data.cursor import Cursor, Color

from receiver.internal.set_flag import (
    SetFlagReceiver,
    multicast_flag_set,
    get_tile_if_flaggable
)

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call
from .test_tools import get_cur_set, PathPatch


patch = PathPatch("receiver.internal.set_flag")

class MulticastSetFlag_TestCase(AsyncTestCase):
    @patch("multicast")
    async def test_multicast_flag_set(self, mock:AsyncMock):
        cur_a, cur_b, cur_c = get_cur_set(3)
        target_conns = [cur_a, cur_b, cur_c ]
        position = Point(1, 1)
        tile = Tile.create(
            is_open=False,
            is_mine=False,
            is_flag=True,
            color=Color.BLUE,
            number=1
        )

        await multicast_flag_set(target_conns=target_conns, tile=tile, position=position)

        mock.assert_called_once_with(
            target_conns=[cur.id for cur in target_conns],
            message=Message(
                event=EventEnum.FLAG_SET,
                payload=FlagSetPayload(
                    position=position,
                    is_set=tile.is_flag,
                    color=tile.color,
                )
            )
        )
    

class GetTileIfFlaggable_TestCase(AsyncTestCase):
    def setUp(self):
        self.cursor = Cursor.create("A")

        self.check_interactable_mock = MagicMock()
        self.cursor.check_interactable = self.check_interactable_mock

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
        self.open_tile_tiles = Tiles(data=bytearray([self.open_tile.data]))
        self.closed_tile_tiles = Tiles(data=bytearray([self.closed_tile.data]))
        
    
    @patch("BoardHandler.fetch")
    async def test_normal(self, fetch: MagicMock):
        self.check_interactable_mock.return_value = True
        fetch.return_value = self.closed_tile_tiles

        result = await get_tile_if_flaggable(self.cursor)

        self.assertEqual(result, self.closed_tile)

    @patch("BoardHandler.fetch")
    async def test_not_interactable(self, fetch: MagicMock):
        self.check_interactable_mock.return_value = False
        fetch.return_value = self.closed_tile_tiles

        result = await get_tile_if_flaggable(self.cursor)
        self.assertIsNone(result)

    @patch("BoardHandler.fetch")
    async def test_open_tile(self, fetch: MagicMock):
        self.check_interactable_mock.return_value = True
        fetch.return_value = self.open_tile_tiles

        result = await get_tile_if_flaggable(self.cursor)
        self.assertIsNone(result)

cursor_a = Cursor.create("A")
cursor_a.pointer = Point(1, 1)

def mock_set_flag_receiver_dependency(func):
    func = patch("CursorHandler.get_cursor", return_value=cursor_a)(func)
    func = patch("get_tile_if_flaggable")(func)
    func = patch("BoardHandler.set_flag_state")(func)
    func = patch("CursorHandler.view_includes_point", return_value=[])(func)
    func = patch("multicast_flag_set")(func)

    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


class SetFlagReceiver_TestCase(AsyncTestCase):
    def setUp(self):
        self.input_message = Message(
            event=EventEnum.SET_FLAG,
            header={"sender": cursor_a.id},
            payload=SetFlagPayload()
        )
        self.tile = Tile.create(
            is_open=False,
            is_mine=False,
            is_flag=False,
            color=None,
            number=1
        )

    @mock_set_flag_receiver_dependency
    async def test_normal(
            self,
            get_cursor: MagicMock,
            get_tile_if_flaggable: AsyncMock,
            set_flag_state: MagicMock,
            view_includes_point: MagicMock,
            multicast_flag_set: AsyncMock
        ):
        get_tile_if_flaggable.return_value = self.tile

        expected_flag_state = not self.tile.is_flag
        expected_color = cursor_a.color

        await SetFlagReceiver.receive_set_flag(self.input_message)
            
        set_flag_state.assert_called_once_with(
            p=cursor_a.pointer, 
            state=expected_flag_state, 
            color=expected_color
        )
        multicast_flag_set.assert_not_called()
        
    @mock_set_flag_receiver_dependency
    async def test_not_flaggable(
            self,
            get_cursor: MagicMock,
            get_tile_if_flaggable: AsyncMock,
            set_flag_state: MagicMock,
            view_includes_point: MagicMock,
            multicast_flag_set: AsyncMock
        ):
        get_tile_if_flaggable.return_value = None

        await SetFlagReceiver.receive_set_flag(self.input_message)
        
        set_flag_state.assert_not_called()
        multicast_flag_set.assert_not_called()
        
    @mock_set_flag_receiver_dependency
    async def test_view_cursors(
            self,
            get_cursor: MagicMock,
            get_tile_if_flaggable: AsyncMock,
            set_flag_state: MagicMock,
            view_includes_point: MagicMock,
            multicast_flag_set: AsyncMock
        ):
        cursors = get_cur_set(3)
        view_includes_point.return_value = cursors
        get_tile_if_flaggable.return_value = self.tile

        expected_flag_state = not self.tile.is_flag
        expected_color = cursor_a.color

        await SetFlagReceiver.receive_set_flag(self.input_message)
            
        set_flag_state.assert_called_once_with(
            p=cursor_a.pointer, 
            state=expected_flag_state, 
            color=expected_color
        )

        multicast_flag_set.assert_called_once_with(
            target_conns=cursors,
            tile=self.tile, position=cursor_a.pointer
        )