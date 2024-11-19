import unittest
from unittest.mock import MagicMock

from message import Message
from event import EventBroker, Receiver, NoMatchingReceiverException

class EventBrokerTestCase(unittest.TestCase):

    def setUp(self):
        self.handler = MagicMock()
        self.func_receive_a = MagicMock()
        self.func_receive_b = MagicMock()
        
        self.func_receive_a = EventBroker.add_receiver("example_a")(self.func_receive_a)
        self.func_receive_b = EventBroker.add_receiver("example_b")(self.handler.receive_b)
        
        self.handler.receive_a = self.func_receive_a
        self.handler.receive_b = self.func_receive_b


    def tearDown(self):
        EventBroker.remove_receiver(self.handler.receive_a)
        EventBroker.remove_receiver(self.handler.receive_b)
                
    def test_add_receiver(self):
        assert self.handler.receive_a.id in Receiver.receiver_dict


    def test_remove_receiver(self):
        assert self.handler.receive_a.id in Receiver.receiver_dict
        assert "example_a" in EventBroker.event_dict
        assert EventBroker.event_dict["example_a"].count(self.handler.receive_a.id) == 1

        EventBroker.remove_receiver(self.handler.receive_a)

        assert self.handler.receive_a.id not in Receiver.receiver_dict
        assert "example_a" not in EventBroker.event_dict
        
    def test_publish(self):
        message = Message(event="example_a", payload=None)
        
        EventBroker.publish(message=message)

        assert len(self.handler.receive_a.func.mock_calls) == 1
        mock_message = self.handler.receive_a.func.mock_calls[0].args[0]               
        assert mock_message.event == message.event
        assert mock_message.payload == message.payload

    def test_publish_no_receiver(self):
        message = Message(event="invaild_event", payload=None)

        with self.assertRaises(NoMatchingReceiverException) as cm:
            EventBroker.publish(message=message)
        self.assertEqual(cm.exception.msg, "no matching receiver for 'invaild_event'")

if __name__ == "__main__":
    unittest.main()