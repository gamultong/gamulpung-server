from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, ConnClosedPayload, CursorQuitPayload, ErrorPayload
)

from handler.cursor import CursorHandler
from handler.score import ScoreHandler

from data.cursor import Cursor

from config import VIEW_SIZE_LIMIT

from .utils import multicast, unwatch, get_watchers


class ConnClosedReceiver:
    @EventBroker.add_receiver(EventCollection.CONN_CLOSED)
    @staticmethod
    async def receive_conn_closed(message: Message[ConnClosedPayload]):
        cursor = CursorHandler.get_cursor(message.header["sender"])

        watching = get_watchings(cursor)
        watchers = get_watchers(cursor)

        unwatch(watchers=[cursor], watchings=watching)
        unwatch(watchers=watchers, watchings=[cursor])

        await remove_cursor(cursor)

        await multicast_cursor_quit(target_conns=watchers, cursor=cursor)


def get_watchings(cursor: Cursor) -> list[Cursor]:
    watchers_id = CursorHandler.get_watching_id(cursor.id)

    return [CursorHandler.get_cursor(id) for id in watchers_id]

async def remove_cursor(cursor: Cursor):
    CursorHandler.remove_cursor(cursor.id)
    await ScoreHandler.delete(cursor.id)


async def multicast_cursor_quit(target_conns: list[Cursor], cursor: Cursor):
    await multicast(
        target_conns=[c.id for c in target_conns],
        message=Message(
            event=EventCollection.CURSOR_QUIT,
            payload=CursorQuitPayload(id=cursor.id)
        )
    )
