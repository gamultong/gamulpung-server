from event.broker import EventBroker
from event.message import Message

from data.payload import DataPayload
from data.cursor import Cursor
from data.board import Tiles
from data.conn.event import ServerEvent

from handler.cursor import CursorEvent, CursorHandler, CursorException
from handler.board import BoardHandler
from handler.score import ScoreHandler

from ..utils import multicast


def validate(old: Cursor, new: Cursor):
    if old.position != new.position:
        return True
    if old.width < new.width:
        return True
    if old.height < new.height:
        return True
    return False


class NotifyWindowChangedReceiver():
    @EventBroker.add_receiver(CursorEvent.WINDOW_SIZE_SET)
    @EventBroker.add_receiver(CursorEvent.MOVED)
    @staticmethod
    async def notify_window_changed(message: Message[DataPayload[Cursor[Cursor.Targets]]]):
        cur_id = message.payload.id

        old_cur = message.payload.data
        assert old_cur is not None
        old_targets = old_cur.sub[Cursor.Targets]

        new_cur = await CursorHandler.get(cur_id)
        if not validate(old_cur, new_cur):
            return

        # 변경해야함
        new_targets = await CursorHandler.get_targets(new_cur)

        new_targets = Cursor.Targets(
            _id=cur_id,
            relations=[cur.id for cur in new_targets]
        )

        tl = new_cur.view_range.top_left
        br = new_cur.view_range.bottom_right
        tiles = await BoardHandler.fetch(tl, br)

        tiles_state_event = make_tiles_state_event(new_cur, tiles)

        await multicast(
            target_conns=[cur_id],
            event=tiles_state_event
        )

        filtering_targets = filter_new_targets(old_targets, new_targets)
        if len(filtering_targets) == 0:
            return

        filtering_targets = [
            await CursorHandler.get(_cur_id)
            for _cur_id in filtering_targets
        ]

        event = await make_cursor_state_event(filtering_targets)
        await multicast(
            target_conns=[cur_id],
            event=event
        )


async def make_cursor_state_event(targets: list[Cursor]):
    event_elem_li = [
        ServerEvent.CursorsState.Elem(
            id=cur.id,
            position=cur.position,
            pointer=cur.pointer,
            color=cur.color,
            revive_at=cur.revive_at,
            score=(await ScoreHandler.get(cur.id)).value
        )
        for cur in targets
    ]

    event = ServerEvent.CursorsState(
        cursors=event_elem_li
    )

    return event


def filter_new_targets(old_targets: Cursor.Targets, new_targets: Cursor.Targets):
    def func(id): return id not in old_targets

    return Cursor.Targets(
        _id=new_targets.id,
        relations=[cur_id for cur_id in filter(func, new_targets)]
    )


def make_tiles_state_event(cursor: Cursor, tiles: Tiles):
    event_elem = ServerEvent.TilesState.Elem(
        range=cursor.view_range,
        data=tiles.to_str()
    )

    event = ServerEvent.TilesState(
        tiles=[event_elem]
    )

    return event
