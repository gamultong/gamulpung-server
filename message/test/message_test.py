from message import Message, InvalidEventTypeException
from message.payload import Payload, FetchTilesPayload, TilesPayload
from .message_testdata import FETCH_TILES_EXAMPLE, INVALID_EVENT_EXAMPLE, TILES_EXAMPLE
from board.data import Point

import unittest
import json


class MessageTestCase(unittest.TestCase):
    def test_fetch_tiles_from_str(self):
        socket_msg = FETCH_TILES_EXAMPLE
        message: Message[FetchTilesPayload] = Message.from_str(socket_msg)

        self.assertEqual(message.event, "fetch-tiles")
        self.assertTrue(issubclass(type(message.payload), Payload))
        self.assertEqual(message.payload.start_p.x, 0)
        self.assertEqual(message.payload.start_p.y, 0)
        self.assertEqual(message.payload.end_p.x, 0)
        self.assertEqual(message.payload.end_p.y, 0)

    def test_fetch_tiles_to_str(self):
        message: Message[FetchTilesPayload] = Message(
            event="fetch-tiles",
            payload=FetchTilesPayload(
                start_p=Point(0, 0),
                end_p=Point(0, 0)
            )
        )

        msg_str = message.to_str()

        self.assertEqual(json.loads(msg_str), json.loads(FETCH_TILES_EXAMPLE))

    def test_tiles_from_str(self):
        socket_msg = TILES_EXAMPLE
        message: Message[TilesPayload] = Message.from_str(socket_msg)

        self.assertEqual(message.event, "tiles")
        self.assertTrue(issubclass(type(message.payload), Payload))
        self.assertEqual(message.payload.start_p.x, 0)
        self.assertEqual(message.payload.start_p.y, 0)
        self.assertEqual(message.payload.end_p.x, 4)
        self.assertEqual(message.payload.end_p.y, 4)
        self.assertEqual(message.payload.tiles, "CCCCCCCCCCC111CC1F1CC111C")

    def test_tiles_to_str(self):
        message: Message[TilesPayload] = Message(
            event="tiles",
            payload=TilesPayload(
                start_p=Point(0, 0),
                end_p=Point(4, 4),
                tiles="CCCCCCCCCCC111CC1F1CC111C"
            )
        )

        msg_str = message.to_str()

        self.assertEqual(json.loads(msg_str), json.loads(TILES_EXAMPLE))

    def test_from_str_invalid_event(self):
        socket_msg = INVALID_EVENT_EXAMPLE

        with self.assertRaises(InvalidEventTypeException) as cm:
            Message.from_str(socket_msg)

        self.assertEqual(cm.exception.__str__(), "invalid event type: 'ayo invalid'")


if __name__ == "__main__":
    unittest.main()
