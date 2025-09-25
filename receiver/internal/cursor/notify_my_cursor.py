from event.broker import EventBroker
from event.message import Message
from event.payload import IdPayload

from data.conn.event import ServerEvent
from data.cursor import Cursor
from data.conn.event import ServerEvent

from handler.cursor import CursorEvent, CursorHandler

from ..utils import multicast


class NotifyMyCursorReceiver():
    @EventBroker.add_receiver(CursorEvent.CREATED)
    @staticmethod
    async def notify_my_cursor(message: Message[IdPayload[str]]):
        id = message.payload.id
        cursor = await CursorHandler.get(id)

        await multicast_my_cursor(cursor)

        watchers = await CursorHandler.get_watchers(cursor=cursor)
        watchers.append(cursor)  # 본인도 줘야 함.

        await multicast_cursors_state(target_conns=watchers, cursor=cursor)


async def multicast_my_cursor(cursor: Cursor):
    event = ServerEvent.MyCursor(id=cursor.id)

    await multicast(target_conns=[cursor.conn_id], event=event)


async def multicast_cursors_state(target_conns: list[Cursor], cursor: Cursor):
    # TODO: empty 로직 추가 (@byundojin)

    event = ServerEvent.CursorsState(
        cursors=[
            ServerEvent.CursorsState.Elem(
                id=cursor.id,
                color=cursor.color,
                pointer=cursor.pointer,
                position=cursor.position,
                revive_at=cursor.revive_at,
            )
        ]
    )

    await multicast(target_conns=[c.id for c in target_conns], event=event)
