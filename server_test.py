from unittest.mock import AsyncMock, patch
import unittest
from conn.manager import ConnectionManager
from event.broker.test.utils import clear_records
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from server import app
from event.message import Message
from event.payload import FetchTilesPayload, TilesPayload, TilesEvent, NewConnEvent
from board.data.storage.test.fixtures import setup_board, teardown_board
from board.event.handler import BoardEventHandler
from data_layer.board import Point, Tile, Tiles
from event.broker import EventBroker


class ServerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await setup_board()
        self.client = TestClient(app)

    async def asyncTearDown(self):
        await teardown_board()
        await clear_records()
        self.client.params = {}
        self.client.close()

    def test_no_params(self):
        with self.assertRaises(WebSocketDisconnect) as cm:
            with self.client.websocket_connect("/session") as websocket:
                websocket.close()

    def test_wrong_params(self):
        with self.assertRaises(WebSocketDisconnect) as cm:
            with self.client.websocket_connect("/session?view_width=hello") as websocket:
                websocket.close()

    @patch("event.broker.EventBroker.publish")
    def test_fetch_tiles(self, mock: AsyncMock):
        async def filter_tiles_event(message: Message):
            match (message.event):
                case "multicast":
                    await ConnectionManager.receive_multicast_event(message)
                case TilesEvent.FETCH_TILES:
                    await BoardEventHandler.receive_fetch_tiles(message)

        mock.side_effect = filter_tiles_event

        with self.client.websocket_connect("/session", **{"params": {"view_width": 1, "view_height": 1}}) as websocket:
            msg = Message(
                event=TilesEvent.FETCH_TILES,
                payload=FetchTilesPayload(
                    start_p=Point(-2, 1),
                    end_p=Point(1, -2)
                )
            )

            expect = Message(
                event=TilesEvent.TILES,
                payload=TilesPayload(
                    start_p=Point(-2, 1),
                    end_p=Point(1, -2),
                    tiles="82818130818081008281813883280000"
                )
            )

            websocket.send_text(msg.to_str())

            response = websocket.receive_text()
            self.assertEqual(response, expect.to_str())


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        from db import db
        import asyncio
        asyncio.run(db.close())
