from event.broker import EventBroker
from event.message import Message
from event.payload import IdDataPayload

from data.cursor import Cursor
from data.score import Score
from data.board import Point, PointRange
from data.conn.event import ServerEvent, ClientEvent

from handler.cursor import CursorHandler
from handler.board import BoardHandler
from handler.conn import ConnectionEvent, ConnectionHandler
from handler.score import ScoreHandler

from utils.config import Config


class SetFlagExternalReceiver():
    @EventBroker.add_receiver(ConnectionEvent.SET_FLAG)
    @staticmethod
    async def set_flag(msg: Message[IdDataPayload[str, ClientEvent.SetFlag]]):
        cur_id = msg.payload.id
        tile_point = msg.payload.data.position

        tile = await BoardHandler.fetch_point(tile_point)

        if tile.is_open:
            return

        await BoardHandler.togle_flag(tile_point)

        if tile.is_flag:
            await ScoreHandler.increase(cur_id, Config.SET_FLAG_SCORE)
        else:
            await ScoreHandler.increase(cur_id, Config.CLEAR_FLAG_SCORE)
