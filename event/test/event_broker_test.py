import unittest
from unittest.mock import MagicMock, AsyncMock, patch

from message import Message
from event import EventBroker, Receiver, NoMatchingReceiverException
from .utils import clear_records


class EventBrokerTestCase(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.handler = MagicMock()
        self.func_receive_a = AsyncMock()
        self.func_receive_b = AsyncMock()

        self.func_receive_a = EventBroker.add_receiver("example_a")(self.func_receive_a)
        self.func_receive_b = EventBroker.add_receiver("example_b")(self.func_receive_b)
        self.func_receive_b = EventBroker.add_receiver("example_c")(self.func_receive_b)

        self.handler.receive_a = self.func_receive_a
        self.handler.receive_b = self.func_receive_b

    async def asyncTearDown(self):
        await clear_records()
        EventBroker.remove_receiver(self.handler.receive_a)
        EventBroker.remove_receiver(self.handler.receive_b)

    def test_add_receiver(self):
        self.assertIn(self.handler.receive_a.id, Receiver.receiver_dict)

    def test_remove_receiver(self):
        self.assertIn(self.handler.receive_a.id, Receiver.receiver_dict)
        self.assertIn("example_a", EventBroker.event_dict)
        self.assertEqual(EventBroker.event_dict["example_a"].count(self.handler.receive_a.id), 1)

        EventBroker.remove_receiver(self.handler.receive_a)

        self.assertNotIn(self.handler.receive_a.id, Receiver.receiver_dict)
        self.assertNotIn("example_a", EventBroker.event_dict)

    @patch("event.EventRecorder.record")
    async def test_publish(self, mock: AsyncMock):
        message = Message(event="example_a", payload=None)

        await EventBroker.publish(message=message)

        self.handler.receive_a.func.assert_called_once()
        mock_message = self.handler.receive_a.func.mock_calls[0].args[0]
        self.assertEqual(mock_message.event, message.event)

    @patch("event.EventRecorder.record")
    async def test_multiple_receiver_publish(self, mock: AsyncMock):
        message_b = Message(event="example_b", payload=None)
        await EventBroker.publish(message=message_b)

        message_c = Message(event="example_c", payload=None)
        await EventBroker.publish(message=message_c)

        self.assertEqual(len(self.handler.receive_b.func.mock_calls), 2)

        mock_message_b = self.handler.receive_b.func.mock_calls[0].args[0]
        self.assertEqual(mock_message_b.event, message_b.event)

        mock_message_c = self.handler.receive_b.func.mock_calls[1].args[0]
        self.assertEqual(mock_message_c.event, message_c.event)

    async def test_publish_no_receiver(self):
        message = Message(event="invaild_event", payload=None)

        with self.assertRaises(NoMatchingReceiverException) as cm:
            await EventBroker.publish(message=message)
        self.assertEqual(cm.exception.__str__(), "no matching receiver for 'invaild_event'")


if __name__ == "__main__":
    unittest.main()
