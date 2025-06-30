from event.broker import EventBroker
from event.message import Message

from data.payload import DataPayload
from data.cursor import Cursor
from data.conn.event import ServerEvent

from handler.cursor import CursorEvent
from handler.score import ScoreHandler

from .utils import multicast


class CursorReceiver():
    @EventBroker.add_receiver(CursorEvent.CREATED)
    @staticmethod
    async def cursor_created(message: Message[DataPayload[Cursor]]):
        cursor = message.payload.data
        assert cursor is not None

        await ScoreHandler.create(id=cursor.id)

        await multicast_my_cursor(cursor)


async def multicast_my_cursor(cursor: Cursor):
    event = ServerEvent.MyCursor(id=cursor.id)

    await multicast(target_conns=[cursor.conn_id], event=event)
