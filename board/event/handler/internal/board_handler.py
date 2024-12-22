import asyncio
from event import EventBroker
from board.data import Point, Tile, Tiles
from board.data.handler import BoardHandler
from cursor.data import Color
from message import Message
from message.payload import (
    FetchTilesPayload,
    TilesPayload,
    TilesEvent,
    NewConnEvent,
    NewConnPayload,
    TryPointingPayload,
    PointingResultPayload,
    PointEvent,
    MoveEvent,
    CheckMovablePayload,
    MovableResultPayload,
    ClickType,
    InteractionEvent,
    TilesOpenedPayload,
    SingleTileOpenedPayload,
    FlagSetPayload
)


class BoardEventHandler():
    @EventBroker.add_receiver(TilesEvent.FETCH_TILES)
    @staticmethod
    async def receive_fetch_tiles(message: Message[FetchTilesPayload]):
        sender = message.header["sender"]

        await BoardEventHandler._publish_tiles(message.payload.start_p, message.payload.end_p, [sender])

    @EventBroker.add_receiver(NewConnEvent.NEW_CONN)
    @staticmethod
    async def receive_new_conn(message: Message[NewConnPayload]):
        sender = message.payload.conn_id

        # 0, 0 기준으로 fetch
        width = message.payload.width
        height = message.payload.height

        start_p = Point(x=-width, y=height)
        end_p = Point(x=width, y=-height)

        await BoardEventHandler._publish_tiles(start_p, end_p, [sender])

    @staticmethod
    async def _publish_tiles(start: Point, end: Point, to: list[str]):
        tiles = BoardHandler.fetch(start, end)
        tiles.hide_info()

        pub_message = Message(
            event="multicast",
            header={"target_conns": to,
                    "origin_event": TilesEvent.TILES},
            payload=TilesPayload(
                start_p=Point(start.x, start.y),
                end_p=Point(end.x, end.y),
                tiles=tiles.to_str()
            )
        )

        await EventBroker.publish(pub_message)

    @EventBroker.add_receiver(PointEvent.TRY_POINTING)
    @staticmethod
    async def receive_try_pointing(message: Message[TryPointingPayload]):
        sender = message.header["sender"]

        pointer = message.payload.new_pointer

        tiles = BoardHandler.fetch(
            Point(pointer.x-1, pointer.y+1),
            Point(pointer.x+1, pointer.y-1)
        )

        # 포인팅한 칸 포함 3x3칸 중 열린 칸이 존재하는지 확인
        pointable = False
        for tile in tiles.data:
            t = Tile.from_int(tile)
            if t.is_open:
                pointable = True
                break

        publish_coroutines = []

        pub_message = Message(
            event=PointEvent.POINTING_RESULT,
            header={"receiver": sender},
            payload=PointingResultPayload(
                pointer=pointer,
                pointable=pointable
            )
        )

        publish_coroutines.append(EventBroker.publish(pub_message))

        if not pointable:
            await asyncio.gather(*publish_coroutines)
            return

        cursor_pos = message.payload.cursor_position

        # 인터랙션 범위 체크
        if \
                pointer.x < cursor_pos.x - 1 or \
                pointer.x > cursor_pos.x + 1 or \
                pointer.y < cursor_pos.y - 1 or \
                pointer.y > cursor_pos.y + 1:
            await asyncio.gather(*publish_coroutines)
            return

        # 보드 상태 업데이트하기
        tile = Tile.from_int(tiles.data[4])  # 3x3칸 중 가운데 = 포인팅한 타일
        click_type = message.payload.click_type

        if tile.is_open:
            await asyncio.gather(*publish_coroutines)
            return

        match (click_type):
            # 닫힌 타일 열기
            case ClickType.GENERAL_CLICK:
                if tile.is_flag:
                    await asyncio.gather(*publish_coroutines)
                    return

                if tile.number is None:
                    # 빈 칸. 주변 칸 모두 열기.
                    start_p, end_p, tiles = BoardHandler.open_tiles_cascade(pointer)
                    tiles.hide_info()
                    tile_str = tiles.to_str()

                    pub_message = Message(
                        event=InteractionEvent.TILES_OPENED,
                        payload=TilesOpenedPayload(
                            start_p=start_p,
                            end_p=end_p,
                            tiles=tile_str
                        )
                    )
                    publish_coroutines.append(EventBroker.publish(pub_message))
                else:
                    tile = BoardHandler.open_tile(pointer)

                    tile_str = Tiles(data=bytearray([tile.data])).to_str()

                    pub_message = Message(
                        event=InteractionEvent.SINGLE_TILE_OPENED,
                        payload=SingleTileOpenedPayload(
                            position=pointer,
                            tile=tile_str
                        )
                    )
                    publish_coroutines.append(EventBroker.publish(pub_message))

            # 깃발 꽂기/뽑기
            case ClickType.SPECIAL_CLICK:
                flag_state = not tile.is_flag
                color = message.payload.color if flag_state else None

                _ = BoardHandler.set_flag_state(p=pointer, state=flag_state, color=color)

                pub_message = Message(
                    event=InteractionEvent.FLAG_SET,
                    payload=FlagSetPayload(
                        position=pointer,
                        is_set=flag_state,
                        color=color,
                    )
                )
                publish_coroutines.append(EventBroker.publish(pub_message))

        await asyncio.gather(*publish_coroutines)

    @EventBroker.add_receiver(MoveEvent.CHECK_MOVABLE)
    @staticmethod
    async def receive_check_movable(message: Message[CheckMovablePayload]):
        sender = message.header["sender"]

        position = message.payload.position

        tiles = BoardHandler.fetch(start=position, end=position)
        tile = Tile.from_int(tiles.data[0])

        movable = tile.is_open

        message = Message(
            event=MoveEvent.MOVABLE_RESULT,
            header={"receiver": sender},
            payload=MovableResultPayload(
                position=position,
                movable=movable
            )
        )

        await EventBroker.publish(message)
