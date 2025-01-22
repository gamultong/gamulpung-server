from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventEnum, MovingPayload, MovedPayload, ErrorPayload,
    CursorsPayload, CursorReviveAtPayload
)

from handler.board import BoardHandler
from handler.cursor import CursorHandler

from data.board import Point, Tile
from data.cursor import Cursor


async def validate_new_position(cursor: Cursor, new_position: Point) -> Message | None:
    if new_position == cursor.position:
        return Message(
            event=EventEnum.ERROR,
            payload=ErrorPayload(msg="moving to current position is not allowed")
        )

    if not cursor.check_interactable(new_position):
        return Message(
            event=EventEnum.ERROR,
            payload=ErrorPayload(msg="only moving to 8 nearby tiles is allowed")
        )

    tiles = await BoardHandler.fetch(start=new_position, end=new_position)
    tile = Tile.from_int(tiles.data[0])
    if not tile.is_open:
        return Message(
            event=EventEnum.ERROR,
            payload=ErrorPayload(msg="moving to closed tile is not available")
        )


class MovingReceiver():
    @EventBroker.add_receiver(EventEnum.MOVING)
    @staticmethod
    async def receive_moving(message: Message[MovingPayload]):
        sender = message.header["sender"]

        cursor = CursorHandler.get_cursor(sender)
        position = message.payload.position

        if (msg := await validate_new_position(cursor, position)):
            await multicast(
                target_conns=[sender],
                message=msg
            )
            return

        old_position = cursor.position
        cursor.position = position

        cursors_to_unwatch = find_cursors_to_unwatch(cursor)
        if len(cursors_to_unwatch) > 0:
            unwatch(watcher=[cursor], watching=cursors_to_unwatch)

        old_top_left, old_bottom_right = get_view_range_points(old_position, cursor.width, cursor.height)
        new_top_left, new_bottom_right = get_view_range_points(position, cursor.width, cursor.height)

        new_watchings = CursorHandler.exists_range(
            start=new_top_left, end=new_bottom_right,
            exclude_start=old_top_left, exclude_end=old_bottom_right,
            exclude_ids=[cursor.id]
        )
        if len(new_watchings) > 0:
            watch(wachers=[cursor.id], watchings=new_watchings)

            await publish_new_cursors(target_cursors=[cursor], cursors=new_watchings)

        original_watcher_ids = CursorHandler.get_watchers(cursor_id=cursor.id)

        if len(original_watcher_ids) > 0:
            original_watchers = [CursorHandler.get_cursor(id) for id in original_watcher_ids]

            # 범위 벗어나면 watcher 제거
            unwatching_cursors = [
                other_cursor
                for other_cursor in original_watchers
                if not other_cursor.check_in_view(cursor.position)
            ]

            unwatch(watcher=unwatching_cursors, watching=cursor)

            # moved 이벤트 전달
            multicast(
                target_conns=original_watchers,
                message=Message(
                    event=EventEnum.MOVED,
                    payload=MovedPayload(
                        id=cursor.id,
                        new_position=position
                    )
                )
            )

        # 새로운 위치를 바라보고 있는 커서들 찾기, 본인 제외
        watchers_new_pos = CursorHandler.view_includes_point(p=position, exclude_ids=[cursor.id])

        new_watchers = list(filter(lambda c: c.id not in original_watcher_ids, watchers_new_pos))
        if len(new_watchers) > 0:
            watch(watcher=new_watchers, watchings=[cursor])

            await publish_new_cursors(target_cursors=new_watchers, cursors=[cursor])


async def multicast(target_conns: list[str], message: Message):
    await EventBroker.publish(
        message=Message(
            event="multicast",
            header={
                "target_conns": target_conns,
                "origin_event": message.event
            },
            payload=message.payload
        )
    )


def watch(wachers: list[Cursor], watchings: list[Cursor]):
    for wacher in wachers:
        for waching in watchings:
            CursorHandler.add_watcher(watcher=wacher, watching=waching)


def unwatch(wachers: list[Cursor], watchings: list[Cursor]):
    for wacher in wachers:
        for waching in watchings:
            CursorHandler.remove_watcher(watcher=wacher, watching=waching)


def get_view_range_points(postion: Point, width: int, height: int):
    top_left = Point(x=postion.x - width, y=postion.y + height)
    bottom_right = Point(x=postion.x + width, y=postion.y - height)
    return top_left, bottom_right


def find_cursors_to_unwatch(cursor: Cursor) -> list[Cursor]:
    def get_if_in_view(cursor_id: str) -> Cursor | None:
        other_cursor = CursorHandler.get_cursor(cursor_id)
        if cursor.check_in_view(other_cursor.position):
            return None
        return other_cursor

    cur_watching = CursorHandler.get_watching(cursor_id=cursor.id)

    return [
        cursor
        for id in cur_watching
        if (cursor := get_if_in_view(id))
    ]


async def publish_new_cursors(target_cursors: list[Cursor], cursors: list[Cursor]):
    message = Message(
        event=EventEnum.CURSORS,
        payload=CursorsPayload(
            cursors=[CursorReviveAtPayload(
                id=cursor.id,
                position=cursor.position,
                pointer=cursor.pointer,
                color=cursor.color,
                revive_at=cursor.revive_at.astimezone().isoformat() if cursor.revive_at is not None else None
            ) for cursor in cursors]
        )
    )

    await multicast(
        target_conns=[cursor.id for cursor in target_cursors],
        message=message
    )
