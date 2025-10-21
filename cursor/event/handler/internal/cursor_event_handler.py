import asyncio
from data_layer.cursor import Cursor
from cursor.data.handler import CursorHandler
from data_layer.board import Point, Tile, Tiles, Section
from event import EventBroker
from message import Message
from datetime import datetime, timedelta
from message.payload import (
    MyCursorPayload,
    CursorsPayload,
    CursorInfoPayload,
    CursorReviveAtPayload,
    CursorsDiedPayload,
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
    ErrorPayload,
    NewCursorCandidatePayload,
    ChatEvent,
    ChatPayload,
    SendChatPayload,
    ScoreEvent,
    AddScorePayload,
    ScoreNotifyPayload
)
from config import Config

MINE_KILL_DURATION_SECONDS = Config.MINE_KILL_DURATION_SECONDS
VIEW_SIZE_LIMIT = Config.VIEW_SIZE_LIMIT
CHAT_MAX_LENGTH = Config.CHAT_MAX_LENGTH


class CursorEventHandler:
    @EventBroker.add_receiver(NewConnEvent.NEW_CURSOR_CANDIDATE)
    @staticmethod
    async def receive_new_cursor_candidate(message: Message[NewCursorCandidatePayload]):
        cursor = CursorHandler.create_cursor(
            conn_id=message.payload.conn_id,
            position=message.payload.position,
            width=message.payload.width, height=message.payload.height
        )

        publish_coroutines = []

        new_cursor_message = Message(
            event="multicast",
            header={"target_conns": [cursor.id],
                    "origin_event": NewConnEvent.MY_CURSOR},
            payload=MyCursorPayload(
                id=cursor.id,
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

        cursors_in_range = CursorHandler.exists_range(start=start_p, end=end_p, exclude_ids=[cursor.id])
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

        cursors_with_view_including = CursorHandler.view_includes_point(p=cursor.position, exclude_ids=[cursor.id])
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
            return

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

        # TODO: message.payload.pointable 사용처?
        cursor.pointer = message.payload.pointer

        watchers = CursorHandler.get_watchers(cursor.id)

        message = Message(
            event="multicast",
            header={
                "target_conns": [cursor.id] + watchers,
                "origin_event": PointEvent.POINTER_SET
            },
            payload=PointerSetPayload(
                id=cursor.id,
                pointer=cursor.pointer
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
            header={"sender": cursor.id},
            payload=CheckMovablePayload(
                position=new_position
            )
        )

        await EventBroker.publish(message)

        message = Message(
            event=ScoreEvent.ADD_SCORE,
            payload=AddScorePayload(
                cursor_id=sender,
                score=1
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
        cursors_in_view = CursorHandler.exists_range(start=top_left, end=bottom_right, exclude_ids=[cursor.id])

        original_watching_ids = CursorHandler.get_watching(cursor_id=cursor.id)
        original_watchings = [CursorHandler.get_cursor(id) for id in original_watching_ids]

        if len(original_watchings) > 0:
            # 범위 벗어난 커서들 연관관계 해제
            for other_cursor in original_watchings:
                in_view = cursor.check_in_view(other_cursor.position)
                if not in_view:
                    CursorHandler.remove_watcher(watcher=cursor, watching=other_cursor)

        publish_coroutines = []

        new_watchings = list(filter(lambda c: c.id not in original_watching_ids, cursors_in_view))
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
        watchers_new_pos = CursorHandler.view_includes_point(p=new_position, exclude_ids=[cursor.id])

        original_watcher_ids = CursorHandler.get_watchers(cursor_id=cursor.id)
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
                    id=cursor.id,
                    new_position=new_position
                )
            )

            publish_coroutines.append(EventBroker.publish(message))

            # 범위 벗어나면 watcher 제거
            for other_cursor in original_watchers:
                in_view = other_cursor.check_in_view(cursor.position)
                if not in_view:
                    CursorHandler.remove_watcher(watcher=other_cursor, watching=cursor)

        new_watchers = list(filter(lambda c: c.id not in original_watcher_ids, watchers_new_pos))
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
                    "target_conns": [c.id for c in view_cursors],
                    "origin_event": message.event
                },
                payload=message.payload
            )
            publish_coroutines.append(EventBroker.publish(pub_message))

        if not tile.is_mine:
            await asyncio.gather(*publish_coroutines)
            return

        # 주변 8칸 커서들 찾기
        start_p = Point(position.x - 1, position.y + 1)
        end_p = Point(position.x + 1, position.y - 1)

        nearby_cursors = CursorHandler.exists_range(start=start_p, end=end_p)
        # nearby_cursors 중 죽지 않은 커서들만 걸러내기
        nearby_cursors = list(filter(lambda c: c.revive_at is None, nearby_cursors))

        if len(nearby_cursors) > 0:
            revive_at = datetime.now() + timedelta(seconds=MINE_KILL_DURATION_SECONDS)

            # 범위 안 커서들에게 you-died
            pub_message = Message(
                event="multicast",
                header={
                    "target_conns": [c.id for c in nearby_cursors],
                    "origin_event": InteractionEvent.YOU_DIED
                },
                payload=YouDiedPayload(revive_at=revive_at.astimezone().isoformat())
            )
            publish_coroutines.append(EventBroker.publish(pub_message))

            # 보고있는 커서들에게 cursors-died
            watcher_ids: set[str] = set()
            for cursor in nearby_cursors:
                temp_watcher_ids = CursorHandler.get_watchers(cursor_id=cursor.id)
                watcher_ids.update(temp_watcher_ids + [cursor.id])

            pub_message = Message(
                event="multicast",
                header={
                    "target_conns": [id for id in watcher_ids],
                    "origin_event": InteractionEvent.CURSORS_DIED
                },
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
            publish_coroutines.append(EventBroker.publish(pub_message))

            # 영향 범위 커서들 죽이기
            for c in nearby_cursors:
                c.revive_at = revive_at
                c.pointer = None

        await asyncio.gather(*publish_coroutines)

    @staticmethod
    @EventBroker.add_receiver(InteractionEvent.TILES_OPENED)
    async def receive_tiles_opened(message: Message[TilesOpenedPayload]):
        start_p = message.payload.start_p
        end_p = message.payload.end_p

        # 변경된 타일을 보고있는 커서들에게 전달
        view_cursors = CursorHandler.view_includes_range(start=start_p, end=end_p)
        if len(view_cursors) > 0:
            pub_message = Message(
                event="multicast",
                header={
                    "target_conns": [c.id for c in view_cursors],
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
                    "target_conns": [c.id for c in view_cursors],
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

        watching = CursorHandler.get_watching(cursor_id=cursor.id)
        watchers = CursorHandler.get_watchers(cursor_id=cursor.id)

        for id in watching:
            other_cursor = CursorHandler.get_cursor(id)
            CursorHandler.remove_watcher(watcher=cursor, watching=other_cursor)

        for id in watchers:
            other_cursor = CursorHandler.get_cursor(id)
            CursorHandler.remove_watcher(watcher=other_cursor, watching=cursor)

        CursorHandler.remove_cursor(cursor.id)

        if len(watchers) > 0:
            message = Message(
                event="multicast",
                header={"target_conns": watchers,
                        "origin_event": NewConnEvent.CURSOR_QUIT},
                payload=CursorQuitPayload(
                    id=cursor.id
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

        if \
                new_width <= 0 or new_height <= 0 or \
                new_width > VIEW_SIZE_LIMIT or new_height > VIEW_SIZE_LIMIT:
            # 뷰 범위 한계 넘음
            await EventBroker.publish(Message(
                event="multicast",
                header={
                    "origin_event": ErrorEvent.ERROR,
                    "target_conns": [sender]
                },
                payload=ErrorPayload(msg=f"view width or height should be more than 0 and less than {VIEW_SIZE_LIMIT}")
            ))
            return

        cur_watching = CursorHandler.get_watching(cursor_id=cursor.id)

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

    @EventBroker.add_receiver(ChatEvent.SEND_CHAT)
    @staticmethod
    async def receive_send_chat(message: Message[SendChatPayload]):
        sender = message.header["sender"]

        content = message.payload.message

        if len(content) > CHAT_MAX_LENGTH:
            # 채팅 길이 제한 넘김
            await EventBroker.publish(Message(
                event="multicast",
                header={
                    "origin_event": ErrorEvent.ERROR,
                    "target_conns": [sender]
                },
                payload=ErrorPayload(msg=f"chat length limit exceeded. max length: {CHAT_MAX_LENGTH}")
            ))
            return

        watchers = CursorHandler.get_watchers(sender)

        message = Message(
            event="multicast",
            header={
                "origin_event": ChatEvent.CHAT,
                "target_conns": [sender] + watchers
            },
            payload=ChatPayload(
                cursor_id=sender,
                message=content
            )
        )

        await EventBroker.publish(message)

    @EventBroker.add_receiver(ScoreEvent.ADD_SCORE)
    @staticmethod
    async def receiver_add_score(message: Message[AddScorePayload]):
        cur_id = message.payload.cursor_id
        score = message.payload.score

        current_score = CursorHandler.add_score(cur_id, score)

        watchers = CursorHandler.get_watchers(cur_id)

        message = Message(
            event="multicast",
            header={"target_conns": [cur_id, *(cursor.id for cursor in watchers)],
                    "origin_event": ScoreEvent.SCORE_NOTIFY},
            payload=ScoreNotifyPayload(cur_id, score=current_score)
        )

        await EventBroker.publish(message)


async def publish_new_cursors_event(target_cursors: list[Cursor], cursors: list[Cursor]):
    message = Message(
        event="multicast",
        header={"target_conns": [cursor.id for cursor in target_cursors],
                "origin_event": NewConnEvent.CURSORS},
        payload=CursorsPayload(
            cursors=[CursorReviveAtPayload(
                id=cursor.id,
                position=cursor.position,
                pointer=cursor.pointer,
                color=cursor.color,
                revive_at=cursor.revive_at.astimezone().isoformat() if cursor.revive_at is not None else None
            ) for cursor in cursors]
        )
    )

    await EventBroker.publish(message)
