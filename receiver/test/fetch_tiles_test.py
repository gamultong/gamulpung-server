from event.message import Message

from data.board import Point
from data.payload import EventEnum, ErrorPayload

from config import VIEW_SIZE_LIMIT

from receiver.internal.fetch_tiles import validate_fetch_range

import unittest
from .utils import assertMessageEqual


class ValidateFetchRange_TestCase(unittest.TestCase):
    def test_normal(self):
        start = Point(x=0, y=0)
        end = Point(x=1, y=-1)

        result = validate_fetch_range(start=start, end=end)

        self.assertIsNone(result)

    def test_range_limit_exceeded(self):
        start = Point(x=0, y=0)
        end = Point(x=VIEW_SIZE_LIMIT, y=-VIEW_SIZE_LIMIT)

        result = validate_fetch_range(start=start, end=end)

        assertMessageEqual(
            self, result,
            Message(
                event=EventEnum.ERROR,
                payload=ErrorPayload(msg=f"fetch gap should not be more than {VIEW_SIZE_LIMIT}")
            )
        )

    def test_check_left_top_and_right_bottom(self):
        start = Point(x=1, y=-1)
        end = Point(x=0, y=0)

        result = validate_fetch_range(start=start, end=end)

        assertMessageEqual(
            self, result,
            Message(
                event=EventEnum.ERROR,
                payload=ErrorPayload(msg="start_p should be left-top, and end_p should be right-bottom")
            )
        )
