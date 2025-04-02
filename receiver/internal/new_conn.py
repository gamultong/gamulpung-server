from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, NewConnPayload,
    MyCursorPayload, TilesPayload
)

from handler.board import BoardHandler
from handler.cursor import CursorHandler
from handler.score import ScoreHandler


from data.board import Point, Tiles
from data.cursor import Cursor

from .utils import (
    multicast, watch, get_view_range_points, publish_new_cursors, fetch_tiles
)

# 1. 커서 포지션 선정
# 2. 커서 만든 후 보내기
# 3. 커서간 연관관계 설정 후 보내기
# 4. 타일 보내기


class NewConnReceiver():
    @EventBroker.add_receiver(EventCollection.NEW_CONN)
    @staticmethod
    async def receive_new_conn(message: Message[NewConnPayload]):
        cursor = await new_cursor(
            message.payload.conn_id, 
            message.payload.width, 
            message.payload.height
        )

        start, end = get_view_range_points(cursor.position, cursor.width, cursor.height)

        await multicast_my_cursor(target_conns=[cursor],cursor=cursor)

        cursors_in_view = fetch_cursors_in_view(cursor)
        if len(cursors_in_view) > 0:
            watch(watchers=[cursor], watchings=cursors_in_view)

            await publish_new_cursors(
                target_cursors=[cursor],
                cursors=cursors_in_view
            )

        cursors_with_view_including = fetch_with_view_including(cursor)
        if len(cursors_with_view_including) > 0:
            watch(watchers=cursors_with_view_including, watchings=[cursor])

            await publish_new_cursors(
                target_cursors=cursors_with_view_including,
                cursors=[cursor]
            )

        tiles = await fetch_tiles(start, end)
        
        await multicast_tiles(
            target_conns=[cursor], 
            start=start, end=end, tiles=tiles
        )



async def new_cursor(conn_id: str, width: int, height: int):
    position = await BoardHandler.get_random_open_position()

    cursor = CursorHandler.create_cursor(
        conn_id=conn_id,
        position=position,
        width=width, 
        height=height
    )

    await ScoreHandler.create(cursor.id)

    return cursor


def fetch_with_view_including(cursor: Cursor) -> list[Cursor]:
    cursors_in_view = CursorHandler.view_includes_point(cursor.position, exclude_ids=[cursor.id])

    return cursors_in_view


def fetch_cursors_in_view(cursor: Cursor) -> list[Cursor]:
    start, end = get_view_range_points(cursor.position, cursor.width, cursor.height)

    cursors_in_view = CursorHandler.exists_range(start=start, end=end, exclude_ids=[cursor.id])

    return cursors_in_view


async def multicast_my_cursor(target_conns: list[Cursor], cursor: Cursor):
    await multicast(
        target_conns=[cursor.id for cursor in target_conns],
        message=Message(
            event=EventCollection.MY_CURSOR,
            payload=MyCursorPayload(
                id=cursor.id,
                position=cursor.position,
                pointer=cursor.pointer,
                color=cursor.color
            )
        )
    )

async def multicast_tiles(target_conns: list[Cursor], start: Point, end: Point, tiles: Tiles):
    await multicast(
    target_conns=[cursor.id for cursor in target_conns],
    message=Message(
        event=EventCollection.TILES,
        payload=TilesPayload(
            start_p=start,
            end_p=end,
            tiles=tiles.to_str()
        )
    )
)
