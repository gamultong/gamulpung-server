from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, SendChatPayload, ChatPayload, ErrorPayload
)

from data.cursor import Cursor


from receiver.internal.send_chat import (
    SendChatReceiver,
    validate_content, multicast_chat
)

from config import CHAT_MAX_LENGTH


from .test_tools import get_cur_set
from tests.utils import PathPatch

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call

patch = PathPatch("receiver.internal.send_chat")


class MulticastChat_TestCase(AsyncTestCase):
    @patch("multicast")
    async def test_multicast_chat(self, mock: AsyncMock):
        cur_a, cur_b, cur_c = get_cur_set(3)
        content = "ABC"

        await multicast_chat(
            target_conns=[cur_a, cur_b],
            sender=cur_c,
            content=content
        )

        mock.assert_called_once_with(
            target_conns=[cur_a.id, cur_b.id],
            message=Message(
                event=EventCollection.CHAT,
                payload=ChatPayload(
                    cursor_id=cur_c.id,
                    message=content
                )
            )
        )


class ValidateContent_TestCase(TestCase):
    def test_normal(self):
        content = "A" * CHAT_MAX_LENGTH
        result = validate_content(content=content)
        self.assertIsNone(result)

    def test_length_limit(self):
        content = "A" * (CHAT_MAX_LENGTH+1)
        result = validate_content(content=content)

        self.assertEqual(
            result,
            Message(
                event=EventCollection.ERROR,
                payload=ErrorPayload(msg=f"chat length limit exceeded. max length: {CHAT_MAX_LENGTH}")
            )
        )


cursor_a = Cursor.create("A")
cursors = get_cur_set(3)


def mock_send_chat_receiver_dependency(func):
    func = patch("CursorHandler.get_cursor", return_value=cursor_a)(func)
    func = patch("validate_content", return_value=None)(func)
    func = patch("get_watchers", return_value=cursors)(func)
    func = patch("multicast_chat")(func)
    func = patch("multicast")(func)

    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


class SendChatReceiver_TestCase(AsyncTestCase):
    def setUp(self):
        self.content = "ABC"
        self.input_message = Message(
            event=EventCollection.SEND_CHAT,
            header={"sender": cursor_a.id},
            payload=SendChatPayload(message=self.content)
        )

    @mock_send_chat_receiver_dependency
    async def test_normal(
            self,
            get_cursor: MagicMock,
            validate_content: MagicMock,
            get_watchers: MagicMock,
            multicast_chat: AsyncMock,
            multicast: AsyncMock,
    ):

        await SendChatReceiver.receive_send_chat(self.input_message)

        multicast_chat.assert_called_once_with(
            target_conns=[cursor_a] + cursors,
            sender=cursor_a,
            content=self.content
        )

        multicast.assert_not_called()

    @mock_send_chat_receiver_dependency
    async def test_validation_failed(
            self,
            get_cursor: MagicMock,
            validate_content: MagicMock,
            get_watchers: MagicMock,
            multicast_chat: AsyncMock,
            multicast: AsyncMock,
    ):
        error_msg = Message(event=EventCollection.ERROR, payload=None)
        validate_content.return_value = error_msg

        await SendChatReceiver.receive_send_chat(self.input_message)

        multicast.assert_called_once_with(
            target_conns=[cursor_a.id],
            message=error_msg
        )

        multicast_chat.assert_not_called()
