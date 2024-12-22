from board.data import Point
from cursor.data import Cursor, Color
from .cursor_exception import (
    AlreadyWatchingException,
    NoMatchingCursorException,
    NotWatchableException,
    NotWatchingException
)


class CursorHandler:
    cursor_dict: dict[str, Cursor] = {}

    watchers: dict[str, list[str]] = {}
    watching: dict[str, list[str]] = {}

    @staticmethod
    def create_cursor(conn_id: str):
        cursor = Cursor.create(conn_id)

        CursorHandler.cursor_dict[conn_id] = cursor

        return cursor

    @staticmethod
    def remove_cursor(conn_id: str):
        if conn_id in CursorHandler.cursor_dict:
            del CursorHandler.cursor_dict[conn_id]

    @staticmethod
    def get_cursor(conn_id: str) -> Cursor | None:
        if conn_id in CursorHandler.cursor_dict:
            return CursorHandler.cursor_dict[conn_id]

    # range 안에 커서가 있는가
    @staticmethod
    def exists_range(
        start: Point, end: Point, exclude_ids: list[str] = [],
        exclude_start: Point | None = None, exclude_end: Point | None = None
    ) -> list[Cursor]:
        result = []
        for cursor_id in CursorHandler.cursor_dict:
            if cursor_id in exclude_ids:
                continue

            cursor = CursorHandler.cursor_dict[cursor_id]
            pos = cursor.position
            # start & end 범위를 벗어나는가
            if \
                    start.x > pos.x or end.x < pos.x or \
                    end.y > pos.y or start.y < pos.y:
                continue

            # exclude_range 범위에 들어가는가
            if exclude_start is not None and exclude_end is not None:
                if \
                        pos.x >= exclude_start.x and pos.x <= exclude_end.x and \
                        pos.y >= exclude_end.y and pos.y <= exclude_start.y:
                    continue

            result.append(cursor)

        return result

    # 커서 view에 tile이 포함되는가
    @staticmethod
    def view_includes_point(p: Point, exclude_ids: list[str] = []) -> list[Cursor]:
        result = []
        for cursor_id in CursorHandler.cursor_dict:
            if cursor_id in exclude_ids:
                continue

            cursor = CursorHandler.cursor_dict[cursor_id]

            # 커서 뷰 범위를 벗어나는가
            if not cursor.check_in_view(p):
                continue

            result.append(cursor)

        return result

    # 커서 view에 range가 포함되는가
    @staticmethod
    def view_includes_range(start: Point, end: Point, exclude_ids: list[str] = []) -> list[Cursor]:
        result = []
        for cursor_id in CursorHandler.cursor_dict:
            if cursor_id in exclude_ids:
                continue

            cursor = CursorHandler.cursor_dict[cursor_id]

            left_top = Point(
                x=cursor.position.x - cursor.width,
                y=cursor.position.y + cursor.height
            )
            right_bottom = Point(
                x=cursor.position.x + cursor.width,
                y=cursor.position.y - cursor.height
            )

            # left_top이 end보다 오른쪽 혹은 아래인가
            if left_top.x > end.x or left_top.y < end.y:
                continue
            # right_bottom이 start 보다 왼쪽 혹은 위인가
            if right_bottom.x < start.x or right_bottom.y > start.y:
                continue

            result.append(cursor)

        return result

    @staticmethod
    def add_watcher(watcher: Cursor, watching: Cursor) -> None:
        watcher_id = watcher.conn_id
        watching_id = watching.conn_id

        watcher_exists = CursorHandler.check_cursor_exists(watcher_id)
        if not watcher_exists:
            raise NoMatchingCursorException(watcher_id)

        watching_exists = CursorHandler.check_cursor_exists(watching_id)
        if not watching_exists:
            raise NoMatchingCursorException(watching_id)

        if CursorHandler.check_cursor_watching(watching_id, watcher_id):
            raise AlreadyWatchingException(watcher=watcher_id, watching=watching_id)

        if not watcher.check_in_view(watching.position):
            raise NotWatchableException(p=watching.position, cursor_id=watcher.conn_id)

        if not watcher_id in CursorHandler.watching:
            CursorHandler.watching[watcher_id] = []
        CursorHandler.watching[watcher_id].append(watching_id)

        if not watching_id in CursorHandler.watchers:
            CursorHandler.watchers[watching_id] = []
        CursorHandler.watchers[watching_id].append(watcher_id)

    @staticmethod
    def remove_watcher(watcher: Cursor, watching: Cursor):
        watcher_id = watcher.conn_id
        watching_id = watching.conn_id

        watcher_exists = CursorHandler.check_cursor_exists(watcher_id)
        if not watcher_exists:
            raise NoMatchingCursorException(watcher_id)

        watching_exists = CursorHandler.check_cursor_exists(watching_id)
        if not watching_exists:
            raise NoMatchingCursorException(watching_id)

        if not CursorHandler.check_cursor_watching(watching_id, watcher_id):
            raise NotWatchingException(watcher=watcher_id, watching=watching_id)

        CursorHandler.watching[watcher_id].remove(watching_id)
        if len(CursorHandler.watching[watcher_id]) == 0:
            del CursorHandler.watching[watcher_id]

        CursorHandler.watchers[watching_id].remove(watcher_id)
        if len(CursorHandler.watchers[watching_id]) == 0:
            del CursorHandler.watchers[watching_id]

    @staticmethod
    def get_watchers(cursor_id: str) -> list[str]:
        if not CursorHandler.check_cursor_exists(cursor_id):
            raise NoMatchingCursorException(cursor_id)

        if cursor_id in CursorHandler.watchers:
            return CursorHandler.watchers[cursor_id].copy()

        return []

    @staticmethod
    def get_watching(cursor_id: str) -> list[str]:
        if not CursorHandler.check_cursor_exists(cursor_id):
            raise NoMatchingCursorException(cursor_id)

        if cursor_id in CursorHandler.watching:
            return CursorHandler.watching[cursor_id].copy()

        return []

    @staticmethod
    def check_cursor_exists(id: str):
        return id in CursorHandler.cursor_dict

    @staticmethod
    def check_cursor_watching(watching_id: str, watcher_id: str):
        """
        커서 watching 관계가 형성되어 있으면 True
        """
        watcher_rel = watching_id in CursorHandler.watchers
        watcher_rel = watcher_rel and watcher_id in CursorHandler.watchers[watching_id]

        watching_rel = watcher_id in CursorHandler.watching
        watching_rel = watching_rel and watching_id in CursorHandler.watching[watcher_id]

        return watcher_rel and watching_rel
