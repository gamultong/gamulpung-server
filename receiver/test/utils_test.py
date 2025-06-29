from event.message import Message
from data.cursor import Cursor
from data.board import Point, Tiles
from data.score import Score
from data.payload import DataPayload

from receiver.internal.utils import (
    multicast, broadcast
)

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import patch, AsyncMock, MagicMock, call

from tests.utils import PathPatch

patch = PathPatch("receiver.internal.utils")


class Multicast_TestCase(AsyncTestCase):
    async def test_normal(self):
        # TODO: 다시짜기
        pass
        # target_conns = ["a", "b", "c"]
        # message = Message(
        #     event="example_event",
        #     payload="example_payload"
        # )

        # await multicast(target_conns=target_conns, message=message)

        # publish_mock.assert_called_once()
        # got: Message = publish_mock.mock_calls[0].kwargs["message"]
        # self.assertEqual(
        #     got,
        #     Message(
        #         event="multicast",
        #         header={
        #             "target_conns": target_conns,
        #             "origin_event": message.event
        #         },
        #         payload=message.payload
        #     )
        # )

    async def test_no_target_conns(self):
        # TODO: 다시짜기
        pass
        # target_conns = []
        # message = Message(
        #     event="example_event",
        #     payload="example_payload"
        # )

        # await multicast(target_conns=target_conns, message=message)

        # publish_mock.assert_not_called()
