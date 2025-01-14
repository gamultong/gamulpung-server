from event.broker import EventBroker
from event.message import Message
from event.payload import (
    TilesEvent, FetchTilesPayload, TilesPayload,
    ErrorEvent, ErrorPayload
)

from handler.board import BoardHandler

from data.board import Point

from config import VIEW_SIZE_LIMIT


def validate_fetch_range(start: Point, end: Point):
    # start_p: 좌상, end_p: 우하 확인
    if start.x > end.x or start.y < end.y:
        return Message(
            event=ErrorEvent.ERROR,
            payload=ErrorPayload(msg="start_p should be left-top, and end_p should be right-bottom")
        )

    # start_p와 end_p 차이 확인
    x_gap, y_gap = (end.x - start.x + 1), (start.y - end.y + 1)
    if x_gap > VIEW_SIZE_LIMIT or y_gap > VIEW_SIZE_LIMIT:
        return Message(
            event=ErrorEvent.ERROR,
            payload=ErrorPayload(msg=f"fetch gap should not be more than {VIEW_SIZE_LIMIT}")
        )

    return None


class FetchTilesReceiver:
    @EventBroker.add_receiver(TilesEvent.FETCH_TILES)
    @staticmethod
    async def receive_fetch_tiles(message: Message[FetchTilesPayload]):
        sender = message.header["sender"]

        start: Point = message.payload.start_p
        end: Point = message.payload.end_p

        if (msg := validate_fetch_range(start, end)):
            await multicast(
                target_conns=[sender],
                message=msg
            )
            return

        tiles = await fetch_tiles(start, end)

        await multicast(
            target_conns=[sender],
            message=Message(
                event=TilesEvent.TILES,
                payload=TilesPayload(
                    start_p=start,
                    end_p=end,
                    tiles=tiles.to_str()
                )
            )
        )


async def fetch_tiles(start: Point, end: Point):
    tiles = await BoardHandler.fetch(start, end)
    tiles.hide_info()

    return tiles


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