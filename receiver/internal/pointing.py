from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, ClickType, ErrorPayload,
    PointingPayload, PointerSetPayload,
    OpenTilePayload, SetFlagPayload
)

from handler.cursor import CursorHandler

from data.board import Point, Tile, Tiles, PointRange
from data.cursor import Cursor

from .utils import multicast, get_watchers


class PointingReceiver():
    @EventBroker.add_receiver(EventCollection.POINTING)
    @staticmethod
    async def receive_pointing(message: Message[PointingPayload]):
        cursor = CursorHandler.get_cursor(message.header["sender"])

        new_pointer = message.payload.position
        click_type = message.payload.click_type

        if (msg := validate_pointable(cursor, new_pointer)):
            await multicast(target_conns=[cursor.id], message=msg)
            return

        cursor.pointer = new_pointer

        watchers = get_watchers(cursor=cursor)
        if len(watchers) > 0:
            await multicast_pointer_set(
                target_conns=[cursor] + watchers,
                cursor=cursor
            )

        if click_type == ClickType.GENERAL_CLICK:
            await publish_open_tile(cursor=cursor)
        if click_type == ClickType.SPECIAL_CLICK:
            await publish_set_flag(cursor=cursor)


async def publish_open_tile(cursor: Cursor):
    await EventBroker.publish(message=Message(
        event=EventCollection.OPEN_TILE,
        header={"sender": cursor.id},
        payload=OpenTilePayload()
    ))


async def publish_set_flag(cursor: Cursor):
    await EventBroker.publish(message=Message(
        event=EventCollection.SET_FLAG,
        header={"sender": cursor.id},
        payload=SetFlagPayload()
    ))


async def multicast_pointer_set(target_conns: list[Cursor], cursor: Cursor):
    await multicast(
        target_conns=[c.id for c in target_conns],
        message=Message(
            event=EventCollection.POINTER_SET,
            payload=PointerSetPayload(
                id=cursor.id,
                pointer=cursor.pointer
            )
        )
    )


def validate_pointable(cursor: Cursor, point: Point):
    if cursor.revive_at is not None:
        return Message(
            event=EventCollection.ERROR,
            payload=ErrorPayload(msg="dead cursor cannot do pointing")
        )

    # 뷰 바운더리 안에서 포인팅하는지 확인
    if not cursor.check_in_view(point):
        return Message(
            event=EventCollection.ERROR,
            payload=ErrorPayload(msg="pointer is out of cursor view")
        )
