from event.broker import EventBroker, publish_data_event
from event.message import Message
from event.payload import IdDataPayload

from data.cursor import Cursor
from data.score import Score
from data.board import Point, PointRange
from data.conn.event import ServerEvent, ClientEvent

from handler.cursor import CursorHandler
from handler.board import BoardEvent, BoardHandler
from handler.conn import ConnectionEvent, ConnectionHandler
from handler.score import ScoreHandler

from utils.config import Config


class OpenTileExternalReceiver():
    @EventBroker.add_receiver(ConnectionEvent.OPEN_TILE)
    @staticmethod
    async def open_tile(msg: Message[IdDataPayload[str, ClientEvent.OpenTile]]):
        cur_id = msg.payload.id
        tile_point = msg.payload.data.position

        tile = await BoardHandler.fetch_point(tile_point)

        if tile.is_open or tile.is_flag:
            return

        await BoardHandler.open_tiles(tile_point)

        if tile.is_mine:
            await publish_data_event(
                event=BoardEvent.EXPLOSION,
                data=tile,
                id=tile_point
            )
            return

        await ScoreHandler.increase(cur_id, Config.OPEN_TILE_SCORE)
