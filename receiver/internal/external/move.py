from event.broker import EventBroker
from event.message import Message
from event.payload import IdDataPayload

from data.conn.event import ClientEvent

from handler.cursor import CursorHandler
from handler.conn import ConnectionEvent
from handler.score import ScoreHandler

from utils.config import Config


class MoveExternalReceiver():
    @EventBroker.add_receiver(ConnectionEvent.MOVE)
    @staticmethod
    async def move(msg: Message[IdDataPayload[str, ClientEvent.Move]]):
        cur_id = msg.payload.id
        move_point = msg.payload.data.position

        cursor = await CursorHandler.get(cur_id)

        await CursorHandler.move(cur_id, move_point)

        await ScoreHandler.increase(cursor.id, Config.MOVE_SCORE)
