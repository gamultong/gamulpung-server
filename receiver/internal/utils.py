from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventEnum, CursorsPayload, CursorReviveAtPayload
)

from handler.cursor import CursorHandler

from data.cursor import Cursor
from data.board import Point


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
