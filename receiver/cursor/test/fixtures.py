from data.board import Point
from data.cursor import Cursor, Color
from handler.cursor import CursorHandler


def setup_cursor_locations() -> tuple[Cursor]:
    """
    /docs/example/cursor-location.png

    A, B, C 차례로 반환
    """
    CursorHandler.cursor_dict = {
        "A": Cursor(
            conn_id="A",
            position=Point(-3, 3),
            pointer=None,
            height=6,
            width=6,
            color=Color.YELLOW
        ),
        "B": Cursor(
            conn_id="B",
            position=Point(-3, -4),
            pointer=None,
            height=7,
            width=7,
            color=Color.BLUE
        ),
        "C": Cursor(
            conn_id="C",
            position=Point(2, -1),
            pointer=None,
            height=4,
            width=4,
            color=Color.PURPLE
        )
    }

    cur_a = CursorHandler.cursor_dict["A"]
    cur_b = CursorHandler.cursor_dict["B"]
    cur_c = CursorHandler.cursor_dict["C"]

    CursorHandler.watchers = {}
    CursorHandler.watching = {}

    CursorHandler.add_watcher(watcher=cur_b, watching=cur_a)
    CursorHandler.add_watcher(watcher=cur_b, watching=cur_c)
    CursorHandler.add_watcher(watcher=cur_a, watching=cur_c)

    return (cur_a, cur_b, cur_c)
