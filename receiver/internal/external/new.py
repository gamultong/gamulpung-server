from event.broker import EventBroker
from event.message import Message
from event.payload import DataPayload

from data.cursor import Cursor
from data.score import Score
from data.board import Point
from data.conn.event import ServerEvent

from handler.cursor import CursorHandler
# from handler.board import BoardHandler
from handler.conn import Conn, CursorEvent

from ..utils import multicast


# 내가 생각하는 흐름은:
# 1. position = get_random_open_position (현재 없으니 mocking) -> BoardHandler
# 2. cursor = Cursor.Create(position=position)
# 3. CursorHAndelr.Set(cursor) -> CursorHandler

class NewExternalReceiver():
    @EventBroker.add_receiver(CursorEvent.JOIN)
    @staticmethod
    async def new(message: Message[DataPayload]):
        conn_id = message.payload.id
        cursor = Cursor.create(conn_id=conn_id)

        position = await get_random_open_position()
        cursor.position = position

        await CursorHandler.create(template=cursor)


async def get_random_open_position() -> Point:
    return Point(1, 1)
