from aiosqlite import connect, Connection
from utils.config import Config


def use_db(func):
    async def wrapper(*args, **kwargs):
        try:
            db = await get_db()
            return await func(db, *args, **kwargs)
        finally:
            await db.close()

    return wrapper


async def get_db() -> Connection:
    return await connect(
        database=Config.DATABASE_PATH,
        isolation_level=None  # AUTOCOMMIT
    )
