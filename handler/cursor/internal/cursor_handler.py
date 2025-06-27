from data.base.utils import Relation
from data.board import Point, PointRange, overlaps
from data.cursor import Cursor, Color

from . import cursor_exception as CursorException

from event.payload import DumbHumanException
from event.broker import publish_data_event

from data.payload import EventEnum, DataPayload

from handler.storage.interface import KeyValueInterface, ListInterface
from handler.storage.dict import DictStorage
from handler.storage.list.array import ArrayListStorage
from data.payload import DataPayload
from event.broker import publish_data_event
from event.message import Message

from config import MOVE_RANGE

from datetime import datetime, timedelta
from typing import Callable


class CursorEvent(EventEnum):
    WINDOW_SIZE_SET = "Cursor.WINDOW_SIZE_SET"
    MOVED = "Cursor.MOVED"
    REVIVE = "Cursor.REVIVE"
    DEATH = "Cursor.DEATH"
    POINTING = "Cursor.POINTING"
    CREATED = "Cursor.CREATED"
    DELETE = "Cursor.DELETE"


class CursorHandler:
    __identify__: str = "Cursor"
    __event__: CursorEvent

    # 메인 스토리지
    cursor_storage: KeyValueInterface[str, Cursor] = DictStorage.create_space(
        key=__identify__ + ".cursor"
    )

    # 부가 스토리지
    # Handler <-1---N-> Space
    # Data    <-1---N-> Space
    watcher_storage: KeyValueInterface[str, Relation[str]] = DictStorage.create_space(
        key=__identify__ + ".watcher"
    )
    target_storage: KeyValueInterface[str, Relation[str]] = DictStorage.create_space(
        key=__identify__ + ".target"
    )

    @classmethod
    async def _add_watcher(cls, watcher: Cursor, target: Cursor):
        if not watcher.check_in_view(target.position):
            raise CursorException.NotWatchable()

        targets = await cls.target_storage.get(watcher.id) or Relation[str](_id=watcher.id)
        watchers = await cls.watcher_storage.get(target.id) or Relation[str](_id=target.id)

        if (target.id in targets.relations) or (watcher.id in watchers.relations):
            raise CursorException.AlreadyWatching

        targets.relations.append(target.id)
        watchers.relations.append(watcher.id)

        await cls.target_storage.set(watcher.id, targets)
        await cls.watcher_storage.set(target.id, watchers)

    @classmethod
    async def _remove_watcher(cls, watcher: Cursor, target: Cursor):
        targets = await cls.target_storage.get(watcher.id) or Relation[str](_id=watcher.id)
        watchers = await cls.watcher_storage.get(target.id) or Relation[str](_id=target.id)

        if not ((target.id in targets.relations) and (watcher.id in watchers.relations)):
            raise CursorException.NotWatching

        targets.relations.remove(target.id)
        watchers.relations.remove(watcher.id)

        await cls.target_storage.set(watcher.id, targets)
        await cls.watcher_storage.set(target.id, watchers)

    @classmethod  # argument가 id인 이유 -> get해서 최신 cursor 받아와야함
    async def revive(cls, id: str) -> Cursor:
        cursor = await cls.get(id)

        # vaildate
        if cursor.revive_at is None:
            raise CursorException.NotDead
        if cursor.revive_at > datetime.now():
            raise CursorException.CannotRevive

        cursor.revive_at = None
        await cls._update(cursor)

        await publish_data_event(CursorEvent.REVIVE, data=cursor)

        return cursor

    @classmethod
    async def set_window_size(cls, id: str, width: int, height: int):
        if width < 0 or height < 0:
            raise CursorException.InvalidParameter("width and height cannot be negative")

        cursor = await cls.get(id)
        prev_cur = cursor.copy()

        cursor.width, cursor.height = width, height

        await cls._update(cursor=cursor)

        old_t, cur_t = await cls._justify_targets(cursor=cursor)
        prev_cur, cursor = set_targets(prev_cur, old_t), set_targets(cursor, cur_t)

        await publish_data_event(CursorEvent.WINDOW_SIZE_SET, data=prev_cur)

        return cursor

    @classmethod
    async def move(cls, id: str, p: Point) -> Cursor:
        cursor = await cls.get(id)
        prev_cur = cursor.copy()

        movable_range = get_movable_range(cursor.position)
        if cursor.position == p or not movable_range.is_in(p):
            raise CursorException.NotMovable

        cursor.position = p

        await cls._update(cursor=cursor)

        old_t, cur_t = await cls._justify_targets(cursor)
        prev_cur, cursor = set_targets(prev_cur, old_t), set_targets(cursor, cur_t)

        old_w, cur_w = await cls._justify_watchers(cursor)
        prev_cur, cursor = set_watchers(prev_cur, old_w), set_watchers(cursor, cur_w)

        await publish_data_event(CursorEvent.MOVED, data=prev_cur)

        return cursor

    @classmethod
    async def set_pointer(cls, id: str, p: Point) -> Cursor:
        cursor = await cls.get(id)
        prev_cur = cursor.copy()

        if not cursor.check_in_view(p):
            raise CursorException.NotPointable

        cursor.pointer = p

        await cls._update(cursor=cursor)

        await publish_data_event(CursorEvent.POINTING, data=prev_cur)

        return cursor

    @classmethod
    async def kill(cls, id: str, duration: timedelta) -> Cursor:
        cursor = await cls.get(id)
        prev_cur = cursor.copy()

        # vaildate
        if cursor.revive_at is not None:
            raise CursorException.NotAlive

        now = datetime.now()

        cursor.revive_at = now + duration

        await cls._update(cursor=cursor)

        await publish_data_event(CursorEvent.DEATH, data=prev_cur)

        return cursor

    @classmethod
    async def _justify_watchers(cls, cursor: Cursor) -> tuple[list[Cursor], list[Cursor]]:
        old_watchers = await cls.get_watchers(cursor=cursor)
        current_watchers = await cls.get_by_watching_point(
            point=cursor.position,
            filters=[lambda c:c.id != cursor.id]
        )

        to_remove, _, to_add = diff_cursors(old_watchers, current_watchers)
        for other_cursor in to_remove:
            await cls._remove_watcher(watcher=other_cursor, target=cursor)
        for other_cursor in to_add:
            await cls._add_watcher(watcher=other_cursor, target=cursor)

        return old_watchers, current_watchers

    @classmethod
    async def _justify_targets(cls, cursor: Cursor) -> tuple[list[Cursor], list[Cursor]]:
        old_targets = await cls.get_targets(cursor=cursor)
        current_targets = await cls.get_by_range(
            range=cursor.view_range,
            filters=[lambda c: c.id != cursor.id]
        )

        to_remove, _, to_add = diff_cursors(old_targets, current_targets)
        for other_cursor in to_remove:
            await cls._remove_watcher(watcher=cursor, target=other_cursor)
        for other_cursor in to_add:
            await cls._add_watcher(watcher=cursor, target=other_cursor)

        return old_targets, current_targets

    @classmethod
    async def _update(cls, cursor: Cursor):
        """
        무조건 유효한 커서를 넘겨야 함. 
        """
        await cls.cursor_storage.set(key=cursor.id, value=cursor)

    @classmethod
    async def create(cls, template: Cursor) -> Cursor:
        existing = await cls.cursor_storage.get(template.id)
        if existing is not None:
            raise CursorException.AlreadyExists

        await cls.cursor_storage.set(template.id, template)

        await publish_data_event(CursorEvent.CREATED, id=template.id)

        return template.copy()

    @classmethod
    async def delete(cls, id: str) -> Cursor:
        cur = await cls.cursor_storage.get(id)
        if cur is None:
            raise CursorException.NotFound

        await cls.cursor_storage.delete(id)

        await publish_data_event(CursorEvent.DELETE, data=cur)

    @classmethod
    async def get(cls, id: str) -> Cursor:
        cur = await cls.cursor_storage.get(id)
        if cur is None:
            raise CursorException.NotFound

        return cur

    @classmethod
    async def get_by_range(cls, range: PointRange, filters: list[Callable[[Cursor], bool]] | None = None) -> list[Cursor]:
        result = []
        for id in await cls.cursor_storage.keys():
            cursor = await cls.cursor_storage.get(id)

            if not range.is_in(cursor.position):
                continue

            if filters is not None and not all(filter(cursor) for filter in filters):
                continue

            result.append(cursor)

        return result

    @classmethod
    async def get_by_point(cls, point: Point) -> list[Cursor]:
        return await cls.get_by_range(PointRange(point, point))

    @classmethod
    async def get_by_watching_range(cls, range: PointRange, filters: list[Callable[[Cursor], bool]] | None = None) -> list[Cursor]:
        result = []

        for id in await cls.cursor_storage.keys():
            cursor = await cls.cursor_storage.get(id)

            if not overlaps(cursor.view_range, range):
                continue

            if filters is not None and not all(filter(cursor) for filter in filters):
                continue

            result.append(cursor)

        return result

    @classmethod
    async def get_by_watching_point(cls, point: Point, filters: list[Callable[[Cursor], bool]] | None = None) -> list[Cursor]:
        return await cls.get_by_watching_range(PointRange(point, point), filters)

    @classmethod
    async def get_watchers(cls, cursor: Cursor) -> list[Cursor]:
        ids = await cls.watcher_storage.get(cursor.id)

        return [await cls.get(id) for id in ids]

    @classmethod
    async def get_targets(cls, cursor: Cursor) -> list[Cursor]:
        ids = await cls.target_storage.get(cursor.id)

        return [await cls.get(id) for id in ids]


def set_watchers(cursor: Cursor, watchers: list[Cursor]) -> Cursor[Cursor.Watchers]:
    cursor.sub[Cursor.Watchers] = Relation(_id=cursor.id, relations=[c.id for c in watchers])
    return cursor


def set_targets(cursor: Cursor, targets: list[Cursor]) -> Cursor[Cursor.Targets]:
    cursor.sub[Cursor.Targets] = Relation(_id=cursor.id, relations=[c.id for c in targets])
    return cursor


# return -> [a_only, both, b_only]
def diff_cursors(a_list: list[Cursor], b_list: list[Cursor]) -> tuple[list[Cursor]]:
    res = {cur.id: 1 for cur in a_list}
    res.update({cur.id: 1 for cur in b_list})

    cur_dict = {cur.id: cur for cur in a_list}
    cur_dict.update({cur.id: cur for cur in b_list})

    for cur in a_list:
        res[cur.id] -= 1
    for cur in b_list:
        res[cur.id] += 1

    result = [[], [], []]
    for id, idx in res.items():
        result[idx].append(cur_dict[id])

    return result


def get_movable_range(p: Point) -> PointRange:
    distance = MOVE_RANGE

    return PointRange.create_by_mid(p, width=distance, height=distance)


"""
method list
- create
- delete
- update -> 아예 update

WINDOW_SIZE_SET

move receiver에서 처리

WINDOW_SIZE_SET = "Cursor.WINDOW_SIZE_SET"
MOVED = "Cursor.MOVED"
DEATH = "Cursor.DEATH"
POINTING = "Cursor.POINTING"

move -> 따로
    cursor_storage
    watcher_storage
    watching_storage


내부 메서드
- add_relation(watcher, watching)
- remove_relation(watcher, watching)

- add_watcher
- remove_watcher
- add_watching -> watcher wrapper
- remove_watching -> watcher wrapper

-> 사용측에서 (모르고) 둘 다 쓰게 된다면?

-> 외부 접근 x
watcher_storage  
watching_storage
reason
    cursor_storage에서 carculate 완전 대채 가능 -> cache


    ======== 다음!!!!!!! =============
receiver test 만들고
receiver 구현 하면서 필요 method 구상
-> 이거 구현
"""
