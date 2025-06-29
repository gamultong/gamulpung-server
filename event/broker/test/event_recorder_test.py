# from datetime import datetime
# from .utils import clear_records
# from data.payload import EventCollection, ErrorPayload
# from event.message import Message
# import unittest

# from event.broker import EventRecorder


# class EventRecorderTestCase(unittest.IsolatedAsyncioTestCase):
#     async def asyncSetUp(self):
#         await clear_records()

#     async def asyncTearDown(self):
#         await clear_records()

#     async def test_record(self):
#         message = Message(
#             event=EventCollection.ERROR,
#             header={
#                 "ayo": "pizza here",
#                 "thisisint": 1
#             },
#             payload=ErrorPayload(msg="heelo world")
#         )

#         timestamp = datetime.now()

#         await EventRecorder.record(timestamp, message)


# if __name__ == "__main__":
#     unittest.main()
