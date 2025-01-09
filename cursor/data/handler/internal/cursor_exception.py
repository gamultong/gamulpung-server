from data_layer.board import Point


class AlreadyWatchingException(Exception):
    def __init__(self, watcher: str, watching: str):
        self.watcher = watcher
        self.watchin = watching

    def __str__(self):
        return f"cursor {self.watcher} is already watching {self.watching}"


class NoMatchingCursorException(Exception):
    def __init__(self, cursor_id: str):
        self.cursor_id = cursor_id

    def __str__(self):
        return f"no matching cursor with id: {self.cursor_id}"


class NotWatchableException(Exception):
    def __init__(self, p: Point, cursor_id: str):
        self.p = p
        self.cursor_id = cursor_id

    def __str__(self):
        return f"position: ({self.p.x}, {self.p.y}) is not watchable to cursor: {self.cursor_id}"


class NotWatchingException(Exception):
    def __init__(self, watcher: str, watching: str):
        self.watcher = watcher
        self.watchin = watching

    def __str__(self):
        return f"cursor {self.watcher} is not watching {self.watching}"
