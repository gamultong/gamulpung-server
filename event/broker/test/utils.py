from db import get_db


async def clear_records():
    db = await get_db()
    await db.execute("DELETE FROM events")
    await db.close()
