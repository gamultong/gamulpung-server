from event.broker import EventBroker
from event.message import Message
from event.payload import IdDataPayload

from data.cursor import Cursor
from data.board import Tiles, PointRange
from data.conn.event import ServerEvent

from handler.cursor import CursorEvent, CursorHandler, CursorException
from handler.board import BoardHandler
from handler.score import ScoreHandler

from ..utils import multicast


class NotifyWindowChangedReceiver():
    @EventBroker.add_receiver(CursorEvent.WINDOW_SIZE_SET)
    @EventBroker.add_receiver(CursorEvent.MOVED)
    @staticmethod
    async def notify_window_changed(message: Message[IdDataPayload[str, Cursor[Cursor.Targets]]]):
        cur_id = message.payload.id
        old_cur = message.payload.data

        assert old_cur is not None

        new_cur = await CursorHandler.get(cur_id)
        if is_omittable(old_cur, new_cur):
            return

        view_range = new_cur.view_range
        tiles = await fetch_delta_tiles(view_range)

        await multicast_tiles_state_event(target_conns=[new_cur], range=view_range, tiles_list=[tiles])

        new_targets = await get_new_targets(old_cur, new_cur)

        await multicast_cursor_state_event(target_conns=[new_cur], cursors=new_targets)


def is_omittable(old: Cursor, new: Cursor):
    if old.position != new.position:
        return False
    if old.width < new.width:
        return False
    if old.height < new.height:
        return False
    return True


async def multicast_cursor_state_event(target_conns: list[Cursor], cursors: list[Cursor]):
    elems = [
        ServerEvent.CursorsState.Elem(
            id=c.id,
            position=c.position,
            pointer=c.pointer,
            color=c.color,
            revive_at=c.revive_at,
            score=(await ScoreHandler.get(c.id)).value
        )
        for c in cursors
    ]

    event = ServerEvent.CursorsState(cursors=elems)

    await multicast(target_conns=[c.id for c in target_conns], event=event)


async def get_new_targets(old_cursor: Cursor[Cursor.Targets], new_cursor: Cursor) -> list[Cursor]:
    old_targets = old_cursor.sub[Cursor.Targets]

    # 현재 시야의 커서
    current_targets = await CursorHandler.get_targets(new_cursor)

    # 이전 상태의 커서들과 비교하여 새로운 커서를 찾기
    new_targets = filter_new_targets(old_targets, current_targets)
    return new_targets


def filter_new_targets(old_targets: Cursor.Targets, new_targets: list[Cursor]) -> list[Cursor]:
    def func(id): return id not in old_targets

    return list(filter(func, new_targets))


# TODO: 바뀐 부분만 fetch 할 수 있도록 인터페이스 변경.
async def fetch_delta_tiles(range: PointRange) -> Tiles:
    tiles = await BoardHandler.fetch(range)

    return tiles


# TODO: tiles가 position 정보를 가져야 함.
async def multicast_tiles_state_event(target_conns: list[Cursor], range: PointRange, tiles_list: list[Tiles]):
    elems = [
        ServerEvent.TilesState.Elem(
            range=range,
            data=tiles.to_str()
        ) for tiles in tiles_list
    ]

    event = ServerEvent.TilesState(tiles=elems)

    await multicast(target_conns=[c.id for c in target_conns], event=event)
