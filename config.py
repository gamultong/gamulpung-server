import os

from dotenv import load_dotenv

if os.environ.get("ENV") != "prod":
    load_dotenv(".dev.env")


MINE_KILL_DURATION_SECONDS: int = int(os.environ.get("MINE_KILL_DURATION_SECONDS"))
DATABASE_PATH: str = os.environ.get("DATABASE_PATH")
VIEW_SIZE_LIMIT: int = int(os.environ.get("VIEW_SIZE_LIMIT"))
