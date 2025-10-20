from .base import Env

from datetime import timedelta
from dotenv import load_dotenv

load_dotenv(".dev.env")

class Config:
    MINE_KILL_DURATION_SECONDS = Env[timedelta](lambda s: timedelta(seconds=int(s)))

    DATABASE_PATH = Env[str]()
    WINDOW_SIZE_LIMIT = Env[int](int)

    MESSAGE_RATE_LIMIT = Env[str]()
    CHAT_MAX_LENGTH = Env[int](int)
    OPEN_TILE_SCORE = Env[int](int)
    SET_FLAG_SCORE = Env[int](int)
    CLEAR_FLAG_SCORE = Env[int](int)
    MOVE_SCORE = Env[int](int)

    MOVE_RANGE = Env[int](int)

    SCOREBOARD_SIZE = Env[int](int)
