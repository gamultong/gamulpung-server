from event.broker import EventBroker
from event.message import Message
from event.payload import (
    NewConnEvent, SetViewSizePayload,
    ErrorEvent, ErrorPayload,
    CursorsPayload, CursorReviveAtPayload
)

from handler.cursor import CursorHandler

from data.board import Point
from data.cursor import Cursor

from config import VIEW_SIZE_LIMIT


class SetViewSizeReceiver():
    @EventBroker.add_receiver(NewConnEvent.SET_VIEW_SIZE)
    @staticmethod
    async def receive_set_view_size(message: Message[SetViewSizePayload]):
        sender = message.header["sender"]
        cursor = CursorHandler.get_cursor(sender)

        new_width, new_height = message.payload.width, message.payload.height

        if (msg := validate_view_size(cursor, new_height, new_height)):
            await multicast(
                target_conns=[sender],
                message=msg
            )
            return

        old_width, old_height = cursor.width, cursor.height
        cursor.set_size(new_width, new_height)

        size_grown = (new_width > old_width) or (new_height > old_height)

        if size_grown:
            old_top_left, old_bottom_right = get_view_range_points(cursor.position, old_width, old_height)
            new_top_left, new_bottom_right = get_view_range_points(cursor.position, new_width, new_height)

            # 현재 범위를 제외한 새로운 범위에서 커서들 가져오기
            new_watchings = CursorHandler.exists_range(
                start=new_top_left, end=new_bottom_right,
                exclude_start=old_top_left, exclude_end=old_bottom_right
            )

            if len(new_watchings) > 0:
                watch(watchers=[sender], watchings=new_watchings)

                await publish_new_cursors(target_cursors=[cursor], cursors=new_watchings)

        cursors_to_unwatch = find_cursors_to_unwatch(cursor)
        if len(cursors_to_unwatch) > 0:
            unwatch(watchers=[sender], watching=cursors_to_unwatch)


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


def get_view_range_points(postion: Point, width: int, height: int):
    top_left = Point(x=postion.x - width, y=postion.y + height)
    bottom_right = Point(x=postion.x + width, y=postion.y - height)
    return top_left, bottom_right


def validate_view_size(cursor: Cursor, new_width: int, new_height: int):
    if new_width == cursor.width and new_height == cursor.height:
        # 변동 없음
        return Message(
            event=ErrorEvent.ERROR,
            payload=ErrorPayload(msg=f"view size is same as current size")
        )

    if new_width <= 0 or new_height <= 0 or \
            new_width > VIEW_SIZE_LIMIT or new_height > VIEW_SIZE_LIMIT:
        # 뷰 범위 한계 넘음
        return Message(
            event=ErrorEvent.ERROR,
            payload=ErrorPayload(msg=f"view width or height should be more than 0 and less than {VIEW_SIZE_LIMIT}")
        )


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


async def publish_new_cursors(target_cursors: list[Cursor], cursors: list[Cursor]):
    message = Message(
        event=NewConnEvent.CURSORS,
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
