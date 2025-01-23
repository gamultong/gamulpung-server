from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventEnum, NewConnPayload,
    MyCursorPayload, TilesPayload
)

from handler.board import BoardHandler
from handler.cursor import CursorHandler

from data.board import Point
from data.cursor import Cursor

from .utils import (
    multicast, watch, get_view_range_points, publish_new_cursors
)

# 1. 커서 포지션 선정
# 2. 커서 만든 후 보내기
# 3. 커서간 연관관계 설정 후 보내기
# 4. 타일 보내기


class NewConnReceiver():
    @EventBroker.add_receiver(EventEnum.NEW_CONN)
    @staticmethod
    async def receive_new_conn(message: Message[NewConnPayload]):
        cursor = await new_cursor(message.payload)

        start, end = get_view_range_points(cursor.position, cursor.width, cursor.height)

        await multicast(
            target_conns=[cursor.id],
            message=Message(
                event=EventEnum.MY_CURSOR,
                payload=MyCursorPayload(
                    id=cursor.id,
                    position=cursor.position,
                    pointer=cursor.pointer,
                    color=cursor.color
                )
            )
        )

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

        await multicast(
            target_conns=[cursor.id],
            message=Message(
                event=EventEnum.TILES,
                payload=TilesPayload(
                    start_p=start,
                    end_p=end,
                    tiles=tiles.to_str()
                )
            )
        )


async def new_cursor(payload: NewConnPayload):
    position = await BoardHandler.get_random_open_position()

    conn_id = payload.conn_id
    width = payload.width
    height = payload.height

    cursor = CursorHandler.create_cursor(
        conn_id=conn_id,
        position=position,
        width=width, height=height
    )

    return cursor


async def fetch_tiles(start: Point, end: Point):
    tiles = await BoardHandler.fetch(start, end)
    tiles.hide_info()

    return tiles


def fetch_with_view_including(cursor: Cursor) -> list[Cursor]:
    cursors_in_view = CursorHandler.view_includes_point(cursor.position, exclude_ids=[cursor.id])

    return cursors_in_view


def fetch_cursors_in_view(cursor: Cursor) -> list[Cursor]:
    start, end = get_view_range_points(cursor.position, cursor.width, cursor.height)

    cursors_in_view = CursorHandler.exists_range(start=start, end=end, exclude_ids=[cursor.id])

    return cursors_in_view
