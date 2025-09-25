from event.broker import EventBroker
from handler.board import BoardHandler, BoardEvent
from data.conn.event import ServerEvent
from handler.cursor import CursorHandler
from handler.conn import ConnectionHandler
from event.message import Message
from event.payload import IdDataPayload
from data.board import Tile, Point, PointRange
from utils.config import Config

EXPLOSION_RANGE = 1

"""
1. 터진 타일 근처 커서 죽이기
2. explosion(external_event)를 multicast -> 이 폭발 범위을 바라보고 있는 애들(팔발 애니메가 재생된다는 가정)
"""


def get_explosion_range(point: Point):
    x = point.x
    y = point.y
    return PointRange(
        Point(x-EXPLOSION_RANGE, y+EXPLOSION_RANGE),
        Point(x+EXPLOSION_RANGE, y-EXPLOSION_RANGE)
    )


class ExplosionReceiver:
    @EventBroker.add_receiver(BoardEvent.EXPLOSION)
    @staticmethod
    async def r(msg: Message[IdDataPayload[Point, Tile]]):
        position = msg.payload.id

        explosion_range = get_explosion_range(position)

        cursor_list = await CursorHandler.get_by_range(explosion_range)

        for cursor in cursor_list:
            await CursorHandler.kill(cursor.id, Config.MINE_KILL_DURATION_SECONDS)

        watching_cursor_list = await CursorHandler.get_by_watching_range(explosion_range)
        watching_cursor_id_list = [cursor.id for cursor in watching_cursor_list]

        external_event = ServerEvent.Explosion(
            position=position
        )

        await ConnectionHandler.multicast(watching_cursor_id_list, external_event)
