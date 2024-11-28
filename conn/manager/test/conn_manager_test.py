import unittest
import uuid

from unittest.mock import MagicMock, AsyncMock, patch
from conn import Conn
from conn.manager import ConnectionManager
from message import Message
from message.payload import TilesPayload, NewConnEvent, NewConnPayload
from event import EventBroker
from conn.test.fixtures import create_connection_mock
from board import Point


class ConnectionManagerTestCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.con1 = create_connection_mock()
        self.con2 = create_connection_mock()
        self.con3 = create_connection_mock()
        self.con4 = create_connection_mock()

    @patch("event.EventBroker.publish")
    async def test_add(self, mock: AsyncMock):

        width = 1
        height = 1

        con_obj = await ConnectionManager.add(self.con1, width, height)
        self.assertEqual(type(con_obj), Conn)

        self.assertEqual(ConnectionManager.get_conn(con_obj.id).id, con_obj.id)

        mock.assert_called_once()
        got: Message[NewConnPayload] = mock.mock_calls[0].args[0]

        self.assertEqual(type(got), Message)
        self.assertEqual(type(got.payload), NewConnPayload)
        self.assertEqual(got.payload.conn_id, con_obj.id)
        self.assertEqual(got.payload.width, width)
        self.assertEqual(got.payload.height, height)

    def test_get_conn(self):
        valid_id = "abc"
        invalid_id = "abcdef"
        ConnectionManager.conns[valid_id] = Conn(valid_id, create_connection_mock())

        self.assertIsNotNone(ConnectionManager.get_conn(valid_id))
        self.assertIsNone(ConnectionManager.get_conn(invalid_id))

    @patch("event.EventBroker.publish")
    async def test_generate_conn_id(self, mock: AsyncMock):
        n_conns = 5

        conns = [create_connection_mock() for _ in range(n_conns)]
        conn_ids = [None] * n_conns

        for idx, conn in enumerate(conns):
            conn_obj = await ConnectionManager.add(conn=conn, width=1, height=1)
            conn_ids[idx] = conn_obj.id

        for id in conn_ids:
            self.assertEqual(conn_ids.count(id), 1)
            # UUID 포맷인지 확인. 아니면 ValueError
            uuid.UUID(id)

    @patch("event.EventBroker.publish")
    async def test_receive_broadcast_event(self, mock: AsyncMock):
        _ = await ConnectionManager.add(self.con1, 1, 1)
        _ = await ConnectionManager.add(self.con2, 1, 1)
        _ = await ConnectionManager.add(self.con3, 1, 1)
        _ = await ConnectionManager.add(self.con4, 1, 1)

        origin_event = "ayo"

        message = Message(event="broadcast", header={"origin_event": origin_event}, payload=None)

        await ConnectionManager.receive_broadcast_event(message)

        self.con1.send_text.assert_called_once()
        self.con2.send_text.assert_called_once()
        self.con3.send_text.assert_called_once()
        self.con4.send_text.assert_called_once()

        expected = Message(event=origin_event, payload=None)

        got1: str = self.con1.send_text.mock_calls[0].args[0]
        got2: str = self.con2.send_text.mock_calls[0].args[0]
        got3: str = self.con3.send_text.mock_calls[0].args[0]
        got4: str = self.con4.send_text.mock_calls[0].args[0]

        self.assertEqual(expected.to_str(), got1)
        self.assertEqual(expected.to_str(), got2)
        self.assertEqual(expected.to_str(), got3)
        self.assertEqual(expected.to_str(), got4)

    @patch("event.EventBroker.publish")
    async def test_receive_multicast_event(self, mock: AsyncMock):
        con1 = await ConnectionManager.add(self.con1, 1, 1)
        con2 = await ConnectionManager.add(self.con2, 1, 1)
        _ = await ConnectionManager.add(self.con3, 1, 1)
        _ = await ConnectionManager.add(self.con4, 1, 1)

        origin_event = "ayo"

        message = Message(
            event="multicast",
            header={
                "target_conns": [con1.id, con2.id],
                "origin_event": origin_event
            },
            payload=None
        )

        expected = Message(event=origin_event, payload=None)

        await ConnectionManager.receive_multicast_event(message)

        self.con1.send_text.assert_called_once()
        self.con2.send_text.assert_called_once()
        self.con3.send_text.assert_not_called()
        self.con4.send_text.assert_not_called()

        got1: str = self.con1.send_text.mock_calls[0].args[0]
        got2: str = self.con1.send_text.mock_calls[0].args[0]

        self.assertEqual(expected.to_str(), got1)
        self.assertEqual(expected.to_str(), got2)

    async def test_handle_message(self):
        mock = AsyncMock()
        EventBroker.add_receiver("example")(mock)

        conn_id = "haha this is some random conn id"
        message = Message(event="example",
                          header={"sender": conn_id},
                          payload=TilesPayload(
                              Point(0, 0), Point(0, 0), "abcdefg"
                          ))

        await ConnectionManager.handle_message(message=message)

        mock.assert_called_once()

        got: Message[TilesPayload] = mock.mock_calls[0].args[0]

        self.assertEqual(got.header["sender"], conn_id)
        self.assertEqual(got.to_str(), message.to_str())


if __name__ == "__main__":
    unittest.main()
