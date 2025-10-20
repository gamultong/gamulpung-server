from .internal.base import ValidationException


class ClientPayload:
    from .internal.base import ClientPayload as Base

    from .internal.client import (
        Chat,
        SetFlag,
        Pointing,
        Move,
        OpenTile,
        SetWindowSize
    )


class ServerPayload:
    from .internal.base import ServerPayload as Base

    from .internal.server import (
        Chat,
        CursorsState,
        Explosion,
        MyCursor,
        ScoreboardState,
        TilesState
    )
