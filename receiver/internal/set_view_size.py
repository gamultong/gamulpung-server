from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventEnum, SetViewSizePayload, ErrorPayload
)

from handler.cursor import CursorHandler

from data.cursor import Cursor

from config import VIEW_SIZE_LIMIT

from .utils import (
    multicast, watch, unwatch, get_view_range_points,
    publish_new_cursors, find_cursors_to_unwatch
)


class SetViewSizeReceiver():
    @EventBroker.add_receiver(EventEnum.SET_VIEW_SIZE)
    @staticmethod
    async def receive_set_view_size(message: Message[SetViewSizePayload]):
        sender = message.header["sender"]
        cursor = CursorHandler.get_cursor(sender)

        new_width, new_height = message.payload.width, message.payload.height

        if (msg := validate_view_size(cursor, new_height, new_height)):
            await multicast(
                target_conns=[sender],
                message=msg
            )
            return

        old_width, old_height = cursor.width, cursor.height
        cursor.set_size(new_width, new_height)

        size_grown = (new_width > old_width) or (new_height > old_height)

        if size_grown:
            old_top_left, old_bottom_right = get_view_range_points(cursor.position, old_width, old_height)
            new_top_left, new_bottom_right = get_view_range_points(cursor.position, new_width, new_height)

            # 현재 범위를 제외한 새로운 범위에서 커서들 가져오기
            new_watchings = CursorHandler.exists_range(
                start=new_top_left, end=new_bottom_right,
                exclude_start=old_top_left, exclude_end=old_bottom_right
            )

            if len(new_watchings) > 0:
                watch(watchers=[sender], watchings=new_watchings)

                await publish_new_cursors(target_cursors=[cursor], cursors=new_watchings)

        cursors_to_unwatch = find_cursors_to_unwatch(cursor)
        if len(cursors_to_unwatch) > 0:
            unwatch(watchers=[sender], watching=cursors_to_unwatch)


def validate_view_size(cursor: Cursor, new_width: int, new_height: int):
    if new_width == cursor.width and new_height == cursor.height:
        # 변동 없음
        return Message(
            event=EventEnum.ERROR,
            payload=ErrorPayload(msg=f"view size is same as current size")
        )

    if new_width <= 0 or new_height <= 0 or \
            new_width > VIEW_SIZE_LIMIT or new_height > VIEW_SIZE_LIMIT:
        # 뷰 범위 한계 넘음
        return Message(
            event=EventEnum.ERROR,
            payload=ErrorPayload(msg=f"view width or height should be more than 0 and less than {VIEW_SIZE_LIMIT}")
        )
