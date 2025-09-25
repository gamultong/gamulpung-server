from event.broker import EventBroker
from handler.board import BoardEvent
from data.conn.event import ServerEvent
from handler.cursor import CursorHandler
from handler.conn import ConnectionHandler
from event.message import Message
from event.payload import IdDataPayload
from data.board import PointRange, Tiles


class NotifyBoardChangedReceiver:
    @EventBroker.add_receiver(BoardEvent.UPDATE)
    @staticmethod
    async def r(msg: Message[IdDataPayload[PointRange, Tiles]]):
        range = msg.payload.id
        tiles = msg.payload.data

        watching_cursor_list = await CursorHandler.get_by_watching_range(range)
        watching_cursor_id_list = [cursor.id for cursor in watching_cursor_list]

        external_event = ServerEvent.TilesState(
            tiles=[
                ServerEvent.TilesState.Elem(
                    range=range,
                    data=tiles.to_str()
                )
            ]
        )

        await ConnectionHandler.multicast(watching_cursor_id_list, external_event)
