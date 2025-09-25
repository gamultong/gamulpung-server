class ScoreReceiver:
    from .internal.score.notify_score_changed import NotifyScoreChangedReceiver
    from .internal.score.save_deleted_score import SaveDeletedScoreReceiver
    from .internal.score.send_initial_scoreboard import SendInitialScoreboardReceiver


class CursorReceiver:
    from .internal.cursor.create_score import CreateScoreReceiver
    from .internal.cursor.cursor_delete import DeleteCursorReceiver
    from .internal.cursor.death import CursorDeathReceiver
    from .internal.cursor.notify_cursor_state_changed import NotifyCursorStateChangedReceiver
    from .internal.cursor.notify_my_cursor import NotifyMyCursorReceiver
    from .internal.cursor.notify_window_changed import NotifyWindowChangedReceiver


class ExternalRecevier:
    from .internal.external.chat import ChatExternalReceiver
    from .internal.external.move import MoveExternalReceiver
    from .internal.external.new import NewExternalReceiver
    from .internal.external.open_tile import OpenTileExternalReceiver
    from .internal.external.pointing import PointingExternalReceiver
    from .internal.external.quit import QuitExternalReceiver
    from .internal.external.set_flag import SetFlagExternalReceiver
    from .internal.external.set_window_size import SetWindowSizeExternalReceiver


class BoardRecever:
    from .internal.board.explosion import ExplosionReceiver
    from .internal.board. notify_board_changed import NotifyBoardChangedReceiver
