from .internal.cursor_handler import CursorHandler, CursorEvent


class CursorException:
    from .internal.cursor_exception import (
        AlreadyWatching,
        NoMatchingCursor,
        NotWatchable,
        NotWatching,
        NotFound,
        AlreadyExists,
        NotDead,
        CannotRevive,
        InvalidParameter,
        NotMovable,
        NotPointable,
        NotAlive
    )
