from cursor.data import Color
from board.data import Point
from board.event.handler import BoardEventHandler
from board.data.handler.test.fixtures import setup_board_fake, setup_board
from message import Message
from message.payload import \
    FetchTilesPayload, TilesEvent, TilesPayload, NewConnEvent, NewConnPayload, TryPointingPayload, PointingResultPayload, PointEvent, ClickType, MoveEvent, CheckMovablePayload, MovableResultPayload

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
    def setUp(self):
        setup_board_fake()

    @patch("event.EventBroker.publish")
    async def test_fetch_tiles_receiver_normal_case(self, mock: AsyncMock):
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

        # trigger message 생성
        message = Message(
            event=TilesEvent.FETCH_TILES,
            payload=FetchTilesPayload(Point(-2, 1), Point(1, -2)),
            header={"sender": "ayo"},

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
        self.assertEqual(got.payload.start_p.x, -2)
        self.assertEqual(got.payload.start_p.y, 1)
        self.assertEqual(got.payload.end_p.x, 1)
        self.assertEqual(got.payload.end_p.y, -2)
        self.assertEqual(got.payload.tiles, "df12df12er56er56")

    @patch("event.EventBroker.publish")
    async def test_receive_new_conn(self, mock: AsyncMock):
        message = Message(
            event=NewConnEvent.NEW_CONN,
            header={"sender": "ayo"},
            payload=NewConnPayload(conn_id="not important", width=2, height=2)
        )

        await BoardEventHandler.receive_new_conn(message)

        mock.assert_called_once()
        got: Message[TilesPayload] = mock.mock_calls[0].args[0]

        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")

        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertEqual(got.header["target_conns"][0], message.header["sender"])

        self.assertEqual(type(got.payload), TilesPayload)
        self.assertEqual(got.payload.start_p.x, -2)
        self.assertEqual(got.payload.start_p.y, 2)
        self.assertEqual(got.payload.end_p.x, 2)
        self.assertEqual(got.payload.end_p.y, -2)
        self.assertEqual(got.payload.tiles, "df123df123df123er567er567")


class BoardEventHandler_PointingReceiver_TestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        setup_board()
        self.sender_id = "ayo"

    @patch("event.EventBroker.publish")
    async def test_try_pointing_pointable(self, mock: AsyncMock):
        pointer = Point(0, 0)

        message = Message(
            event=PointEvent.TRY_POINTING,
            header={"sender": self.sender_id},
            payload=TryPointingPayload(
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

    @patch("event.EventBroker.publish")
    async def test_try_pointing_pointable_closed(self, mock: AsyncMock):
        pointer = Point(1, 0)

        message = Message(
            event=PointEvent.TRY_POINTING,
            header={"sender": self.sender_id},
            payload=TryPointingPayload(
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

    @patch("event.EventBroker.publish")
    async def test_try_pointing_not_pointable(self, mock: AsyncMock):
        pointer = Point(2, 0)

        message = Message(
            event=PointEvent.TRY_POINTING,
            header={"sender": self.sender_id},
            payload=TryPointingPayload(
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

    @patch("event.EventBroker.publish")
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

    @patch("event.EventBroker.publish")
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
