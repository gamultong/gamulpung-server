from event.broker import EventBroker
from event.message import Message
from event.payload import IdPayload

from handler.cursor import CursorHandler
from handler.conn import ConnectionEvent


class QuitExternalReceiver():
    @EventBroker.add_receiver(ConnectionEvent.QUIT)
    @staticmethod
    async def quit(message: Message[IdPayload[str]]):
        cur_id = message.payload.id

        await CursorHandler.delete(cur_id)
