from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventEnum, 
    OpenTilePayload, SingleTileOpenedPayload, TilesOpenedPayload,
    YouDiedPayload, CursorsDiedPayload, CursorInfoPayload
)

from handler.board import BoardHandler
from handler.cursor import CursorHandler

from data.board import Point, Tile, Tiles, PointRange
from data.cursor import Cursor

from config import MINE_KILL_DURATION_SECONDS

from datetime import datetime, timedelta

from .utils import multicast

def get_tile_if_openable(cursor:Cursor):
    if not cursor.check_interactable(cursor.pointer):
        return None

    # 보드 상태 가져오기 ~ 업데이트하기
    tiles = BoardHandler.fetch(start=cursor.pointer, end=cursor.pointer)
    tile = Tile.from_int(tiles[0])

    if tile.is_open:
        return None
    
    if tile.is_flag:
        return None
    
    return tile

class OpenTileReceiver():
    @EventBroker.add_receiver(EventEnum.OPEN_TILE)
    @staticmethod
    async def receive_open_tile(message: Message[OpenTilePayload]):
        cursor = CursorHandler.get_cursor(message.header["sender"])

        if not (tile := get_tile_if_openable(cursor)):
            return

        is_multi_openable = (not tile.is_mine) and (tile.number is None)
        if is_multi_openable:
            # 빈 칸. 주변 칸 모두 열기.
            start_p, end_p, tiles = await BoardHandler.open_tiles_cascade(cursor.pointer)
            tiles.hide_info()
            tiles_str = tiles.to_str()

            # 변경된 타일을 보고있는 커서들에게 전달
            view_cursors = CursorHandler.view_includes_range(start=start_p, end=end_p)
            if len(view_cursors) > 0:
                await multicast_tiles_opened(
                    target_conns=view_cursors, 
                    point_range=PointRange(start_p, end_p),
                    tiles_str=tiles_str
                )

        else:
            tile = await BoardHandler.open_tile(cursor.pointer)

            # 변경된 타일을 보고있는 커서들에게 전달
            view_cursors = CursorHandler.view_includes_point(p=cursor.pointer)
            if len(view_cursors) > 0:
                await multicast_single_tile_opened(
                    target_conns=view_cursors,
                    tile=tile, position=cursor.pointer
                )

            if not tile.is_mine:
                return

            # 주변 8칸 커서들 찾기
            nearby_cursors = get_nearby_cursors(cursor)
            if len(nearby_cursors) > 0:
                revive_at = get_revive_at()

                # 범위 안 커서들에게 you-died
                await multicast_you_died(target_conns=nearby_cursors, revive_at=revive_at)
                
                # 보고있는 커서들에게 cursors-died
                watchers = get_watchers(nearby_cursors)
                if len(watchers) > 0:
                    await multicast_cursors_died(
                        target_conns=watchers,
                        cursors=nearby_cursors,
                        revive_at=revive_at
                    )

                # 영향 범위 커서들 죽이기
                kill_cursors(nearby_cursors, revive_at)

def get_revive_at():
    return datetime.now() + timedelta(seconds=MINE_KILL_DURATION_SECONDS)

def get_nearby_cursors(cursor:Cursor):
    start_p = Point(cursor.pointer.x - 1, cursor.pointer.y + 1)
    end_p = Point(cursor.pointer.x + 1, cursor.pointer.y - 1)

    nearby_cursors = CursorHandler.exists_range(start=start_p, end=end_p)
    # nearby_cursors 중 죽지 않은 커서들만 걸러내기
    return list(filter(lambda c: c.revive_at is None, nearby_cursors))

def get_watchers(cursors: list[Cursor]):
    watcher_ids: set[str] = set()
    for cursor in cursors:
        temp_watcher_ids = CursorHandler.get_watchers_id(cursor_id=cursor.id)
        watcher_ids.update(temp_watcher_ids + [cursor.id])

    return [
        CursorHandler.get_cursor(id)
        for id in watcher_ids
    ]


def kill_cursors(cursors: list[Cursor], revive_at: datetime):
    for c in cursors:
        c.revive_at = revive_at
        c.pointer = None


async def multicast_tiles_opened(target_conns: list[Cursor], point_range: PointRange, tiles_str: str):
    await multicast(
        target_conns=[c.id for c in target_conns],
        message=Message(
            event=EventEnum.TILES_OPENED,
            payload=TilesOpenedPayload(
                start_p=point_range.top_left,
                end_p=point_range.bottom_right,
                tiles=tiles_str
            )
        )
    )

async def multicast_single_tile_opened(target_conns: list[Cursor], tile: Tile, position: Point):
    tile_str = Tiles(data=bytearray([tile.data])).to_str()
    
    await multicast(
        target_conns=[c.id for c in target_conns],
        message=Message(
            event=EventEnum.SINGLE_TILE_OPENED,
            payload=SingleTileOpenedPayload(
                position=position,
                tile=tile_str
            )
        )
    )

async def multicast_you_died(target_conns: list[Cursor], revive_at: datetime):
    await multicast(
        target_conns=[c.id for c in target_conns],
        message=Message(
            event=EventEnum.YOU_DIED,
            payload=YouDiedPayload(revive_at=revive_at.astimezone().isoformat())
        )
    )

async def multicast_cursors_died(target_conns: list[Cursor], cursors: list[Cursor],revive_at: datetime ):
    await multicast(
        target_conns=[c.id for c in target_conns],
        message=Message(
            event=EventEnum.CURSORS_DIED,
            payload=CursorsDiedPayload(
                revive_at=revive_at.astimezone().isoformat(),
                cursors=[CursorInfoPayload(
                    id=cursor.id,
                    position=cursor.position,
                    color=cursor.color,
                    pointer=cursor.pointer
                ) for cursor in cursors]
            )
        )
    )