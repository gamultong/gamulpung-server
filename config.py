import os

from dodoenv import load_dotenv, Env

if os.environ.get("ENV") != "prod":
    load_dotenv(".dev.env")


class Config:
    MINE_KILL_DURATION_SECONDS = Env[int](func=int)
    DATABASE_PATH = Env[str]()
    VIEW_SIZE_LIMIT = Env[int](func=int)
    MESSAGE_RATE_LIMIT = Env[str]()
    CHAT_MAX_LENGTH = Env[int](func=int)
