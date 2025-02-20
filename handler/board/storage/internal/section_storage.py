from data.board import Point, Section
import asyncio

from aiosqlite import Connection
from db import use_db

TABLE_NAME = "sections"


@use_db
async def init_table(db: Connection):
    await db.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
        x INT NOT NULL,
        y INT NOT NULL,
        applied_flag INT NOT NULL,
        data BLOB NOT NULL
    )""")

    await db.execute(f"""
    CREATE UNIQUE INDEX IF NOT EXISTS x_y_idx ON {TABLE_NAME}(
        x, y
    )""")

asyncio.run(init_table())


class SectionStorage:
    @use_db
    async def get_random_sec_point(db: Connection) -> Point:
        """
        주의: 한개 이상의 섹션이 존재해야 함
        """
        row = None
        cur = await db.execute(f"SELECT x, y FROM {TABLE_NAME} ORDER BY RANDOM() LIMIT 1")
        row = await cur.fetchone()

        return Point(x=row[0], y=row[1])

    @use_db
    async def get(db: Connection, p: Point) -> Section | None:
        cur = await db.execute(
            f"SELECT applied_flag, data FROM {TABLE_NAME} WHERE x=:x AND y=:y",
            {"x": p.x, "y": p.y}
        )
        row = await cur.fetchone()

        if row is None:
            return None

        return Section(p=p, applied_flag=row[0], data=bytearray(row[1]))

    @use_db
    async def set(db: Connection, section: Section):
        await db.execute(
            f"""
            INSERT INTO {TABLE_NAME}(x, y, applied_flag, data)
            VALUES (:x, :y, :applied_flag, :data)
            ON CONFLICT(x, y) DO UPDATE SET data = :data, applied_flag = :applied_flag
            """,
            {
                "x": section.p.x,
                "y": section.p.y,
                "applied_flag": section.applied_flag,
                "data": section.data
            }
        )
