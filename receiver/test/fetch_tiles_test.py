from event.message import Message

from data.board import Point, Tiles, Tile
from data.payload import (
    EventCollection, ErrorPayload,
    FetchTilesPayload, TilesPayload
)
from config import VIEW_SIZE_LIMIT

from receiver.internal.fetch_tiles import (
    FetchTilesReceiver,
    validate_fetch_range
)

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import patch, AsyncMock, MagicMock

from .test_tools import assertMulticast


class ValidateFetchRange_TestCase(TestCase):
    def test_normal(self):
        start = Point(x=0, y=0)
        end = Point(x=1, y=-1)

        result = validate_fetch_range(start=start, end=end)

        self.assertIsNone(result)

    def test_range_limit_exceeded(self):
        start = Point(x=0, y=0)
        end = Point(x=VIEW_SIZE_LIMIT, y=-VIEW_SIZE_LIMIT)

        result = validate_fetch_range(start=start, end=end)

        self.assertEqual(
            result,
            Message(
                event=EventCollection.ERROR,
                payload=ErrorPayload(msg=f"fetch gap should not be more than {VIEW_SIZE_LIMIT}")
            )
        )

    def test_check_left_top_and_right_bottom(self):
        start = Point(x=1, y=-1)
        end = Point(x=0, y=0)

        result = validate_fetch_range(start=start, end=end)

        self.assertEqual(
            result,
            Message(
                event=EventCollection.ERROR,
                payload=ErrorPayload(msg="start_p should be left-top, and end_p should be right-bottom")
            )
        )

def mock_fetch_tiles_receiver_dependency(func):
    func = patch("receiver.internal.fetch_tiles.multicast")(func)
    func = patch("receiver.internal.fetch_tiles.fetch_tiles")(func)
    func = patch("receiver.internal.fetch_tiles.validate_fetch_range")(func)

    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


class FetchTilesReceiver_TestCase(AsyncTestCase):
    @mock_fetch_tiles_receiver_dependency
    async def test_normal(
        self,
        multicast: AsyncMock,
        fetch_tiles: AsyncMock,
        validate_fetch_range: MagicMock
    ):
        # arg
        start = Point(0, 0)
        end = Point(1, -1)
        sender = "example"
        # expect
        expected_tiles_str = "abcdef"

        # mock
        tiles_mock = MagicMock(Tiles)
        tiles_mock.to_str.return_value = expected_tiles_str
        validate_fetch_range.return_value = None
        fetch_tiles.return_value = tiles_mock

        # call
        await FetchTilesReceiver.receive_fetch_tiles(Message(
            event=EventCollection.FETCH_TILES,
            header={"sender": sender},
            payload=FetchTilesPayload(
                start_p=start,
                end_p=end
            )
        ))

        # assert
        validate_fetch_range.assert_called_once_with(start, end)
        fetch_tiles.assert_awaited_once_with(start, end)

        multicast.assert_awaited_once()
        assertMulticast(
            self=self, call=multicast.mock_calls[0],
            target_conns=[sender],
            message=Message(
                event=EventCollection.TILES,
                payload=TilesPayload(
                    start_p=start,
                    end_p=end,
                    tiles=expected_tiles_str
                )
            )
        )

    @mock_fetch_tiles_receiver_dependency
    async def test_invalid_fetch_range(
        self,
        multicast: AsyncMock,
        fetch_tiles: AsyncMock,
        validate_fetch_range: MagicMock
    ):
        # arg
        start = Point(1, 0)
        end = Point(0, 0)
        sender = "example"
        # expect
        error_msg = Message(
            event=EventCollection.ERROR,
            payload=ErrorPayload(msg="example message")
        )

        # mock
        validate_fetch_range.return_value = error_msg

        # call
        await FetchTilesReceiver.receive_fetch_tiles(Message(
            event=EventCollection.FETCH_TILES,
            header={"sender": sender},
            payload=FetchTilesPayload(
                start_p=start,
                end_p=end
            )
        ))

        # assert
        validate_fetch_range.assert_called_once_with(start, end)

        multicast.assert_awaited_once()
        assertMulticast(
            self=self, call=multicast.mock_calls[0],
            target_conns=[sender],
            message=error_msg
        )

        fetch_tiles.assert_not_called()
