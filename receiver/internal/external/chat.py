from event.broker import EventBroker
from event.message import Message
from event.payload import IdDataPayload

from data.conn.event import ServerEvent, ClientEvent

from handler.cursor import CursorHandler
from handler.conn import ConnectionEvent, ConnectionHandler


class ChatExternalReceiver():
    @EventBroker.add_receiver(ConnectionEvent.CHAT)
    @staticmethod
    async def chat(msg: Message[IdDataPayload[str, ClientEvent.Chat]]):
        cur_id = msg.payload.id
        content = msg.payload.data.message

        cursor = await CursorHandler.get(cur_id)

        watchers = await CursorHandler.get_watchers(cursor)

        external_event = ServerEvent.Chat(
            chats=[
                ServerEvent.Chat.Elem(
                    cursor_id=cur_id,
                    content=content
                )
            ]
        )

        await ConnectionHandler.multicast([c.id for c in watchers], external_event)
