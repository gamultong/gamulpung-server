from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventEnum, 
    OpenTilePayload, TilesOpenedPayload,
    YouDiedPayload, CursorReviveAtPayload, CursorsPayload
)

from handler.board import BoardHandler
from handler.cursor import CursorHandler

from data.board import Point, Tile, Tiles, PointRange
from data.cursor import Cursor

from config import MINE_KILL_DURATION_SECONDS

from datetime import datetime, timedelta

from .utils import multicast

async def get_tile_if_openable(cursor:Cursor):
    if not cursor.check_interactable(cursor.pointer):
        return None

    # 보드 상태 가져오기 ~ 업데이트하기
    tiles = await BoardHandler.fetch(start=cursor.pointer, end=cursor.pointer)
    tile = Tile.from_int(tiles.data[0])

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

        if not (tile := await get_tile_if_openable(cursor)):
            return

        # 빈 칸. 주변 칸 모두 열기.
        opened_range, tiles_opened = await open_tile(point=cursor.pointer)

        # 변경된 타일을 보고있는 커서들에게 전달
        view_cursors = CursorHandler.view_includes_range(
            start=opened_range.top_left, 
            end=opened_range.bottom_right
        )
        await multicast_tiles_opened(
            target_conns=view_cursors, 
            point_range=opened_range,
            tiles_str=tiles_opened
        )

        if tile.is_mine:
            dead_cursors = detonate_mine(point=cursor.pointer)

            # 범위 안 커서들에게 you-died
            await multicast_you_died(target_conns=dead_cursors)
            
            # 보고있는 커서들에게 cursors-died
            watchers = get_watchers(dead_cursors)
            await multicast_cursors_died(target_conns=watchers,cursors=dead_cursors)

async def open_tile(point: Point) -> tuple[PointRange, str]:
    start_p, end_p, tiles = await BoardHandler.open_tiles(point)
    tiles.hide_info()
    tiles_str = tiles.to_str()
    return PointRange(start_p, end_p), tiles_str

def detonate_mine(point:Point):        
    # 주변 8칸 커서들 찾기
    nearby_cursors = get_nearby_alive_cursors(point)

    revive_at = get_revive_at()

    for c in nearby_cursors:
        c.revive_at = revive_at
        c.pointer = None

    return nearby_cursors

def get_revive_at():
    return datetime.now() + timedelta(seconds=MINE_KILL_DURATION_SECONDS)

def get_nearby_alive_cursors(point: Point):
    start_p = Point(point.x - 1, point.y + 1)
    end_p = Point(point.x + 1, point.y - 1)

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

async def multicast_you_died(target_conns: list[Cursor]):
    for cursor in target_conns:
        await multicast(
            target_conns=[cursor.id],
            message=Message(
                event=EventEnum.YOU_DIED,
                payload=YouDiedPayload(revive_at=cursor.revive_at.astimezone().isoformat())
            )
        )

async def multicast_cursors_died(target_conns: list[Cursor], cursors: list[Cursor] ):
    await multicast(
        target_conns=[c.id for c in target_conns],
        message=Message(
            event=EventEnum.CURSORS_DIED,
            payload=CursorsPayload(
                cursors=[CursorReviveAtPayload(
                    id=cursor.id,
                    position=cursor.position,
                    color=cursor.color,
                    revive_at=cursor.revive_at,
                    pointer=cursor.pointer
                ) for cursor in cursors]
            )
        )
    )