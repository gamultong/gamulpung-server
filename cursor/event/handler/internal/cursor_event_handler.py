import asyncio
from cursor.data import Cursor
from cursor.data.handler import CursorHandler
from board.data import Point, Tile, Tiles
from event import EventBroker
from message import Message
from datetime import datetime, timedelta
from message.payload import (
    NewConnPayload,
    MyCursorPayload,
    CursorsPayload,
    CursorPayload,
    NewConnEvent,
    PointingPayload,
    TryPointingPayload,
    PointingResultPayload,
    PointerSetPayload,
    PointEvent,
    MoveEvent,
    MovingPayload,
    CheckMovablePayload,
    MovableResultPayload,
    MovedPayload,
    InteractionEvent,
    FlagSetPayload,
    SingleTileOpenedPayload,
    TilesOpenedPayload,
    YouDiedPayload,
    ConnClosedPayload,
    CursorQuitPayload,
    SetViewSizePayload,
    ErrorEvent,
    ErrorPayload
)


class CursorEventHandler:
    @EventBroker.add_receiver(NewConnEvent.NEW_CONN)
    @staticmethod
    async def receive_new_conn(message: Message[NewConnPayload]):
        cursor = CursorHandler.create_cursor(message.payload.conn_id)
        cursor.set_size(message.payload.width, message.payload.height)

        publish_coroutines = []

        new_cursor_message = Message(
            event="multicast",
            header={"target_conns": [cursor.conn_id],
                    "origin_event": NewConnEvent.MY_CURSOR},
            payload=MyCursorPayload(
                position=cursor.position,
                pointer=cursor.pointer,
                color=cursor.color
            )
        )

        publish_coroutines.append(EventBroker.publish(new_cursor_message))

        start_p = Point(
            x=cursor.position.x - cursor.width,
            y=cursor.position.y + cursor.height
        )
        end_p = Point(
            x=cursor.position.x + cursor.width,
            y=cursor.position.y - cursor.height
        )

        cursors_in_range = CursorHandler.exists_range(start=start_p, end=end_p, exclude_ids=[cursor.conn_id])
        if len(cursors_in_range) > 0:
            # 내가 보고있는 커서들
            for other_cursor in cursors_in_range:
                CursorHandler.add_watcher(watcher=cursor, watching=other_cursor)

            publish_coroutines.append(
                publish_new_cursors_event(
                    target_cursors=[cursor],
                    cursors=cursors_in_range
                )
            )

        cursors_with_view_including = CursorHandler.view_includes_point(p=cursor.position, exclude_ids=[cursor.conn_id])
        if len(cursors_with_view_including) > 0:
            # 나를 보고있는 커서들
            for other_cursor in cursors_with_view_including:
                CursorHandler.add_watcher(watcher=other_cursor, watching=cursor)

            publish_coroutines.append(
                publish_new_cursors_event(
                    target_cursors=cursors_with_view_including,
                    cursors=[cursor]
                )
            )

        await asyncio.gather(*publish_coroutines)

    @EventBroker.add_receiver(PointEvent.POINTING)
    @staticmethod
    async def receive_pointing(message: Message[PointingPayload]):
        sender = message.header["sender"]

        cursor = CursorHandler.get_cursor(sender)
        new_pointer = message.payload.position

        # 커서 부활시간 확인
        if cursor.revive_at is not None:
            if cursor.revive_at >= datetime.now():
                return
            cursor.revive_at = None

        # 뷰 바운더리 안에서 포인팅하는지 확인
        if not cursor.check_in_view(new_pointer):
            await EventBroker.publish(Message(
                event="multicast",
                header={
                    "origin_event": ErrorEvent.ERROR,
                    "target_conns": [sender]
                },
                payload=ErrorPayload(msg="pointer is out of cursor view")
            ))
            return

        message = Message(
            event=PointEvent.TRY_POINTING,
            header={"sender": sender},
            payload=TryPointingPayload(
                cursor_position=cursor.position,
                new_pointer=new_pointer,
                color=cursor.color,
                click_type=message.payload.click_type
            )
        )

        await EventBroker.publish(message)

    @EventBroker.add_receiver(PointEvent.POINTING_RESULT)
    @staticmethod
    async def receive_pointing_result(message: Message[PointingResultPayload]):
        receiver = message.header["receiver"]

        cursor = CursorHandler.get_cursor(receiver)

        new_pointer = message.payload.pointer if message.payload.pointable else None
        origin_pointer = cursor.pointer
        cursor.pointer = new_pointer

        if origin_pointer is None and new_pointer is None:
            # 변동 없음
            return

        watchers = CursorHandler.get_watchers(cursor.conn_id)

        message = Message(
            event="multicast",
            header={
                "target_conns": [cursor.conn_id] + watchers,
                "origin_event": PointEvent.POINTER_SET
            },
            payload=PointerSetPayload(
                origin_position=origin_pointer,
                new_position=new_pointer,
                color=cursor.color,
            )
        )

        await EventBroker.publish(message)

    @EventBroker.add_receiver(MoveEvent.MOVING)
    @staticmethod
    async def receive_moving(message: Message[MovingPayload]):
        sender = message.header["sender"]

        cursor = CursorHandler.get_cursor(sender)

        new_position = message.payload.position

        if new_position == cursor.position:
            await EventBroker.publish(Message(
                event="multicast",
                header={
                    "origin_event": ErrorEvent.ERROR,
                    "target_conns": [sender]
                },
                payload=ErrorPayload(msg="moving to current position is not allowed")
            ))
            return

        if not cursor.check_interactable(new_position):
            await EventBroker.publish(Message(
                event="multicast",
                header={
                    "origin_event": ErrorEvent.ERROR,
                    "target_conns": [sender]
                },
                payload=ErrorPayload(msg="only moving to 8 nearby tiles is allowed")
            ))
            return

        message = Message(
            event=MoveEvent.CHECK_MOVABLE,
            header={"sender": cursor.conn_id},
            payload=CheckMovablePayload(
                position=new_position
            )
        )

        await EventBroker.publish(message)

    @EventBroker.add_receiver(MoveEvent.MOVABLE_RESULT)
    @staticmethod
    async def receive_movable_result(message: Message[MovableResultPayload]):
        receiver = message.header["receiver"]

        cursor = CursorHandler.get_cursor(receiver)

        if not message.payload.movable:
            await EventBroker.publish(Message(
                event="multicast",
                header={
                    "origin_event": ErrorEvent.ERROR,
                    "target_conns": [receiver]
                },
                payload=ErrorPayload(msg="moving to given tile is not available")
            ))
            return

        new_position = message.payload.position
        original_position = cursor.position

        cursor.position = new_position

        # TODO: 새로운 방식으로 커서들 찾기. 최적화하기.

        # 새로운 뷰의 커서들 찾기
        top_left = Point(cursor.position.x - cursor.width, cursor.position.y + cursor.height)
        bottom_right = Point(cursor.position.x + cursor.width, cursor.position.y - cursor.height)
        cursors_in_view = CursorHandler.exists_range(start=top_left, end=bottom_right, exclude_ids=[cursor.conn_id])

        original_watching_ids = CursorHandler.get_watching(cursor_id=cursor.conn_id)
        original_watchings = [CursorHandler.get_cursor(id) for id in original_watching_ids]

        if len(original_watchings) > 0:
            # 범위 벗어난 커서들 연관관계 해제
            for watching in original_watchings:
                in_view = cursor.check_in_view(watching.position)
                if not in_view:
                    CursorHandler.remove_watcher(watcher=cursor, watching=other_cursor)

        publish_coroutines = []

        new_watchings = list(filter(lambda c: c.conn_id not in original_watching_ids, cursors_in_view))
        if len(new_watchings) > 0:
            # 새로운 watching 커서들 연관관계 설정
            for other_cursor in new_watchings:
                CursorHandler.add_watcher(watcher=cursor, watching=other_cursor)

            # 새로운 커서들 전달
            publish_coroutines.append(
                publish_new_cursors_event(
                    target_cursors=[cursor],
                    cursors=new_watchings
                )
            )

        # 새로운 위치를 바라보고 있는 커서들 찾기, 본인 제외
        watchers_new_pos = CursorHandler.view_includes_point(p=new_position, exclude_ids=[cursor.conn_id])

        original_watcher_ids = CursorHandler.get_watchers(cursor_id=cursor.conn_id)
        original_watchers = [CursorHandler.get_cursor(id) for id in original_watcher_ids]

        if len(original_watchers) > 0:
            # moved 이벤트 전달
            message = Message(
                event="multicast",
                header={
                    "target_conns": original_watcher_ids,
                    "origin_event": MoveEvent.MOVED,
                },
                payload=MovedPayload(
                    origin_position=original_position,
                    new_position=new_position,
                    color=cursor.color,
                )
            )

            publish_coroutines.append(EventBroker.publish(message))

            # 범위 벗어나면 watcher 제거
            for watcher in original_watchers:
                in_view = watcher.check_in_view(cursor.position)
                if not in_view:
                    CursorHandler.remove_watcher(watcher=watcher, watching=cursor)

        new_watchers = list(filter(lambda c: c.conn_id not in original_watcher_ids, watchers_new_pos))
        if len(new_watchers) > 0:
            # 새로운 watcher 커서들 연관관계 설정
            for other_cursor in new_watchers:
                CursorHandler.add_watcher(watcher=other_cursor, watching=cursor)

            # 새로운 커서들에게 본인 커서 전달
            publish_coroutines.append(
                publish_new_cursors_event(
                    target_cursors=new_watchers,
                    cursors=[cursor]
                )
            )

        await asyncio.gather(*publish_coroutines)

    @EventBroker.add_receiver(InteractionEvent.SINGLE_TILE_OPENED)
    @staticmethod
    async def receive_single_tile_opened(message: Message[SingleTileOpenedPayload]):
        position = message.payload.position
        tile_str = message.payload.tile

        tiles = Tiles(data=bytearray.fromhex(tile_str))
        tile = Tile.from_int(tiles.data[0])

        publish_coroutines = []

        # 변경된 타일을 보고있는 커서들에게 전달
        view_cursors = CursorHandler.view_includes_point(p=position)
        if len(view_cursors) > 0:
            pub_message = Message(
                event="multicast",
                header={
                    "target_conns": [c.conn_id for c in view_cursors],
                    "origin_event": message.event
                },
                payload=message.payload
            )
            publish_coroutines.append(EventBroker.publish(pub_message))

        if not tile.is_mine:
            await asyncio.gather(*publish_coroutines)
            return

        # 주변 8칸 커서들 죽이기
        start_p = Point(position.x - 1, position.y + 1)
        end_p = Point(position.x + 1, position.y - 1)

        nearby_cursors = CursorHandler.exists_range(start=start_p, end=end_p)
        if len(nearby_cursors) > 0:
            # TODO: 하드코딩 없애기
            revive_at = datetime.now() + timedelta(minutes=3)

            for c in nearby_cursors:
                c.revive_at = revive_at

            pub_message = Message(
                event="multicast",
                header={
                    "target_conns": [c.conn_id for c in nearby_cursors],
                    "origin_event": InteractionEvent.YOU_DIED
                },
                payload=YouDiedPayload(revive_at=revive_at.astimezone().isoformat())
            )
            publish_coroutines.append(EventBroker.publish(pub_message))

        await asyncio.gather(*publish_coroutines)

    @staticmethod
    async def receive_tiles_opened(message: Message[TilesOpenedPayload]):
        start_p = message.payload.start_p
        end_p = message.payload.end_p

        # 변경된 타일을 보고있는 커서들에게 전달
        view_cursors = CursorHandler.view_includes_range(start=start_p, end=end_p)
        if len(view_cursors) > 0:
            pub_message = Message(
                event="multicast",
                header={
                    "target_conns": [c.conn_id for c in view_cursors],
                    "origin_event": message.event
                },
                payload=message.payload
            )
            await EventBroker.publish(pub_message)

    @EventBroker.add_receiver(InteractionEvent.FLAG_SET)
    @staticmethod
    async def receive_flag_set(message: Message[FlagSetPayload]):
        position = message.payload.position

        # 변경된 타일을 보고있는 커서들에게 전달
        view_cursors = CursorHandler.view_includes_point(p=position)
        if len(view_cursors) > 0:
            pub_message = Message(
                event="multicast",
                header={
                    "target_conns": [c.conn_id for c in view_cursors],
                    "origin_event": message.event
                },
                payload=message.payload
            )
            await EventBroker.publish(pub_message)

    @EventBroker.add_receiver(NewConnEvent.CONN_CLOSED)
    @staticmethod
    async def receive_conn_closed(message: Message[ConnClosedPayload]):
        sender = message.header["sender"]

        cursor = CursorHandler.get_cursor(sender)

        watching = CursorHandler.get_watching(cursor_id=cursor.conn_id)
        watchers = CursorHandler.get_watchers(cursor_id=cursor.conn_id)

        for id in watching:
            other_cursor = CursorHandler.get_cursor(id)
            CursorHandler.remove_watcher(watcher=cursor, watching=other_cursor)

        for id in watchers:
            other_cursor = CursorHandler.get_cursor(id)
            CursorHandler.remove_watcher(watcher=other_cursor, watching=cursor)

        CursorHandler.remove_cursor(cursor.conn_id)

        message = Message(
            event="multicast",
            header={"target_conns": watchers,
                    "origin_event": NewConnEvent.CURSOR_QUIT},
            payload=CursorQuitPayload(
                position=cursor.position,
                pointer=cursor.pointer,
                color=cursor.color
            )
        )
        await EventBroker.publish(message)

    @EventBroker.add_receiver(NewConnEvent.SET_VIEW_SIZE)
    @staticmethod
    async def receive_set_view_size(message: Message[SetViewSizePayload]):
        sender = message.header["sender"]
        cursor = CursorHandler.get_cursor(sender)

        new_width, new_height = message.payload.width, message.payload.height

        if new_width == cursor.width and new_height == cursor.height:
            # 변동 없음
            return

        cur_watching = CursorHandler.get_watching(cursor_id=cursor.conn_id)

        old_width, old_height = cursor.width, cursor.height
        cursor.set_size(new_width, new_height)

        size_grown = (new_width > old_width) or (new_height > old_height)

        if size_grown:
            pos = cursor.position

            # 현재 범위
            old_top_left = Point(x=pos.x - old_width, y=pos.y + old_height)
            old_bottom_right = Point(x=pos.x + old_width, y=pos.y - old_height)

            # 새로운 범위
            new_top_left = Point(x=pos.x - new_width, y=pos.y + new_height)
            new_bottom_right = Point(x=pos.x + new_width, y=pos.y - new_height)

            # 현재 범위를 제외한 새로운 범위에서 커서들 가져오기
            new_watchings = CursorHandler.exists_range(
                start=new_top_left, end=new_bottom_right,
                exclude_start=old_top_left, exclude_end=old_bottom_right
            )

            if len(new_watchings) > 0:
                for other_cursor in new_watchings:
                    CursorHandler.add_watcher(watcher=cursor, watching=other_cursor)

                await publish_new_cursors_event(target_cursors=[cursor], cursors=new_watchings)

        for id in cur_watching:
            other_cursor = CursorHandler.get_cursor(id)
            if cursor.check_in_view(other_cursor.position):
                continue

            CursorHandler.remove_watcher(watcher=cursor, watching=other_cursor)


async def publish_new_cursors_event(target_cursors: list[Cursor], cursors: list[Cursor]):
    message = Message(
        event="multicast",
        header={"target_conns": [cursor.conn_id for cursor in target_cursors],
                "origin_event": NewConnEvent.CURSORS},
        payload=CursorsPayload(
            cursors=[CursorPayload(cursor.position, cursor.pointer, cursor.color) for cursor in cursors]
        )
    )

    await EventBroker.publish(message)
