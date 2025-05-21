from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, CursorsPayload, CursorPayload
)

from handler.cursor import CursorHandler
from handler.board import BoardHandler
from handler.score import ScoreHandler, ScoreNotFoundException

from data.cursor import Cursor
from data.board import Point


async def multicast(target_conns: list[str], message: Message):
    if len(target_conns) == 0:
        return

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


async def broadcast(message: Message):
    await EventBroker.publish(
        message=Message(
            event="broadcast",
            header={
                "origin_event": message.event
            },
            payload=message.payload
        )
    )


async def fetch_tiles(start: Point, end: Point):
    tiles = await BoardHandler.fetch(start, end)
    tiles.hide_info()

    return tiles


def watch(watchers: list[Cursor], watchings: list[Cursor]):
    for watcher in watchers:
        for watching in watchings:
            CursorHandler.add_watcher(watcher=watcher, watching=watching)


def unwatch(watchers: list[Cursor], watchings: list[Cursor]):
    for watcher in watchers:
        for watching in watchings:
            CursorHandler.remove_watcher(watcher=watcher, watching=watching)


async def publish_new_cursors(target_cursors: list[Cursor], cursors: list[Cursor]):
    if len(cursors) == 0:
        return None

    cursor_payloads = []

    for cursor in cursors:
        try:
            score = await ScoreHandler.get(cursor.id)
        except ScoreNotFoundException:
            continue

        cursor_p = CursorPayload(
            id=cursor.id,
            position=cursor.position,
            pointer=cursor.pointer,
            color=cursor.color,
            revive_at=cursor.revive_at.astimezone().isoformat() if cursor.revive_at is not None else None,
            score=score.value
        )

        cursor_payloads.append(cursor_p)

    message = Message(
        event=EventCollection.CURSORS,
        payload=CursorsPayload(cursors=cursor_payloads)
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

    cur_watching = CursorHandler.get_watching_id(cursor_id=cursor.id)

    return [
        cursor
        for id in cur_watching
        if (cursor := get_if_in_view(id))
    ]


def get_view_range_points(postion: Point, width: int, height: int):
    top_left = Point(x=postion.x - width, y=postion.y + height)
    bottom_right = Point(x=postion.x + width, y=postion.y - height)
    return top_left, bottom_right


def get_watchers(cursor: Cursor) -> list[Cursor]:
    watchers_id = CursorHandler.get_watchers_id(cursor.id)

    return [CursorHandler.get_cursor(id) for id in watchers_id]
