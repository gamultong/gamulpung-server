import os

from dotenv import load_dotenv

if os.environ.get("ENV") != "prod":
    load_dotenv(".dev.env")


MINE_KILL_DURATION_SECONDS = int(os.environ.get("MINE_KILL_DURATION_SECONDS"))
DATABASE_PATH = os.environ.get("DATABASE_PATH")

WINDOW_SIZE_LIMIT = int(os.environ.get("WINDOW_SIZE_LIMIT"))

MESSAGE_RATE_LIMIT = os.environ.get("MESSAGE_RATE_LIMIT")
CHAT_MAX_LENGTH = int(os.environ.get("CHAT_MAX_LENGTH"))
OPEN_TILE_SCORE = int(os.environ.get("OPEN_TILE_SCORE"))
SET_FLAG_SCORE = int(os.environ.get("SET_FLAG_SCORE"))
MOVE_SCORE = int(os.environ.get("MOVE_SCORE"))

MOVE_RANGE = int(os.environ.get("MOVE_RANGE"))

SCOREBOARD_SIZE = int(os.environ.get("SCOREBOARD_SIZE"))
