from cursor.data import Cursor, Color
from cursor.data.handler import CursorHandler
from cursor.event.handler import CursorEventHandler
from message import Message
from message.payload import NewConnEvent, NewConnPayload, MyCursorPayload, CursorsPayload, PointEvent, PointingPayload, TryPointingPayload, PointingResultPayload, PointerSetPayload, ClickType, MoveEvent, MovingPayload, CheckMovablePayload
import unittest
from unittest.mock import AsyncMock, patch
from board import Point

"""
CursorEventHandler Test
----------------------------
Test
✅ : test 통과
❌ : test 실패 
🖊️ : test 작성
- new-conn-receiver
    - ✅| normal-case
        - ✅| without-cursors
        - 작성해야함
- pointing-receiver
    - ✅| normal-case
        - 작성 해야함
# - pointing_result-receiver
#     - 작성해야 함
- moving-receiver
    - ✅| normal-case
        - 작성 해야함
"""


class CursorEventHandler_NewConnReceiver_TestCase(unittest.IsolatedAsyncioTestCase):
    def tearDown(self):
        CursorHandler.cursor_dict = {}
        CursorHandler.watchers = {}
        CursorHandler.watching = {}

    @patch("event.EventBroker.publish")
    async def test_new_conn_receive_without_cursors(self, mock: AsyncMock):
        """
        new-conn-receiver
        without-cursors

        description:
            주변에 다른 커서 없을 경우
        ----------------------------
        trigger event ->

        - new-conn : message[NewConnPayload]
            - header : 
                - sender : conn_id
            - descrption :
                connection 연결

        ----------------------------
        publish event ->

        - multicast : message[MyCursorPayload]
            - header :
                - target_conns : [conn_id]
                - origin_event : my-cursor
            - descrption :
                생성된 커서 정보
        - multicast : message[CursorsPayload]
            - header :
                - target_conns : [conn_id]
                - origin_event : cursors
            - descrption :
                생성된 커서의 주변 커서 정보
        - multicast : message[CursorsPayload]
            - header :
                - target_conns : [conn_id의 주변 커서 id]
                - origin_event : cursors
            - descrption :
                주변 커서에게 생성된 커서 정보
        ----------------------------
        """

        # 초기 커서 셋팅
        CursorHandler.cursor_dict = {}

        # 생성될 커서 값
        expected_conn_id = "example"
        expected_height = 100
        expected_width = 100

        # trigger message 생성
        message = Message(
            event=NewConnEvent.NEW_CONN,
            payload=NewConnPayload(
                conn_id=expected_conn_id,
                width=expected_width,
                height=expected_height
            )
        )

        # trigger event
        await CursorEventHandler.receive_new_conn(message)

        # 호출 여부
        self.assertEqual(len(mock.mock_calls), 1)
        got: Message[MyCursorPayload] = mock.mock_calls[0].args[0]

        # message 확인
        self.assertEqual(type(got), Message)
        # message.event
        self.assertEqual(got.event, "multicast")
        # message.header
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertEqual(got.header["target_conns"][0], expected_conn_id)
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], NewConnEvent.MY_CURSOR)

        # message.payload
        self.assertEqual(type(got.payload), MyCursorPayload)
        self.assertIsNone(got.payload.pointer)
        self.assertEqual(got.payload.position.x, 0)
        self.assertEqual(got.payload.position.y, 0)
        self.assertIn(got.payload.color, Color)

    @patch("event.EventBroker.publish")
    async def test_receive_new_conn_with_cursors(self, mock: AsyncMock):
        # /docs/example/cursor-location.png
        # But B is at 0,0
        CursorHandler.cursor_dict = {
            "A": Cursor(
                conn_id="A",
                position=Point(-3, 3),
                pointer=None,
                height=6,
                width=6,
                # color 중요. 이따 비교에 써야 함.
                color=Color.RED
            ),
            "C": Cursor(
                conn_id="C",
                position=Point(2, -1),
                pointer=None,
                height=4,
                width=4,
                # color 중요.
                color=Color.BLUE
            )
        }

        original_cursors_len = 2
        original_cursors = [c.conn_id for c in list(CursorHandler.cursor_dict.values())]

        new_conn_id = "B"
        height = 7
        width = 7

        message = Message(
            event=NewConnEvent.NEW_CONN,
            payload=NewConnPayload(
                conn_id=new_conn_id,
                width=height,
                height=width
            )
        )

        await CursorEventHandler.receive_new_conn(message)

        # publish 횟수
        self.assertEqual(len(mock.mock_calls), 3)

        # my-cursor
        got = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # target_conns 나인지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertEqual(got.header["target_conns"][0], new_conn_id)
        # origin_event 확인
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], NewConnEvent.MY_CURSOR)
        # payload 확인
        self.assertEqual(type(got.payload), MyCursorPayload)
        self.assertEqual(got.payload.position, Point(0, 0))
        self.assertIsNone(got.payload.pointer)
        self.assertIn(got.payload.color, Color)

        my_color = got.payload.color

        # 커서 본인에게 보내는 cursors
        got = mock.mock_calls[1].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # target_conns 나인지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertEqual(got.header["target_conns"][0], new_conn_id)
        # origin_event 확인
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], NewConnEvent.CURSORS)
        # payload 확인
        self.assertEqual(type(got.payload), CursorsPayload)
        self.assertEqual(len(got.payload.cursors), 2)
        self.assertEqual(got.payload.cursors[0].color, Color.RED)
        self.assertEqual(got.payload.cursors[1].color, Color.BLUE)

        # 다른 커서들에게 보내는 cursors
        got = mock.mock_calls[2].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # target_conns 필터링 잘 됐는지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), original_cursors_len)
        self.assertEqual(set(got.header["target_conns"]), set(original_cursors))
        # origin_event 확인
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], NewConnEvent.CURSORS)
        # payload 확인
        self.assertEqual(type(got.payload), CursorsPayload)
        self.assertEqual(len(got.payload.cursors), 1)
        self.assertEqual(got.payload.cursors[0].color, my_color)

        # 연관관계 확인
        b_watching_list = CursorHandler.get_watching(new_conn_id)
        self.assertEqual(len(b_watching_list), original_cursors_len)

        b_watcher_list = CursorHandler.get_watchers(new_conn_id)
        self.assertEqual(len(b_watcher_list), original_cursors_len)


class CursorEventHandler_PointingReceiver_TestCase(unittest.IsolatedAsyncioTestCase):
    @patch("event.EventBroker.publish")
    async def test_receive_pointing(self, mock: AsyncMock):
        expected_conn_id = "example"
        expected_width = 100
        expected_height = 100

        cursor = Cursor.create(conn_id=expected_conn_id)
        cursor.set_size(expected_width, expected_height)

        CursorHandler.cursor_dict = {
            expected_conn_id: cursor
        }

        click_type = ClickType.GENERAL_CLICK
        pointer = Point(0, 0)

        message = Message(
            event=PointEvent.POINTING,
            header={"sender": expected_conn_id},
            payload=PointingPayload(
                click_type=click_type,
                position=pointer
            )
        )

        await CursorEventHandler.receive_pointing(message)

        # try-pointing 발행하는지 확인
        mock.assert_called_once()
        got = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, PointEvent.TRY_POINTING)

        # sender 확인
        self.assertIn("sender", got.header)
        self.assertEqual(type(got.header["sender"]), str)
        self.assertEqual(got.header["sender"], expected_conn_id)

        # payload 확인
        self.assertEqual(type(got.payload), TryPointingPayload)
        self.assertEqual(got.payload.click_type, click_type)
        self.assertEqual(got.payload.cursor_position, cursor.position)
        self.assertEqual(got.payload.color, cursor.color)
        self.assertEqual(got.payload.new_pointer, Point(0, 0))

    @patch("event.EventBroker.publish")
    async def test_receive_pointing_result_pointable(self, mock: AsyncMock):
        expected_conn_id = "example"

        cursor = Cursor.create(conn_id=expected_conn_id)
        cursor.pointer = Point(0, 0)

        CursorHandler.cursor_dict = {
            expected_conn_id: cursor
        }

        pointer = Point(1, 0)
        message = Message(
            event=PointEvent.POINTING_RESULT,
            header={"receiver": expected_conn_id},
            payload=PointingResultPayload(
                pointer=pointer,
                pointable=True
            )
        )

        await CursorEventHandler.receive_pointing_result(message)

        # pointer-set 발행하는지 확인
        mock.assert_called_once()
        got = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, PointEvent.POINTER_SET)

        # target_conns -> 본인에게 보내는지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertEqual(got.header["target_conns"][0], expected_conn_id)

        # payload 확인
        self.assertEqual(type(got.payload), PointerSetPayload)
        self.assertEqual(got.payload.origin_position, Point(0, 0))
        self.assertEqual(got.payload.color, cursor.color)
        self.assertEqual(got.payload.new_position, pointer)

        self.assertEqual(cursor.pointer, pointer)

    @patch("event.EventBroker.publish")
    async def test_receive_pointing_result_not_pointable(self, mock: AsyncMock):
        expected_conn_id = "example"

        cursor = Cursor.create(conn_id=expected_conn_id)
        cursor.pointer = Point(0, 0)

        pointer = Point(1, 0)
        CursorHandler.cursor_dict = {
            expected_conn_id: cursor
        }

        message = Message(
            event=PointEvent.POINTING_RESULT,
            header={"receiver": expected_conn_id},
            payload=PointingResultPayload(
                pointer=pointer,
                pointable=False
            )
        )

        await CursorEventHandler.receive_pointing_result(message)

        # pointer-set 발행하는지 확인
        mock.assert_called_once()
        got = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, PointEvent.POINTER_SET)

        # target_conns -> 본인에게 보내는지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertEqual(got.header["target_conns"][0], expected_conn_id)

        # payload 확인
        self.assertEqual(type(got.payload), PointerSetPayload)
        self.assertEqual(got.payload.origin_position, Point(0, 0))
        self.assertEqual(got.payload.color, cursor.color)
        self.assertIsNone(got.payload.new_position)

        # 포인터 위치 업데이트 되지 않음
        self.assertNotEqual(cursor.pointer, pointer)

    @patch("event.EventBroker.publish")
    async def test_receive_pointing_result_pointable_no_original_pointer(self, mock: AsyncMock):
        expected_conn_id = "example"

        cursor = Cursor.create(conn_id=expected_conn_id)

        CursorHandler.cursor_dict = {
            expected_conn_id: cursor
        }

        pointer = Point(1, 0)
        message = Message(
            event=PointEvent.POINTING_RESULT,
            header={"receiver": expected_conn_id},
            payload=PointingResultPayload(
                pointer=pointer,
                pointable=True,
            )
        )

        await CursorEventHandler.receive_pointing_result(message)

        # pointer-set 발행하는지 확인
        mock.assert_called_once()
        got = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, PointEvent.POINTER_SET)

        # target_conns -> 본인에게 보내는지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertEqual(got.header["target_conns"][0], expected_conn_id)

        # payload 확인
        self.assertEqual(type(got.payload), PointerSetPayload)
        self.assertIsNone(got.payload.origin_position)
        self.assertEqual(got.payload.color, cursor.color)
        self.assertEqual(got.payload.new_position, pointer)


class CursorEventHandler_MovingReceiver_TestCase(unittest.IsolatedAsyncioTestCase):
    """
    TODO: 테스트 케이스
    1. 자기 자신 위치로 이동
    2. 주변 8칸 벗어나게 이동
    """

    def setUp(self):
        self.conn_id = "example"

        self.cursor = Cursor.create(conn_id=self.conn_id)

        CursorHandler.cursor_dict = {
            self.conn_id: self.cursor
        }

    def tearDown(self):
        CursorHandler.cursor_dict = {}

    @patch("event.EventBroker.publish")
    async def test_receive_moving(self, mock: AsyncMock):
        message = Message(
            event=MoveEvent.MOVING,
            header={"sender": self.conn_id},
            payload=CheckMovablePayload(
                position=Point(
                    # 위로 한칸 이동
                    x=self.cursor.position.x,
                    y=self.cursor.position.y + 1,
                )
            )
        )

        await CursorEventHandler.receive_moving(message)

        # check-movable 이벤트 발행 확인
        mock.assert_called_once()
        got = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, MoveEvent.CHECK_MOVABLE)

        # sender 보냈는지 확인
        self.assertIn("sender", got.header)
        self.assertEqual(type(got.header["sender"]), str)
        self.assertEqual(got.header["sender"], self.conn_id)

        # 새로운 위치에 대해 check-movable 발행하는지 확인
        self.assertEqual(type(got.payload), CheckMovablePayload)
        self.assertEqual(got.payload.position, message.payload.position)


if __name__ == "__main__":
    unittest.main()
