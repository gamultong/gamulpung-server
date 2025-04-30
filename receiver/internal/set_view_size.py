from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, SetViewSizePayload, ErrorPayload
)

from handler.cursor import CursorHandler

from data.cursor import Cursor
from data.board import PointRange

from config import WINDOW_SIZE_LIMIT

from .utils import (
    multicast, watch, unwatch, get_view_range_points,
    publish_new_cursors, find_cursors_to_unwatch
)

class SetViewSizeReceiver():
    @EventBroker.add_receiver(EventCollection.SET_VIEW_SIZE)
    @staticmethod
    async def receive_set_view_size(message: Message[SetViewSizePayload]):
        cursor = CursorHandler.get_cursor(message.header["sender"])

        new_width, new_height = message.payload.width, message.payload.height

        if (msg := validate_view_size(cursor, new_height, new_height)):
            await multicast(
                target_conns=[cursor.id],
                message=msg
            )
            return

        
        old_width, old_height = cursor.width, cursor.height
        cursor.set_size(new_width, new_height)
        
        new_watchings = find_new_watchings(cursor, old_width, old_height)
        if len(new_watchings) > 0:
            watch(watchers=[cursor.id], watchings=new_watchings)

            await publish_new_cursors(target_cursors=[cursor], cursors=new_watchings)

        cursors_to_unwatch = find_cursors_to_unwatch(cursor)
        if len(cursors_to_unwatch) > 0:
            unwatch(watchers=[cursor.id], watchings=cursors_to_unwatch)

def validate_view_size(cursor: Cursor, new_width: int, new_height: int):
    is_not_changed = (new_width == cursor.width and new_height == cursor.height)
    if is_not_changed:
        # 변동 없음
        return Message(
            event=EventCollection.ERROR,
            payload=ErrorPayload(msg=f"view size is same as current size")
        )

    is_over_view_limit = new_width <= 0 or \
                         new_height <= 0 or \
                         new_width > WINDOW_SIZE_LIMIT or \
                         new_height > WINDOW_SIZE_LIMIT
    if is_over_view_limit:
        # 뷰 범위 한계 넘음
        return Message(
            event=EventCollection.ERROR,
            payload=ErrorPayload(msg=f"view width or height should be more than 0 and less than {WINDOW_SIZE_LIMIT}")
        )


def find_new_watchings(cursor: Cursor, old_width: int, old_height: int) -> list[Cursor]:
    is_grown = (cursor.width > old_width) or (cursor.height > old_height)

    if not is_grown:
        return []

    old_top_left, old_bottom_right = get_view_range_points(cursor.position, old_width, old_height)
    new_top_left, new_bottom_right = get_view_range_points(cursor.position, cursor.width, cursor.height)

    # 현재 범위를 제외한 새로운 범위에서 커서들 가져오기
    return CursorHandler.exists_range(
        start=new_top_left, end=new_bottom_right,
        exclude_start=old_top_left, exclude_end=old_bottom_right
    )
