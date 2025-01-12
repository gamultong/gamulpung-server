from db import db


async def clear_records():
    await db.execute("DELETE FROM events")
