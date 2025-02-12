from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventEnum, ClickType, ErrorPayload,
    PointingPayload, PointerSetPayload,
    FlagSetPayload, SingleTileOpenedPayload, TilesOpenedPayload,
    YouDiedPayload, CursorsDiedPayload, CursorInfoPayload
)

from handler.board import BoardHandler
from handler.cursor import CursorHandler

from data.board import Point, Tile, Tiles
from data.cursor import Cursor

from config import MINE_KILL_DURATION_SECONDS

from datetime import datetime, timedelta

from .utils import multicast


class PointingReceiver():
    @EventBroker.add_receiver(EventEnum.POINTING)
    @staticmethod
    async def receive_pointing(message: Message[PointingPayload]):
        sender = message.header["sender"]

        cursor = CursorHandler.get_cursor(sender)
        new_pointer = message.payload.position

        if (msg := validate_pointable(cursor, new_pointer)):
            await multicast(target_conns=[cursor.id], message=msg)
            return

        cursor.pointer = new_pointer

        watchers = CursorHandler.get_watchers_id(cursor.id)
        if len(watchers) > 0:
            await multicast(
                target_conns=[cursor.id] + watchers,
                message=Message(
                    event=EventEnum.POINTER_SET,
                    payload=PointerSetPayload(
                        id=cursor.id,
                        pointer=cursor.pointer
                    )
                )
            )

        # 인터랙션 범위 체크
        if not cursor.check_interactable(cursor.pointer):
            return

        # 보드 상태 가져오기 ~ 업데이트하기
        tiles = BoardHandler.fetch(start=cursor.pointer, end=cursor.pointer)
        tile = Tile.from_int(tiles[0])
        click_type = message.payload.click_type

        if tile.is_open:
            return

        if click_type == ClickType.GENERAL_CLICK:
            await general_click(cursor, tile)
        if click_type == ClickType.SPECIAL_CLICK:
            await special_click(cursor, tile)


def validate_pointable(cursor: Cursor, point: Point):
    if cursor.revive_at is not None:
        return Message(
            event=EventEnum.ERROR,
            payload=ErrorPayload(msg="dead cursor cannot do pointing")
        )

    # 뷰 바운더리 안에서 포인팅하는지 확인
    if not cursor.check_in_view(point):
        return Message(
            event=EventEnum.ERROR,
            payload=ErrorPayload(msg="pointer is out of cursor view")
        )


async def general_click(cursor: Cursor, tile: Tile):
    if tile.is_flag:
        return

    if (not tile.is_mine) and (tile.number is None):
        # 빈 칸. 주변 칸 모두 열기.
        start_p, end_p, tiles = await BoardHandler.open_tiles_cascade(cursor.pointer)
        tiles.hide_info()
        tile_str = tiles.to_str()

        # 변경된 타일을 보고있는 커서들에게 전달
        view_cursors = CursorHandler.view_includes_range(start=start_p, end=end_p)
        if len(view_cursors) > 0:
            await multicast(
                target_conns=[c.id for c in view_cursors],
                message=Message(
                    event=EventEnum.TILES_OPENED,
                    payload=TilesOpenedPayload(
                        start_p=start_p,
                        end_p=end_p,
                        tiles=tile_str
                    )
                )
            )
    else:
        tile = await BoardHandler.open_tile(cursor.pointer)

        # 변경된 타일을 보고있는 커서들에게 전달
        view_cursors = CursorHandler.view_includes_point(p=cursor.pointer)
        if len(view_cursors) > 0:
            await multicast(
                target_conns=[c.id for c in view_cursors],
                message=Message(
                    event=EventEnum.SINGLE_TILE_OPENED,
                    payload=SingleTileOpenedPayload(
                        position=cursor.pointer,
                        tile=Tiles(data=bytearray([tile.data])).to_str()
                    )
                )
            )

        if not tile.is_mine:
            return

        # 주변 8칸 커서들 찾기
        start_p = Point(cursor.pointer.x - 1, cursor.pointer.y + 1)
        end_p = Point(cursor.pointer.x + 1, cursor.pointer.y - 1)

        nearby_cursors = CursorHandler.exists_range(start=start_p, end=end_p)
        # nearby_cursors 중 죽지 않은 커서들만 걸러내기
        nearby_cursors = list(filter(lambda c: c.revive_at is None, nearby_cursors))

        if len(nearby_cursors) > 0:
            revive_at = datetime.now() + timedelta(seconds=MINE_KILL_DURATION_SECONDS)

            # 범위 안 커서들에게 you-died
            await multicast(
                target_conns=[c.id for c in nearby_cursors],
                message=Message(
                    event=EventEnum.YOU_DIED,
                    payload=YouDiedPayload(revive_at=revive_at.astimezone().isoformat())
                )
            )

            # 보고있는 커서들에게 cursors-died
            watcher_ids: set[str] = set()
            for cursor in nearby_cursors:
                temp_watcher_ids = CursorHandler.get_watchers_id(cursor_id=cursor.id)
                watcher_ids.update(temp_watcher_ids + [cursor.id])

            if len(watcher_ids) > 0:
                await multicast(
                    target_conns=watcher_ids,
                    message=Message(
                        event=EventEnum.CURSORS_DIED,
                        payload=CursorsDiedPayload(
                            revive_at=revive_at.astimezone().isoformat(),
                            cursors=[CursorInfoPayload(
                                id=cursor.id,
                                position=cursor.position,
                                color=cursor.color,
                                pointer=cursor.pointer
                            ) for cursor in nearby_cursors]
                        )
                    )
                )

            # 영향 범위 커서들 죽이기
            for c in nearby_cursors:
                c.revive_at = revive_at
                c.pointer = None


async def special_click(cursor: Cursor, tile: Tile):
    flag_state = not tile.is_flag
    color = cursor.color if flag_state else None

    await BoardHandler.set_flag_state(p=cursor.pointer, state=flag_state, color=color)

    pointer = cursor.pointer

    # 변경된 타일을 보고있는 커서들에게 전달
    view_cursors = CursorHandler.view_includes_point(p=pointer)
    if len(view_cursors) > 0:
        await multicast(
            target_conns=[c.id for c in view_cursors],
            message=Message(
                event=EventEnum.FLAG_SET,
                payload=FlagSetPayload(
                    position=pointer,
                    is_set=flag_state,
                    color=color
                )
            )
        )
