from event.broker import EventBroker
from event.message import Message
from event.payload import IdDataPayload

from data.board import Point, PointRange, Tiles, Tile
from data.conn.event import ClientEvent

from handler.cursor import CursorHandler, CursorEvent
from handler.board import BoardHandler
from handler.conn import ConnectionEvent


def get_interaction_range(point: Point):
    x = point.x
    y = point.y
    return PointRange(
        Point(x-1, y+1),
        Point(x+1, y-1)
    )


def is_interactable_board(tiles: Tiles):
    for tile_data in tiles.data:
        tile = Tile.from_int(tile_data)
        if tile.is_open:
            return True
    return False


class PointingExternalReceiver():
    @EventBroker.add_receiver(ConnectionEvent.POINTING)
    @staticmethod
    async def pointing(msg: Message[IdDataPayload[str, ClientEvent.Pointing]]):
        cur_id = msg.payload.id
        click_point = msg.payload.data.position

        interaction_range = get_interaction_range(click_point)

        interaction_board = await BoardHandler.fetch(interaction_range)

        if not is_interactable_board(interaction_board):
            return

        await CursorHandler.set_pointer(cur_id, click_point)
