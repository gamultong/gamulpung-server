import unittest

from event import EventRecorder

from message import Message
from message.payload import ErrorEvent, ErrorPayload
from .utils import clear_records

from datetime import datetime


class EventRecorderTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await clear_records()

    async def asyncTearDown(self):
        await clear_records()

    async def test_record(self):
        message = Message(
            event=ErrorEvent.ERROR,
            header={
                "ayo": "pizza here",
                "thisisint": 1
            },
            payload=ErrorPayload(msg="heelo world")
        )

        timestamp = datetime.now()

        await EventRecorder.record(timestamp, message)


if __name__ == "__main__":
    unittest.main()
