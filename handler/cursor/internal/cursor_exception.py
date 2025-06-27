from data.board import Point

# TODO: exception에 context 주기


class NotFound(Exception):
    pass


class AlreadyExists(Exception):
    pass


class NotDead(Exception):
    pass


class CannotRevive(Exception):
    pass


class AlreadyWatching(Exception):
    pass


class NoMatchingCursor(Exception):
    pass


class NotWatchable(Exception):
    pass


class NotWatching(Exception):
    pass


class NotMovable(Exception):
    pass


class NotPointable(Exception):
    pass


class NotAlive(Exception):
    pass


class InvalidParameter(Exception):
    def __init__(self, description: str):
        self.description = description

    def __str__(self):
        return self.description
