import asyncio
from data.board import Section
from datetime import datetime
from data.cursor import Cursor, Color
from handler.cursor import CursorHandler
from receiver.cursor import CursorEventHandler
from event.message import Message
from event.payload import (
    NewConnEvent,
    MyCursorPayload,
    CursorsPayload,
    CursorsDiedPayload,
    PointEvent,
    PointingPayload,
    TryPointingPayload,
    PointingResultPayload,
    PointerSetPayload,
    ClickType,
    MoveEvent,
    MovingPayload,
    CheckMovablePayload,
    MovableResultPayload,
    MovedPayload,
    InteractionEvent,
    YouDiedPayload,
    SingleTileOpenedPayload,
    TilesOpenedPayload,
    FlagSetPayload,
    ConnClosedPayload,
    CursorQuitPayload,
    SetViewSizePayload,
    ErrorEvent,
    ErrorPayload,
    NewCursorCandidatePayload,
    SendChatPayload,
    ChatPayload,
    ChatEvent
)
from .fixtures import setup_cursor_locations
import unittest
from unittest.mock import AsyncMock, patch
from data.board import Point, Tile, Tiles
from config import VIEW_SIZE_LIMIT, CHAT_MAX_LENGTH

"""
CursorEventHandler Test
----------------------------
Test
✅ : test 통과
❌ : test 실패
🖊️ : test 작성
- new-cursor-receiver
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


class CursorEventHandler_NewCursorCandidateReceiver_TestCase(unittest.IsolatedAsyncioTestCase):
    def tearDown(self):
        CursorHandler.cursor_dict = {}
        CursorHandler.watchers = {}
        CursorHandler.watching = {}

    @patch("event.broker.EventBroker.publish")
    async def test_new_cursor_candidate_receive_without_cursors(self, mock: AsyncMock):
        """
        new-cursor-candidate-receiver
        without-cursors

        description:
            주변에 다른 커서 없을 경우
        ----------------------------
        trigger event ->

        - new-cursor-candidate : message[NewConnPayload]
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
        position = Point(1, 1)

        # trigger message 생성
        message = Message(
            event=NewConnEvent.NEW_CURSOR_CANDIDATE,
            payload=NewCursorCandidatePayload(
                conn_id=expected_conn_id,
                width=expected_width,
                height=expected_height,
                position=position
            )
        )

        # trigger event
        await CursorEventHandler.receive_new_cursor_candidate(message)

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
        self.assertEqual(got.payload.id, expected_conn_id)
        self.assertIsNone(got.payload.pointer)
        self.assertEqual(got.payload.position, position)
        self.assertIn(got.payload.color, Color)

    @patch("event.broker.EventBroker.publish")
    async def test_new_cursor_candidate_receive_without_cursors_race(self, mock: AsyncMock):
        conn_1 = "1"
        conn_2 = "2"
        height = 1
        width = 1
        position = Point(0, 0)

        new_cursor_1_msg = Message(
            event=NewConnEvent.NEW_CURSOR_CANDIDATE,
            payload=NewCursorCandidatePayload(conn_id=conn_1, width=width, height=height, position=position)
        )
        new_cursor_2_msg = Message(
            event=NewConnEvent.NEW_CURSOR_CANDIDATE,
            payload=NewCursorCandidatePayload(conn_id=conn_2, width=width, height=height, position=position)
        )

        # 코루틴 스위칭을 위해 sleep. 이게 되는 이유를 모르겠다.
        async def sleep(_):
            await asyncio.sleep(0)
        mock.side_effect = sleep

        await asyncio.gather(
            CursorEventHandler.receive_new_cursor_candidate(new_cursor_1_msg),
            CursorEventHandler.receive_new_cursor_candidate(new_cursor_2_msg)
        )
        # 첫번째 conn: my-cursor, 두번째 conn: my-cursor, cursors * 2
        self.assertEqual(len(mock.mock_calls), 4)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_new_cursor_candidate_with_cursors(self, mock: AsyncMock):
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
                color=Color.RED,
            ),
            "C": Cursor(
                conn_id="C",
                position=Point(2, -1),
                pointer=None,
                height=4,
                width=4,
                # color 중요.
                color=Color.BLUE,
            )
        }
        # 지남. cursors에서 안 보여야 함.
        a_revive_at = datetime(year=1000, month=1, day=1)
        CursorHandler.cursor_dict["A"].revive_at = a_revive_at

        # 안 지남. cursors에서 보여야 함.
        c_revive_at = datetime(year=2200, month=1, day=1)
        CursorHandler.cursor_dict["C"].revive_at = c_revive_at

        original_cursors_len = 2
        original_cursors = [c.id for c in list(CursorHandler.cursor_dict.values())]

        new_conn_id = "B"
        height = 7
        width = 7
        position = Point(0, 0)

        message = Message(
            event=NewConnEvent.NEW_CURSOR_CANDIDATE,
            payload=NewCursorCandidatePayload(
                conn_id=new_conn_id,
                width=height,
                height=width,
                position=position
            )
        )

        await CursorEventHandler.receive_new_cursor_candidate(message)

        # publish 횟수
        self.assertEqual(len(mock.mock_calls), 3)

        # my-cursor
        got: Message[MyCursorPayload] = mock.mock_calls[0].args[0]

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
        self.assertEqual(got.payload.id, new_conn_id)
        self.assertEqual(got.payload.position, position)
        self.assertIsNone(got.payload.pointer)
        self.assertIn(got.payload.color, Color)

        my_color = got.payload.color

        # 커서 본인에게 보내는 cursors
        got: Message[CursorsPayload] = mock.mock_calls[1].args[0]
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
        self.assertIsNone(got.payload.cursors[0].revive_at)
        self.assertEqual(got.payload.cursors[1].color, Color.BLUE)
        self.assertEqual(got.payload.cursors[1].revive_at, c_revive_at.astimezone().isoformat())

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
    def setUp(self) -> None:
        curs = setup_cursor_locations()
        self.cur_a = curs[0]
        self.cur_b = curs[1]
        self.cur_c = curs[2]

    def tearDown(self):
        CursorHandler.cursor_dict = {}
        CursorHandler.watchers = {}
        CursorHandler.watching = {}

    @patch("event.broker.EventBroker.publish")
    async def test_receive_pointing(self, mock: AsyncMock):
        click_type = ClickType.GENERAL_CLICK
        pointer = Point(0, 0)

        message = Message(
            event=PointEvent.POINTING,
            header={"sender": self.cur_a.id},
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
        self.assertEqual(got.header["sender"], self.cur_a.id)

        # payload 확인
        self.assertEqual(type(got.payload), TryPointingPayload)
        self.assertEqual(got.payload.click_type, click_type)
        self.assertEqual(got.payload.color, self.cur_a.color)
        self.assertEqual(got.payload.cursor_position, self.cur_a.position)
        self.assertEqual(got.payload.new_pointer, pointer)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_pointing_out_of_bound(self, mock: AsyncMock):
        click_type = ClickType.GENERAL_CLICK
        pointer = Point(100, 0)

        message = Message(
            event=PointEvent.POINTING,
            header={"sender": self.cur_a.id},
            payload=PointingPayload(
                click_type=click_type,
                position=pointer
            )
        )

        await CursorEventHandler.receive_pointing(message)

        # error 발행하는지 확인
        mock.assert_called_once()
        got = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")

        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], ErrorEvent.ERROR)

        # target_conns -> 본인에게 보내는지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn("A", got.header["target_conns"])

        # payload 확인
        self.assertEqual(type(got.payload), ErrorPayload)
        self.assertEqual(got.payload.msg, "pointer is out of cursor view")

    @patch("event.broker.EventBroker.publish")
    async def test_receive_pointing_dead(self, mock: AsyncMock):
        from datetime import datetime
        self.cur_a.revive_at = datetime(year=2200, month=1, day=1, hour=0, minute=0, second=0)

        click_type = ClickType.GENERAL_CLICK
        pointer = Point(0, 0)

        message = Message(
            event=PointEvent.POINTING,
            header={"sender": self.cur_a.id},
            payload=PointingPayload(
                click_type=click_type,
                position=pointer
            )
        )

        await CursorEventHandler.receive_pointing(message)

        mock.assert_not_called()

    @patch("event.broker.EventBroker.publish")
    async def test_receive_pointing_result_pointable(self, mock: AsyncMock):
        origin_pointer = self.cur_a.pointer
        pointer = Point(1, 0)
        message = Message(
            event=PointEvent.POINTING_RESULT,
            header={"receiver": self.cur_a.id},
            payload=PointingResultPayload(
                pointer=pointer,
                pointable=True
            )
        )

        await CursorEventHandler.receive_pointing_result(message)

        # pointer-set 발행하는지 확인
        mock.assert_called_once()
        got: Message[PointerSetPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")

        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], PointEvent.POINTER_SET)

        # target_conns -> 본인 + B 에게 보내는지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 2)
        self.assertIn("A", got.header["target_conns"])
        self.assertIn("B", got.header["target_conns"])

        # payload 확인
        self.assertEqual(type(got.payload), PointerSetPayload)
        self.assertEqual(got.payload.id, self.cur_a.id)
        self.assertEqual(got.payload.pointer, self.cur_a.pointer)

        self.assertEqual(self.cur_a.pointer, pointer)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_pointing_result_pointable_no_original_pointer(self, mock: AsyncMock):
        pointer = Point(1, 0)
        message = Message(
            event=PointEvent.POINTING_RESULT,
            header={"receiver": self.cur_a.id},
            payload=PointingResultPayload(
                pointer=pointer,
                pointable=True,
            )
        )

        await CursorEventHandler.receive_pointing_result(message)

        # pointer-set 발행하는지 확인
        mock.assert_called_once()
        got: Message[PointerSetPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")

        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], PointEvent.POINTER_SET)

        # target_conns -> 본인 + B 에게 보내는지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 2)
        self.assertIn("A", got.header["target_conns"])
        self.assertIn("B", got.header["target_conns"])

        # payload 확인
        self.assertEqual(type(got.payload), PointerSetPayload)
        self.assertEqual(got.payload.id, self.cur_a.id)
        self.assertEqual(got.payload.pointer, self.cur_a.pointer)


class CursorEventHandler_MovingReceiver_TestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        curs = setup_cursor_locations()
        self.cur_a = curs[0]
        self.cur_b = curs[1]
        self.cur_c = curs[2]

    def tearDown(self):
        CursorHandler.cursor_dict = {}
        CursorHandler.watchers = {}
        CursorHandler.watching = {}

    @patch("event.broker.EventBroker.publish")
    async def test_receive_moving(self, mock: AsyncMock):
        message = Message(
            event=MoveEvent.MOVING,
            header={"sender": self.cur_a.id},
            payload=CheckMovablePayload(
                position=Point(
                    # 위로 한칸 이동
                    x=self.cur_a.position.x,
                    y=self.cur_a.position.y + 1,
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
        self.assertEqual(got.header["sender"], self.cur_a.id)

        # 새로운 위치에 대해 check-movable 발행하는지 확인
        self.assertEqual(type(got.payload), CheckMovablePayload)
        self.assertEqual(got.payload.position, message.payload.position)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_moving_same_position(self, mock: AsyncMock):
        message = Message(
            event=MoveEvent.MOVING,
            header={"sender": self.cur_a.id},
            payload=CheckMovablePayload(
                position=self.cur_a.position
            )
        )

        await CursorEventHandler.receive_moving(message)

        # error 발행하는지 확인
        mock.assert_called_once()
        got = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")

        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], ErrorEvent.ERROR)

        # target_conns -> 본인에게 보내는지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn("A", got.header["target_conns"])

        # payload 확인
        self.assertEqual(type(got.payload), ErrorPayload)
        self.assertEqual(got.payload.msg, "moving to current position is not allowed")

    @patch("event.broker.EventBroker.publish")
    async def test_receive_moving_out_of_bounds(self, mock: AsyncMock):
        message = Message(
            event=MoveEvent.MOVING,
            header={"sender": self.cur_a.id},
            payload=CheckMovablePayload(
                position=Point(
                    x=self.cur_a.position.x + 500,
                    y=self.cur_a.position.y
                )
            )
        )

        await CursorEventHandler.receive_moving(message)

        # error 발행하는지 확인
        mock.assert_called_once()
        got = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")

        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], ErrorEvent.ERROR)

        # target_conns -> 본인에게 보내는지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn("A", got.header["target_conns"])

        # payload 확인
        self.assertEqual(type(got.payload), ErrorPayload)
        self.assertEqual(got.payload.msg, "only moving to 8 nearby tiles is allowed")

    @patch("event.broker.EventBroker.publish")
    async def test_receive_movable_result_not_movable(self, mock: AsyncMock):
        message = Message(
            event=MoveEvent.MOVABLE_RESULT,
            header={"receiver": self.cur_a.id},
            payload=MovableResultPayload(
                movable=False,
                position=Point(0, 0)
            )
        )

        await CursorEventHandler.receive_movable_result(message)

        # error 발행하는지 확인
        mock.assert_called_once()
        got: Message[ErrorPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")

        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], ErrorEvent.ERROR)

        # target_conns -> 본인에게 보내는지 확인
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn("A", got.header["target_conns"])

        # payload 확인
        self.assertEqual(type(got.payload), ErrorPayload)
        self.assertEqual(got.payload.msg, "moving to given tile is not available")

    @patch("event.broker.EventBroker.publish")
    async def test_receive_movable_result_a_up(self, mock: AsyncMock):
        """
        A가 한 칸 위로 이동.
        B, C에게 move 이벤트가 전달되고, B의 시야에서 사라진다.
        """
        original_position = self.cur_a.position
        message = Message(
            event=MoveEvent.MOVABLE_RESULT,
            header={"receiver": self.cur_a.id},
            payload=MovableResultPayload(
                movable=True,
                position=Point(
                    x=self.cur_a.position.x,
                    y=self.cur_a.position.y + 1,
                )
            )
        )

        await CursorEventHandler.receive_movable_result(message)

        # moved 이벤트만 발행됨
        self.assertEqual(len(mock.mock_calls), 1)

        # moved
        got: Message[MovedPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], MoveEvent.MOVED)
        # target_conns 확인, [B]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn("B", got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), MovedPayload)
        self.assertEqual(got.payload.id, self.cur_a.id)
        self.assertEqual(got.payload.new_position, message.payload.position)

        # watcher 관계 확인
        a_watchings = CursorHandler.get_watching("A")
        self.assertEqual(len(a_watchings), 1)
        self.assertIn("C", a_watchings)

        a_watchers = CursorHandler.get_watchers("A")
        self.assertEqual(len(a_watchers), 0)

        b_watchings = CursorHandler.get_watching("B")
        self.assertEqual(len(b_watchings), 1)
        self.assertIn("C", b_watchings)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_movable_result_b_up_right(self, mock: AsyncMock):
        """
        B가 한 칸 위, 한 칸 오른쪽로 이동.
        A, C의 뷰에 B가 추가된다.
        """
        original_position = self.cur_b.position
        message = Message(
            event=MoveEvent.MOVABLE_RESULT,
            header={"receiver": self.cur_b.id},
            payload=MovableResultPayload(
                movable=True,
                position=Point(
                    x=self.cur_b.position.x + 1,
                    y=self.cur_b.position.y + 1,
                )
            )
        )

        await CursorEventHandler.receive_movable_result(message)

        # cursors 이벤트만 발행됨
        self.assertEqual(len(mock.mock_calls), 1)

        # cursors
        got: Message[CursorsPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], NewConnEvent.CURSORS)
        # target_conns 확인, [A, C]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 2)
        self.assertIn("A", got.header["target_conns"])
        self.assertIn("C", got.header["target_conns"])
        # payload 확인, B의 정보
        self.assertEqual(type(got.payload), CursorsPayload)
        self.assertEqual(len(got.payload.cursors), 1)
        self.assertEqual(got.payload.cursors[0].id, self.cur_b.id)
        self.assertEqual(got.payload.cursors[0].position, message.payload.position)
        self.assertEqual(got.payload.cursors[0].pointer, self.cur_b.pointer)
        self.assertEqual(got.payload.cursors[0].color, self.cur_b.color)

        # watcher 관계 확인
        b_watchers = CursorHandler.get_watchers("B")
        self.assertEqual(len(b_watchers), 2)
        self.assertIn("A", b_watchers)
        self.assertIn("C", b_watchers)

        a_watchings = CursorHandler.get_watching("A")
        self.assertEqual(len(a_watchings), 2)
        self.assertIn("B", a_watchings)
        self.assertIn("C", a_watchings)

        c_watchings = CursorHandler.get_watching("C")
        self.assertEqual(len(c_watchings), 1)
        self.assertIn("B", c_watchings)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_movable_result_c_left(self, mock: AsyncMock):
        """
        C가 한 칸 왼쪽으로 이동.
        C의 뷰에 A, B가 추가되고, A, B에 move가 발행된다.
        """
        original_position = self.cur_c.position
        message = Message(
            event=MoveEvent.MOVABLE_RESULT,
            header={"receiver": self.cur_c.id},
            payload=MovableResultPayload(
                movable=True,
                position=Point(
                    x=self.cur_c.position.x - 1,
                    y=self.cur_c.position.y,
                )
            )
        )

        await CursorEventHandler.receive_movable_result(message)

        # cursors, moved 이벤트 발행됨
        self.assertEqual(len(mock.mock_calls), 2)

        # cursors
        got: Message[CursorsPayload] = mock.mock_calls[1].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], NewConnEvent.CURSORS)
        # target_conns 확인, [C]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn("C", got.header["target_conns"])
        # payload 확인, A, B의 정보
        self.assertEqual(type(got.payload), CursorsPayload)
        self.assertEqual(len(got.payload.cursors), 2)
        self.assertEqual(got.payload.cursors[0].id, self.cur_a.id)
        self.assertEqual(got.payload.cursors[0].position, self.cur_a.position)
        self.assertEqual(got.payload.cursors[0].pointer, self.cur_a.pointer)
        self.assertEqual(got.payload.cursors[0].color, self.cur_a.color)
        self.assertEqual(got.payload.cursors[1].id, self.cur_b.id)
        self.assertEqual(got.payload.cursors[1].position, self.cur_b.position)
        self.assertEqual(got.payload.cursors[1].pointer, self.cur_b.pointer)
        self.assertEqual(got.payload.cursors[1].color, self.cur_b.color)

        # moved
        got1: Message[MovedPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got1), Message)
        self.assertEqual(got1.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got1.header)
        self.assertEqual(got1.header["origin_event"], MoveEvent.MOVED)
        # target_conns 확인, [A, B]
        self.assertIn("target_conns", got1.header)
        self.assertEqual(len(got1.header["target_conns"]), 2)
        self.assertIn("A", got1.header["target_conns"])
        self.assertIn("B", got1.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got1.payload), MovedPayload)
        self.assertEqual(got1.payload.id, self.cur_c.id)
        self.assertEqual(got1.payload.new_position, message.payload.position)

        # watcher 관계 확인
        c_watchings = CursorHandler.get_watching("C")
        self.assertEqual(len(c_watchings), 2)
        self.assertIn("A", c_watchings)
        self.assertIn("B", c_watchings)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_movable_result_b_down(self, mock: AsyncMock):
        """
        B가 한 칸 아래로 이동.
        B의 뷰에서 A가 사라진다.
        """
        original_position = self.cur_c.position
        message = Message(
            event=MoveEvent.MOVABLE_RESULT,
            header={"receiver": self.cur_b.id},
            payload=MovableResultPayload(
                movable=True,
                position=Point(
                    x=self.cur_b.position.x,
                    y=self.cur_b.position.y - 1,
                )
            )
        )

        await CursorEventHandler.receive_movable_result(message)

        mock.assert_not_called()

        # watcher 관계 확인
        c_watchings = CursorHandler.get_watching("C")
        self.assertEqual(len(c_watchings), 0)


class CursorEventHandler_TileStateChanged_TestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        curs = setup_cursor_locations()
        self.cur_a = curs[0]
        self.cur_b = curs[1]
        self.cur_c = curs[2]

    def tearDown(self):
        CursorHandler.cursor_dict = {}
        CursorHandler.watchers = {}
        CursorHandler.watching = {}

    @patch("event.broker.EventBroker.publish")
    async def test_receive_flag_set(self, mock: AsyncMock):
        position = Point(-4, -3)
        color = Color.BLUE
        is_set = True

        message: Message[FlagSetPayload] = Message(
            event=InteractionEvent.FLAG_SET,
            payload=FlagSetPayload(
                position=position,
                color=color,
                is_set=is_set
            )
        )

        await CursorEventHandler.receive_flag_set(message)

        # flag-set 발행 확인
        self.assertEqual(len(mock.mock_calls), 1)

        # flag-set
        got: Message[FlagSetPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], InteractionEvent.FLAG_SET)
        # target_conns 확인, [A, B]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 2)
        self.assertIn("A", got.header["target_conns"])
        self.assertIn("B", got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), FlagSetPayload)
        self.assertEqual(got.payload.position, position)
        self.assertEqual(got.payload.color, color)
        self.assertEqual(got.payload.is_set, is_set)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_single_tile_open(self, mock: AsyncMock):
        self.cur_b.pointer = Point(1, 1)

        position = Point(-4, -3)
        tile = Tile.from_int(0b11000000)  # open, mine
        tile_str = Tiles(data=bytearray([tile.data])).to_str()

        message: Message[SingleTileOpenedPayload] = Message(
            event=InteractionEvent.SINGLE_TILE_OPENED,
            payload=SingleTileOpenedPayload(
                position=position,
                tile=tile_str
            )
        )

        await CursorEventHandler.receive_single_tile_opened(message)

        # single-tile-opened, you-died, cursors-died 발행 확인
        self.assertEqual(len(mock.mock_calls), 3)

        # single-tile-opened
        got: Message[SingleTileOpenedPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], InteractionEvent.SINGLE_TILE_OPENED)
        # target_conns 확인, [A, B]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 2)
        self.assertIn("A", got.header["target_conns"])
        self.assertIn("B", got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), SingleTileOpenedPayload)
        self.assertEqual(got.payload.position, position)
        self.assertEqual(bytearray.fromhex(got.payload.tile)[0], tile.data)

        # you-died
        got: Message[YouDiedPayload] = mock.mock_calls[1].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], InteractionEvent.YOU_DIED)
        # target_conns 확인, [B]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn("B", got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), YouDiedPayload)

        revive_at = got.payload.revive_at
        from datetime import datetime
        # TODO
        # datetime.now mocking 후 test
        # self.assertEqual(got.payload.revive_at, something)
        datetime.fromisoformat(revive_at)

        # cursors-died
        got: Message[CursorsDiedPayload] = mock.mock_calls[2].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], InteractionEvent.CURSORS_DIED)
        # target_conns 확인, [B]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn("B", got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), CursorsDiedPayload)
        self.assertEqual(got.payload.revive_at, revive_at)
        self.assertEqual(len(got.payload.cursors), 1)
        self.assertEqual(got.payload.cursors[0].color, self.cur_b.color)

        self.assertIsNone(self.cur_b.pointer)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_single_tile_open_mine_explode_already_died(self, mock: AsyncMock):
        self.cur_b.pointer = Point(1, 1)
        self.cur_b.revive_at = datetime(year=2200, month=1, day=1)

        position = Point(-4, -3)
        tile = Tile.from_int(0b11000000)  # open, mine
        tile_str = Tiles(data=bytearray([tile.data])).to_str()

        message: Message[SingleTileOpenedPayload] = Message(
            event=InteractionEvent.SINGLE_TILE_OPENED,
            payload=SingleTileOpenedPayload(
                position=position,
                tile=tile_str
            )
        )

        await CursorEventHandler.receive_single_tile_opened(message)

        # single-tile-opened 발행 확인
        self.assertEqual(len(mock.mock_calls), 1)

        # single-tile-opened
        got: Message[SingleTileOpenedPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], InteractionEvent.SINGLE_TILE_OPENED)
        # target_conns 확인, [A, B]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 2)
        self.assertIn("A", got.header["target_conns"])
        self.assertIn("B", got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), SingleTileOpenedPayload)
        self.assertEqual(got.payload.position, position)
        self.assertEqual(bytearray.fromhex(got.payload.tile)[0], tile.data)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_tiles_opened(self, mock: AsyncMock):
        start = Point(-3, 1)
        end = Point(-2, 0)
        tile_str = "1234123412341234"

        message: Message[TilesOpenedPayload] = Message(
            event=InteractionEvent.TILES_OPENED,
            payload=TilesOpenedPayload(
                start_p=start,
                end_p=end,
                tiles=tile_str
            )
        )

        await CursorEventHandler.receive_tiles_opened(message)

        # tiles-opened 확인
        self.assertEqual(len(mock.mock_calls), 1)

        # tiles-opened
        got: Message[TilesOpenedPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], InteractionEvent.TILES_OPENED)
        # target_conns 확인, [A, B, C]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 3)
        self.assertIn("A", got.header["target_conns"])
        self.assertIn("B", got.header["target_conns"])
        self.assertIn("C", got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), TilesOpenedPayload)
        self.assertEqual(got.payload.start_p, start)
        self.assertEqual(got.payload.end_p, end)
        self.assertEqual(got.payload.tiles, tile_str)


class CursorEventHandler_ConnClosed_TestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        curs = setup_cursor_locations()
        self.cur_a = curs[0]
        self.cur_b = curs[1]
        self.cur_c = curs[2]

    def tearDown(self):
        CursorHandler.cursor_dict = {}
        CursorHandler.watchers = {}
        CursorHandler.watching = {}

    @patch("event.broker.EventBroker.publish")
    async def test_receive_conn_closed(self, mock: AsyncMock):
        message = Message(
            event=NewConnEvent.CONN_CLOSED,
            header={"sender": self.cur_a.id},
            payload=ConnClosedPayload()
        )

        await CursorEventHandler.receive_conn_closed(message)

        mock.assert_called_once()

        # cursor-quit
        got: Message[CursorQuitPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], NewConnEvent.CURSOR_QUIT)
        # target_conns 확인, [B]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn("B", got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), CursorQuitPayload)
        self.assertEqual(got.payload.id, self.cur_a.id)

        # watcher 관계 확인
        b_watchings = CursorHandler.get_watching("B")
        self.assertEqual(len(b_watchings), 1)
        self.assertIn("C", b_watchings)

        c_watchers = CursorHandler.get_watchers("C")
        self.assertEqual(len(c_watchers), 1)
        self.assertIn("B", c_watchers)

        # 커서 지워졌나 확인
        self.assertIsNone(CursorHandler.get_cursor(self.cur_a.id))


class CursorEventHandler_SetViewSize_TestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        curs = setup_cursor_locations()
        self.cur_a = curs[0]
        self.cur_b = curs[1]
        self.cur_c = curs[2]

    def tearDown(self):
        CursorHandler.cursor_dict = {}
        CursorHandler.watchers = {}
        CursorHandler.watching = {}

    @patch("event.broker.EventBroker.publish")
    async def test_receive_set_view_size_grow_shrink_both(self, mock: AsyncMock):
        message = Message(
            event=NewConnEvent.SET_VIEW_SIZE,
            header={"sender": self.cur_a.id},
            payload=SetViewSizePayload(
                width=self.cur_a.width-2,
                height=self.cur_a.height+1
            )
        )

        await CursorEventHandler.receive_set_view_size(message)

        mock.assert_called_once()

        # cursors
        got: Message[CursorsPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], NewConnEvent.CURSORS)
        # target_conns 확인, [A]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn(self.cur_a.id, got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), CursorsPayload)
        self.assertEqual(len(got.payload.cursors), 1)
        self.assertEqual(got.payload.cursors[0].id, self.cur_b.id)
        self.assertEqual(got.payload.cursors[0].color, self.cur_b.color)
        self.assertEqual(got.payload.cursors[0].position, self.cur_b.position)
        self.assertEqual(got.payload.cursors[0].pointer, self.cur_b.pointer)

        # watcher 관계 확인
        a_watching = CursorHandler.get_watching("A")
        self.assertEqual(len(a_watching), 1)
        self.assertIn("B", a_watching)

        b_watchers = CursorHandler.get_watchers("B")
        self.assertEqual(len(b_watchers), 1)
        self.assertIn("A", b_watchers)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_set_view_size_same(self, mock: AsyncMock):
        message = Message(
            event=NewConnEvent.SET_VIEW_SIZE,
            header={"sender": self.cur_a.id},
            payload=SetViewSizePayload(
                width=self.cur_a.width,
                height=self.cur_a.height
            )
        )

        await CursorEventHandler.receive_set_view_size(message)

        mock.assert_not_called()

        # watcher 관계 확인
        a_watching = CursorHandler.get_watching("A")
        self.assertEqual(len(a_watching), 1)
        self.assertIn("C", a_watching)

        b_watchers = CursorHandler.get_watchers("B")
        self.assertEqual(len(b_watchers), 0)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_set_view_size_exceed_limit(self, mock: AsyncMock):
        message = Message(
            event=NewConnEvent.SET_VIEW_SIZE,
            header={"sender": self.cur_a.id},
            payload=SetViewSizePayload(
                width=VIEW_SIZE_LIMIT + 1,
                height=self.cur_a.height
            )
        )

        await CursorEventHandler.receive_set_view_size(message)

        mock.assert_called_once()

        # error
        got: Message[ErrorPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], ErrorEvent.ERROR)
        # target_conns 확인, [A]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn(self.cur_a.id, got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), ErrorPayload)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_set_view_size_0(self, mock: AsyncMock):
        message = Message(
            event=NewConnEvent.SET_VIEW_SIZE,
            header={"sender": self.cur_a.id},
            payload=SetViewSizePayload(
                width=0,
                height=self.cur_a.height
            )
        )

        await CursorEventHandler.receive_set_view_size(message)

        mock.assert_called_once()

        # error
        got: Message[ErrorPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], ErrorEvent.ERROR)
        # target_conns 확인, [A]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn(self.cur_a.id, got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), ErrorPayload)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_set_view_size_shrink(self, mock: AsyncMock):
        message = Message(
            event=NewConnEvent.SET_VIEW_SIZE,
            header={"sender": self.cur_b.id},
            payload=SetViewSizePayload(
                width=self.cur_b.width,
                height=self.cur_b.height-1
            )
        )

        await CursorEventHandler.receive_set_view_size(message)

        mock.assert_not_called()

        # watcher 관계 확인
        b_watching = CursorHandler.get_watching("B")
        self.assertEqual(len(b_watching), 1)
        self.assertIn("C", b_watching)

        a_watchers = CursorHandler.get_watchers("A")
        self.assertEqual(len(a_watchers), 0)


class CursorEventHandler_Chat_TestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        curs = setup_cursor_locations()
        self.cur_a = curs[0]
        self.cur_b = curs[1]
        self.cur_c = curs[2]

    def tearDown(self):
        CursorHandler.cursor_dict = {}
        CursorHandler.watchers = {}
        CursorHandler.watching = {}

    @patch("event.broker.EventBroker.publish")
    async def test_receive_send_chat(self, mock: AsyncMock):
        content = "test"

        message = Message(
            event=ChatEvent.SEND_CHAT,
            header={"sender": self.cur_a.id},
            payload=SendChatPayload(message=content)
        )

        await CursorEventHandler.receive_send_chat(message)

        self.assertEqual(len(mock.mock_calls), 1)

        # chat
        got: Message[ChatPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], ChatEvent.CHAT)
        # target_conns 확인, [A, B]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 2)
        self.assertIn(self.cur_a.id, got.header["target_conns"])
        self.assertIn(self.cur_b.id, got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), ChatPayload)
        self.assertEqual(got.payload.cursor_id, self.cur_a.id)
        self.assertEqual(got.payload.message, content)

    @patch("event.broker.EventBroker.publish")
    async def test_receive_send_chat_length_exceeded(self, mock: AsyncMock):
        content = "a" * (CHAT_MAX_LENGTH+1)

        message = Message(
            event=ChatEvent.SEND_CHAT,
            header={"sender": self.cur_a.id},
            payload=SendChatPayload(message=content)
        )

        await CursorEventHandler.receive_send_chat(message)

        self.assertEqual(len(mock.mock_calls), 1)

        # error
        got: Message[ErrorPayload] = mock.mock_calls[0].args[0]
        self.assertEqual(type(got), Message)
        self.assertEqual(got.event, "multicast")
        # origin_event
        self.assertIn("origin_event", got.header)
        self.assertEqual(got.header["origin_event"], ErrorEvent.ERROR)
        # target_conns 확인, [A]
        self.assertIn("target_conns", got.header)
        self.assertEqual(len(got.header["target_conns"]), 1)
        self.assertIn(self.cur_a.id, got.header["target_conns"])
        # payload 확인
        self.assertEqual(type(got.payload), ErrorPayload)


if __name__ == "__main__":
    unittest.main()
