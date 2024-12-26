import os

from dotenv import load_dotenv

if os.environ.get("ENV") != "prod":
    load_dotenv(".dev.env")


MINE_KILL_DURATION_SECONDS: int = int(os.environ.get("MINE_KILL_DURATION_SECONDS"))
BOARD_DATABASE_PATH: str = os.environ.get("BOARD_DATABASE_PATH")
