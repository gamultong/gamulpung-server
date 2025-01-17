import asyncio
from aiosqlite import connect
from config import DATABASE_PATH

db = None


async def do_connect():
    global db
    db = await connect(
        database=DATABASE_PATH,
        isolation_level=None  # AUTOCOMMIT
    )

asyncio.run(do_connect())
