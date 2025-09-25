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


class SetWindowSizeExternalReceiver():
    @EventBroker.add_receiver(ConnectionEvent.SET_WINDOW_SIZE)
    @staticmethod
    async def set_window_size(msg: Message[IdDataPayload[str, ClientEvent.SetWindowSize]]):
        cur_id = msg.payload.id
        width = msg.payload.data.width
        height = msg.payload.data.height

        await CursorHandler.set_window_size(cur_id, width, height)
