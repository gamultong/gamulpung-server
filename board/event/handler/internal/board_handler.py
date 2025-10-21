import asyncio
from event import EventBroker
from data_layer.board import Point, Tile, Tiles, Section
from board.data.handler import BoardHandler
from data_layer.cursor import Color
from message import Message
from message.payload import (
    FetchTilesPayload,
    TilesPayload,
    TilesEvent,
    NewConnEvent,
    NewConnPayload,
    NewCursorCandidatePayload,
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
    FlagSetPayload,
    ErrorEvent,
    ErrorPayload
)
from config import Config

VIEW_SIZE_LIMIT = Config.VIEW_SIZE_LIMIT


class BoardEventHandler():
    @EventBroker.add_receiver(TilesEvent.FETCH_TILES)
    @staticmethod
    async def receive_fetch_tiles(message: Message[FetchTilesPayload]):
        sender = message.header["sender"]

        start_p: Point = message.payload.start_p
        end_p: Point = message.payload.end_p

        # start_p: 좌상, end_p: 우하 확인
        if start_p.x > end_p.x or start_p.y < end_p.y:
            await EventBroker.publish(Message(
                event="multicast",
                header={
                    "origin_event": ErrorEvent.ERROR,
                    "target_conns": [sender]
                },
                payload=ErrorPayload(msg="start_p should be left-top, and end_p should be right-bottom")
            ))
            return

        # start_p와 end_p 차이 확인
        x_gap, y_gap = (end_p.x - start_p.x + 1), (start_p.y - end_p.y + 1)
        if x_gap > VIEW_SIZE_LIMIT or y_gap > VIEW_SIZE_LIMIT:
            await EventBroker.publish(Message(
                event="multicast",
                header={
                    "origin_event": ErrorEvent.ERROR,
                    "target_conns": [sender]
                },
                payload=ErrorPayload(msg=f"fetch gap should not be more than {VIEW_SIZE_LIMIT}")
            ))
            return

        await BoardEventHandler._publish_tiles(start_p, end_p, [sender])

    @EventBroker.add_receiver(NewConnEvent.NEW_CONN)
    @staticmethod
    async def receive_new_conn(message: Message[NewConnPayload]):
        sender = message.payload.conn_id

        width = message.payload.width
        height = message.payload.height

        # 커서의 위치
        position = await BoardHandler.get_random_open_position()

        start_p = Point(
            x=position.x - width,
            y=position.y + height
        )
        end_p = Point(
            x=position.x+width,
            y=position.y-height
        )
        publish_tiles = BoardEventHandler._publish_tiles(start_p, end_p, [sender])

        message = Message(
            event=NewConnEvent.NEW_CURSOR_CANDIDATE,
            payload=NewCursorCandidatePayload(
                conn_id=message.payload.conn_id,
                width=width, height=height,
                position=position
            )
        )

        await asyncio.gather(
            publish_tiles,
            EventBroker.publish(message)
        )

    @staticmethod
    async def _publish_tiles(start: Point, end: Point, to: list[str]):
        tiles = await BoardHandler.fetch(start, end)
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

        tiles = await BoardHandler.fetch(
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

                if (not tile.is_mine) and (tile.number is None):
                    # 빈 칸. 주변 칸 모두 열기.
                    start_p, end_p, tiles = await BoardHandler.open_tiles_cascade(pointer)
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
                    tile = await BoardHandler.open_tile(pointer)

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

                _ = await BoardHandler.set_flag_state(p=pointer, state=flag_state, color=color)

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

        tiles = await BoardHandler.fetch(start=position, end=position)
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
