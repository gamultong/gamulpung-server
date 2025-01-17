import asyncio
from data.cursor import Color
from data.board import Point, Tile, Tiles, Section
from receiver.board import BoardEventHandler
from handler.board import BoardHandler
from handler.board.storage.test.fixtures import setup_board
from event.message import Message
from event.payload import (
    FetchTilesPayload,
    TilesEvent,
    TilesPayload,
    NewConnEvent,
    NewConnPayload,
    NewCursorCandidatePayload,
    TryPointingPayload,
    PointingResultPayload,
    PointEvent,
    ClickType,
    MoveEvent,
    CheckMovablePayload,
    MovableResultPayload,
    InteractionEvent,
    SingleTileOpenedPayload,
    TilesOpenedPayload,
    FlagSetPayload,
    ErrorEvent,
    ErrorPayload
)
from config import VIEW_SIZE_LIMIT

import unittest
from unittest.mock import AsyncMock, patch

"""
BoardEventHandler Test
----------------------------
Test
✅ : test 통과
❌ : test 실패
🖊️ : test 작성

- fetch-tiles-receiver
    - ✅| normal-case
    - 🖊️| invaild-message
        - 🖊️| invaild-message-payload
        - 🖊️| no-sender
        - 🖊️| invaild-header
- new-conn-receiver
    - ✅| normal-case
- try-pointing-receiver
    - ✅| normal-case
- check-movable-receiver
    -  ✅| normal-case
"""


# fetch-tiles-receiver Test
class BoardEventHandler_FetchTilesReceiver_TestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await setup_board()

    @patch("data.board.Section.create")
    @patch("event.broker.EventBroker.publish")
    async def test_fetch_tiles_receiver_normal_case(self, mock: AsyncMock, create_mock):
        """
        fetch-tiles-receiver
        normal-case
        ----------------------------
        trigger event ->

        - fetch-tiles : message[FetchTilesPayload]
            - header :
                - sender : conn_id
            - descrption :
                econn_id의 tiles 정보 요청
        ----------------------------
        publish event ->

        - multicast : message[TilesPayload]
            - header :
                - target_conns : [conn_id]
                - origin_event : tiles
            - descrption :
                fetch-tiles의 대한 응답
        ----------------------------
        """

        def stub_section_create(p: Point) -> Section:
            return Section(
                data=bytearray([0b00000000 for _ in range(Section.LENGTH ** 2)]),
                p=p
            )
        create_mock.side_effect = stub_section_create

        start_p = Point(-1, 0)
        end_p = Point(0, -1)

        # trigger message 생성
        message = Message(
            event=TilesEvent.FETCH_TILES,
            header={"sender": "ayo"},
            payload=FetchTilesPayload(
                start_p=start_p,
                end_p=end_p,
            )
        )

        # trigger event
        await BoardEventHandler.receive_fetch_tiles(message)

        # 호출 여부
        mock.assert_called_once()
        got: Message[TilesPayload] = mock.mock_calls[0].args[0]

        # message 확인
        self.assertEqual(type(got), Message)
        # message.event
        self.assertEqual(got.event, "multicast")
        # message.header
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertEqual(got.header["target_conns"][0], message.header["sender"])
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], TilesEvent.TILES)

        # message.payload
        self.assertEqual(type(got.payload), TilesPayload)
        self.assertEqual(got.payload.start_p, start_p)
        self.assertEqual(got.payload.end_p, end_p)

        empty_open = Tile.from_int(0b10000000)
        one_open = Tile.from_int(0b10000001)
        expected = Tiles(data=bytearray([
            empty_open.data, one_open.data, one_open.data, one_open.data
        ]))

        self.assertEqual(got.payload.tiles, expected.to_str())

    @patch("event.broker.EventBroker.publish")
    async def test_fetch_tiles_receiver_malformed_start_end(self, mock: AsyncMock):
        start_p = Point(1, 0)
        end_p = Point(0, -1)

        message = Message(
            event=TilesEvent.FETCH_TILES,
            header={"sender": "ayo"},
            payload=FetchTilesPayload(
                start_p=start_p,
                end_p=end_p,
            )
        )

        # trigger event
        await BoardEventHandler.receive_fetch_tiles(message)

        # 호출 여부
        mock.assert_called_once()
        got: Message[ErrorPayload] = mock.mock_calls[0].args[0]

        # message 확인
        self.assertEqual(type(got), Message)
        # message.event
        self.assertEqual(got.event, "multicast")
        # message.header
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertEqual(got.header["target_conns"][0], message.header["sender"])
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], ErrorEvent.ERROR)

        # message.payload
        self.assertEqual(type(got.payload), ErrorPayload)

    @patch("event.broker.EventBroker.publish")
    async def test_fetch_tiles_receiver_range_exceeded(self, mock: AsyncMock):
        start_p = Point((-VIEW_SIZE_LIMIT/2) // 1, 0)
        end_p = Point((VIEW_SIZE_LIMIT/2) // 1, -1)

        message = Message(
            event=TilesEvent.FETCH_TILES,
            header={"sender": "ayo"},
            payload=FetchTilesPayload(
                start_p=start_p,
                end_p=end_p,
            )
        )

        # trigger event
        await BoardEventHandler.receive_fetch_tiles(message)

        # 호출 여부
        mock.assert_called_once()
        got: Message[ErrorPayload] = mock.mock_calls[0].args[0]

        # message 확인
        self.assertEqual(type(got), Message)
        # message.event
        self.assertEqual(got.event, "multicast")
        # message.header
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertEqual(got.header["target_conns"][0], message.header["sender"])
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], ErrorEvent.ERROR)

        # message.payload
        self.assertEqual(type(got.payload), ErrorPayload)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_new_conn(self, mock: AsyncMock):
        conn_id = "ayo"
        width = 1
        height = 1
        message = Message(
            event=NewConnEvent.NEW_CONN,
            payload=NewConnPayload(conn_id=conn_id, width=width, height=height)
        )

        await BoardEventHandler.receive_new_conn(message)

        # tiles, new-cursor-candidate
        self.assertEqual(len(mock.mock_calls), 2)

        # new-cursor-candidate
        got: Message[NewCursorCandidatePayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, NewConnEvent.NEW_CURSOR_CANDIDATE)

        self.assertEqual(type(got.payload), NewCursorCandidatePayload)
        self.assertEqual(got.payload.conn_id, conn_id)
        self.assertEqual(got.payload.width, width)
        self.assertEqual(got.payload.height, height)

        position = got.payload.position
        tiles = await BoardHandler.fetch(position, position)
        tile = Tile.from_int(tiles.data[0])
        self.assertTrue(tile.is_open)

        # tiles
        got: Message[TilesPayload] = mock.mock_calls[1].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], TilesEvent.TILES)

        self.assertEqual(type(got.payload), TilesPayload)
        self.assertEqual(got.payload.start_p, Point(position.x-width, position.y+height))
        self.assertEqual(got.payload.end_p, Point(position.x+width, position.y-height))

        # 하는 김에 마스킹까지 같이 테스트
        expected = await BoardHandler.fetch(got.payload.start_p, got.payload.end_p)
        expected.hide_info()

        self.assertEqual(got.payload.tiles, expected.to_str())


class BoardEventHandler_PointingReceiver_TestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await setup_board()
        self.sender_id = "ayo"

    @patch("event.broker.EventBroker.publish")
    async def test_try_pointing_pointable_not_interactable(self, mock: AsyncMock):
        cursor_pos = Point(2, 2)
        pointer = Point(0, 0)

        message = Message(
            event=PointEvent.TRY_POINTING,
            header={"sender": self.sender_id},
            payload=TryPointingPayload(
                cursor_position=cursor_pos,
                new_pointer=pointer,
                click_type=ClickType.GENERAL_CLICK,
                color=Color.BLUE
            )
        )

        await BoardEventHandler.receive_try_pointing(message)

        # pointing-result 발행하는지 확인
        mock.assert_called_once()
        got: Message[PointingResultPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, PointEvent.POINTING_RESULT)

        # receiver 값 확인
        self.assertEqual(len(got.header), 1)
        self.assertIn("receiver", got.header)
        self.assertEqual(got.header["receiver"], self.sender_id)

        # payload 확인
        self.assertEqual(type(got.payload), PointingResultPayload)
        self.assertTrue(got.payload.pointable)
        self.assertEqual(got.payload.pointer, pointer)

    @patch("event.broker.EventBroker.publish")
    async def test_try_pointing_pointable_closed_general_click(self, mock: AsyncMock):
        # TODO: 연쇄 개방에 대한 테스트케이스 추가

        cursor_pos = Point(0, 0)
        pointer = Point(1, 0)

        message = Message(
            event=PointEvent.TRY_POINTING,
            header={"sender": self.sender_id},
            payload=TryPointingPayload(
                cursor_position=cursor_pos,
                new_pointer=pointer,
                click_type=ClickType.GENERAL_CLICK,
                color=Color.BLUE
            )
        )

        await BoardEventHandler.receive_try_pointing(message)

        # pointing-result, single-tile-opened 발행하는지 확인
        self.assertEqual(len(mock.mock_calls), 2)

        # pointing-result
        got: Message[PointingResultPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, PointEvent.POINTING_RESULT)
        # receiver 값 확인
        self.assertEqual(len(got.header), 1)
        self.assertIn("receiver", got.header)
        self.assertEqual(got.header["receiver"], self.sender_id)
        # payload 확인
        self.assertEqual(type(got.payload), PointingResultPayload)
        self.assertTrue(got.payload.pointable)
        self.assertEqual(got.payload.pointer, pointer)

        # single-tile-opened
        got: Message[SingleTileOpenedPayload] = mock.mock_calls[1].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, InteractionEvent.SINGLE_TILE_OPENED)
        # payload 확인
        self.assertEqual(type(got.payload), SingleTileOpenedPayload)
        self.assertEqual(got.payload.position, pointer)

        expected_tile = Tile.create(
            is_open=True,
            is_mine=False,
            is_flag=False,
            color=None,
            number=1
        )
        tiles = await BoardHandler.fetch(start=pointer, end=pointer)
        fetched_tile = Tile.from_int(tiles.data[0])

        self.assertEqual(fetched_tile, expected_tile)
        self.assertEqual(got.payload.tile, tiles.to_str())

    @patch("event.broker.EventBroker.publish")
    async def test_try_pointing_pointable_closed_general_click_race(self, mock: AsyncMock):
        cursor_pos = Point(0, 0)
        pointer = Point(1, 0)

        # 코루틴 스위칭을 위해 sleep. 이게 되는 이유를 모르겠다.
        async def sleep(_):
            await asyncio.sleep(0)
        mock.side_effect = sleep

        message = Message(
            event=PointEvent.TRY_POINTING,
            header={"sender": self.sender_id},
            payload=TryPointingPayload(
                cursor_position=cursor_pos,
                new_pointer=pointer,
                click_type=ClickType.GENERAL_CLICK,
                color=Color.BLUE
            )
        )

        await asyncio.gather(
            BoardEventHandler.receive_try_pointing(message),
            BoardEventHandler.receive_try_pointing(message)
        )

        # FIXME: TODO: 레이스 컨디션 처리가 안 되어 있음!!!!!
        # 첫번째: pointing-result, single-tile-opened 두번째: pointing-result 발행하는지 확인
        self.assertEqual(len(mock.mock_calls), 4)

    @patch("event.broker.EventBroker.publish")
    async def test_try_pointing_pointable_closed_general_click_flag(self, mock: AsyncMock):
        cursor_pos = Point(0, 0)
        pointer = Point(1, 1)

        message = Message(
            event=PointEvent.TRY_POINTING,
            header={"sender": self.sender_id},
            payload=TryPointingPayload(
                cursor_position=cursor_pos,
                new_pointer=pointer,
                click_type=ClickType.GENERAL_CLICK,
                color=Color.BLUE
            )
        )

        await BoardEventHandler.receive_try_pointing(message)

        # pointing-result 발행하는지 확인
        self.assertEqual(len(mock.mock_calls), 1)

        # pointing-result
        got: Message[PointingResultPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, PointEvent.POINTING_RESULT)
        # receiver 값 확인
        self.assertEqual(len(got.header), 1)
        self.assertIn("receiver", got.header)
        self.assertEqual(got.header["receiver"], self.sender_id)
        # payload 확인
        self.assertEqual(type(got.payload), PointingResultPayload)
        self.assertTrue(got.payload.pointable)
        self.assertEqual(got.payload.pointer, pointer)

    @patch("event.broker.EventBroker.publish")
    async def test_try_pointing_pointable_closed_special_click(self, mock: AsyncMock):
        cursor_pos = Point(0, 0)
        pointer = Point(1, 0)
        color = Color.BLUE

        message = Message(
            event=PointEvent.TRY_POINTING,
            header={"sender": self.sender_id},
            payload=TryPointingPayload(
                cursor_position=cursor_pos,
                new_pointer=pointer,
                click_type=ClickType.SPECIAL_CLICK,
                color=color
            )
        )

        await BoardEventHandler.receive_try_pointing(message)

        # pointing-result, flag-set 발행하는지 확인
        self.assertEqual(len(mock.mock_calls), 2)

        # pointing-result
        got: Message[PointingResultPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, PointEvent.POINTING_RESULT)
        # receiver 값 확인
        self.assertEqual(len(got.header), 1)
        self.assertIn("receiver", got.header)
        self.assertEqual(got.header["receiver"], self.sender_id)
        # payload 확인
        self.assertEqual(type(got.payload), PointingResultPayload)
        self.assertTrue(got.payload.pointable)
        self.assertEqual(got.payload.pointer, pointer)

        # flag-set
        got: Message[FlagSetPayload] = mock.mock_calls[1].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, InteractionEvent.FLAG_SET)
        # payload 확인
        self.assertEqual(type(got.payload), FlagSetPayload)
        self.assertEqual(got.payload.position, pointer)
        self.assertEqual(got.payload.color, color)
        self.assertTrue(got.payload.is_set)

        expected_tile = Tile.create(
            is_open=False,
            is_mine=False,
            is_flag=True,
            color=color,
            number=1
        )

        fetched_tile = Tile.from_int((await BoardHandler.fetch(start=pointer, end=pointer)).data[0])

        self.assertEqual(fetched_tile, expected_tile)

    @patch("event.broker.EventBroker.publish")
    async def test_try_pointing_pointable_closed_special_click_already_flag(self, mock: AsyncMock):
        cursor_pos = Point(0, 0)
        pointer = Point(1, 1)
        color = Color.BLUE

        message = Message(
            event=PointEvent.TRY_POINTING,
            header={"sender": self.sender_id},
            payload=TryPointingPayload(
                cursor_position=cursor_pos,
                new_pointer=pointer,
                click_type=ClickType.SPECIAL_CLICK,
                color=color
            )
        )

        await BoardEventHandler.receive_try_pointing(message)

        # pointing-result, flag-set 발행하는지 확인
        self.assertEqual(len(mock.mock_calls), 2)

        # pointing-result
        got: Message[PointingResultPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, PointEvent.POINTING_RESULT)
        # receiver 값 확인
        self.assertEqual(len(got.header), 1)
        self.assertIn("receiver", got.header)
        self.assertEqual(got.header["receiver"], self.sender_id)
        # payload 확인
        self.assertEqual(type(got.payload), PointingResultPayload)
        self.assertTrue(got.payload.pointable)
        self.assertEqual(got.payload.pointer, pointer)

        # flag-set
        got: Message[FlagSetPayload] = mock.mock_calls[1].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, InteractionEvent.FLAG_SET)
        # payload 확인
        self.assertEqual(type(got.payload), FlagSetPayload)
        self.assertEqual(got.payload.position, pointer)
        self.assertIsNone(got.payload.color)
        self.assertFalse(got.payload.is_set)

        expected_tile = Tile.create(
            is_open=False,
            is_mine=True,
            is_flag=False,
            color=None,
            number=None
        )

        fetched_tile = Tile.from_int((await BoardHandler.fetch(start=pointer, end=pointer)).data[0])

        self.assertEqual(fetched_tile, expected_tile)

    @patch("event.broker.EventBroker.publish")
    async def test_try_pointing_not_pointable(self, mock: AsyncMock):
        cursor_pos = Point(0, 0)
        pointer = Point(2, 0)

        message = Message(
            event=PointEvent.TRY_POINTING,
            header={"sender": self.sender_id},
            payload=TryPointingPayload(
                cursor_position=cursor_pos,
                new_pointer=pointer,
                click_type=ClickType.GENERAL_CLICK,
                color=Color.BLUE
            )
        )

        await BoardEventHandler.receive_try_pointing(message)

        # pointing-result 발행하는지 확인
        mock.assert_called_once()
        got: Message[PointingResultPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, PointEvent.POINTING_RESULT)

        # receiver 값 확인
        self.assertEqual(len(got.header), 1)
        self.assertIn("receiver", got.header)
        self.assertEqual(got.header["receiver"], self.sender_id)

        # payload 확인
        self.assertEqual(type(got.payload), PointingResultPayload)
        self.assertFalse(got.payload.pointable)
        self.assertEqual(got.payload.pointer, pointer)

    @patch("event.broker.EventBroker.publish")
    async def test_check_movable_true(self, mock: AsyncMock):
        new_position = Point(0, 0)
        message = Message(
            event=MoveEvent.CHECK_MOVABLE,
            header={"sender": self.sender_id},
            payload=CheckMovablePayload(
                position=new_position
            )
        )

        await BoardEventHandler.receive_check_movable(message)

        mock.assert_called_once()
        got: Message[MovableResultPayload] = mock.mock_calls[0].args[0]

        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, MoveEvent.MOVABLE_RESULT)

        self.assertEqual(len(got.header), 1)
        self.assertIn("receiver", got.header)
        self.assertEqual(got.header["receiver"], self.sender_id)

        self.assertEqual(type(got.payload), MovableResultPayload)
        self.assertEqual(got.payload.position, new_position)
        self.assertTrue(got.payload.movable)

    @patch("event.broker.EventBroker.publish")
    async def test_check_movable_false(self, mock: AsyncMock):
        new_position = Point(1, 0)
        message = Message(
            event=MoveEvent.CHECK_MOVABLE,
            header={"sender": self.sender_id},
            payload=CheckMovablePayload(
                position=new_position
            )
        )

        await BoardEventHandler.receive_check_movable(message)

        mock.assert_called_once()
        got: Message[MovableResultPayload] = mock.mock_calls[0].args[0]

        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, MoveEvent.MOVABLE_RESULT)

        self.assertEqual(len(got.header), 1)
        self.assertIn("receiver", got.header)
        self.assertEqual(got.header["receiver"], self.sender_id)

        self.assertEqual(type(got.payload), MovableResultPayload)
        self.assertEqual(got.payload.position, new_position)
        self.assertFalse(got.payload.movable)


if __name__ == "__main__":
    unittest.main()
