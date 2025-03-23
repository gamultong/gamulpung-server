from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, SendChatPayload, ChatPayload, ErrorPayload
)

from handler.cursor import CursorHandler

from data.cursor import Cursor

from config import CHAT_MAX_LENGTH

from .utils import multicast, get_watchers


class SendChatReceiver:
    @EventBroker.add_receiver(EventCollection.SEND_CHAT)
    @staticmethod
    async def receive_send_chat(message: Message[SendChatPayload]):
        cursor = CursorHandler.get_cursor(message.header["sender"])

        content = message.payload.message

        if (msg := validate_content(content)):
            await multicast(target_conns=[cursor.id], message=msg)
            return

        watchers = get_watchers(cursor)

        await multicast_chat(
            target_conns=[cursor] + watchers,
            sender=cursor,
            content=content
        )


def validate_content(content: str) -> Message:
    if len(content) > CHAT_MAX_LENGTH:
        # 채팅 길이 제한 넘김
        return Message(
            event=EventCollection.ERROR,
            payload=ErrorPayload(msg=f"chat length limit exceeded. max length: {CHAT_MAX_LENGTH}")
        )

    return


async def multicast_chat(target_conns: list[Cursor], sender: Cursor, content: str):
    await multicast(
        target_conns=[c.id for c in target_conns],
        message=Message(
            event=EventCollection.CHAT,
            payload=ChatPayload(
                cursor_id=sender.id,
                message=content
            )
        )
    )
