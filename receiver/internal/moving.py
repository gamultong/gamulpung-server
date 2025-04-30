from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, MovingPayload, MovedPayload, ErrorPayload
)

from handler.board import BoardHandler
from handler.cursor import CursorHandler
from handler.score import ScoreHandler

from data.board import Point, Tile
from data.cursor import Cursor
from config import MOVE_SCORE

from .utils import (
    multicast, watch, unwatch, get_view_range_points,
    publish_new_cursors, find_cursors_to_unwatch
)


class MovingReceiver():
    @EventBroker.add_receiver(EventCollection.MOVING)
    @staticmethod
    async def receive_moving(message: Message[MovingPayload]):
        cursor = CursorHandler.get_cursor(message.header["sender"])

        if (msg := await validate_new_position(cursor, message.payload.position)):
            await multicast(
                target_conns=[cursor.id],
                message=msg
            )
            return

        # 커서 위치 변경
        old_position = cursor.position
        cursor.position = message.payload.position
    
        original_watchers  = get_old_watchers(cursor)

        await multicast_moved(target_conns=original_watchers, cursor=cursor)
        await give_reward(cursor)
        
        # 새로운 위치를 바라보고 있는 커서들 찾기, 본인 제외
        new_watchers       = get_new_watchers(cursor, original_watchers)
        new_watchings      = get_new_cursors_on_sight(cursor, old_position)
        unwatching_cursors = pick_unwatching_cursors(cursor, original_watchers)
        cursors_to_unwatch = find_cursors_to_unwatch(cursor)

        # view 범위 들어온 watcher 추가
        watch(watchers=new_watchers, watchings=[cursor]) 
        watch(watchers=[cursor], watchings=new_watchings)
        # view 범위 벗어나면 watcher 제거
        unwatch(watchers=unwatching_cursors, watchings=[cursor])
        unwatch(watchers=[cursor], watchings=cursors_to_unwatch)

        await publish_new_cursors(target_cursors=new_watchers, cursors=[cursor])
        await publish_new_cursors(target_cursors=[cursor], cursors=new_watchings)



def get_new_cursors_on_sight(cursor:Cursor, old_position:Point):
    old_top_left, old_bottom_right = get_view_range_points(old_position, cursor.width, cursor.height)
    new_top_left, new_bottom_right = get_view_range_points(cursor.position, cursor.width, cursor.height)

    return CursorHandler.exists_range(
        start=new_top_left, end=new_bottom_right,
        exclude_start=old_top_left, exclude_end=old_bottom_right,
        exclude_ids=[cursor.id]
    )

async def give_reward(cursor:Cursor):
    await ScoreHandler.increase(cursor.id, MOVE_SCORE)

def pick_unwatching_cursors(cursor: Cursor, original_watchers:list[Cursor]):
    return [
        other_cursor
        for other_cursor in original_watchers
        if not other_cursor.check_in_view(cursor.position)
    ]

async def multicast_moved(target_conns: list[Cursor], cursor: Cursor):
    await multicast(
        target_conns=target_conns,
        message=Message(
            event=EventCollection.MOVED,
            payload=MovedPayload(
                id=cursor.id,
                new_position=cursor.position
            )
        )
    )

def get_new_watchers(cursor: Cursor, original_watchers: list[Cursor]) -> list[Cursor]:
    # 커서 위치 보고있는 커서 모두 가져오기
    cursors_watching_new_pos = CursorHandler.view_includes_point(p=cursor.position, exclude_ids=[cursor.id])
    # 이미 보고있던 커서는 필터링
    return list(filter(lambda c: c not in original_watchers, cursors_watching_new_pos))

def get_old_watchers(cursor:Cursor) -> list[Cursor]:
    watchers_id = CursorHandler.get_watchers_id(cursor_id=cursor.id)

    return [CursorHandler.get_cursor(id) for id in watchers_id]

async def validate_new_position(cursor: Cursor, new_position: Point) -> Message | None:
    is_moving_same_position = new_position == cursor.position
    if is_moving_same_position:
        return Message(
            event=EventCollection.ERROR,
            payload=ErrorPayload(msg="moving to current position is not allowed")
        )
    
    is_movable = cursor.check_interactable(new_position)
    if not is_movable:
        return Message(
            event=EventCollection.ERROR,
            payload=ErrorPayload(msg="only moving to 8 nearby tiles is allowed")
        )

    tiles = await BoardHandler.fetch(start=new_position, end=new_position)
    tile = Tile.from_int(tiles.data[0])
    if not tile.is_open:
        return Message(
            event=EventCollection.ERROR,
            payload=ErrorPayload(msg="moving to closed tile is not available")
        )
