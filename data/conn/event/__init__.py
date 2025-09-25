from .internal.base import (
    Event,
    Empty,
    ValidationException,
    to_message,
    from_message,
    InvalidEventFormat
)


class ClientEvent:
    from .internal.base import ClientEvent as Base
    from .internal.client import (
        SetWindowSize,
        OpenTile,
        SetFlag,
        Move,
        Pointing,
        Chat
    )


class ServerEvent:
    from .internal.base import ServerEvent as Base
    from .internal.server import (
        Error,
        MyCursor,
        TilesState,
        CursorsState,
        ScoreboardState,
        Chat,
        Explosion
    )
