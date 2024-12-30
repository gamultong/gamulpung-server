from board.data import Point, Section
import asyncio
from db import db

TABLE_NAME = "sections"


async def init_table():
    await db.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
        x INT NOT NULL,
        y INT NOT NULL,
        data BLOB NOT NULL
    )""")

    await db.execute(f"""
    CREATE UNIQUE INDEX IF NOT EXISTS x_y_idx ON {TABLE_NAME}(
        x, y
    )""")

asyncio.run(init_table())


class SectionStorage:
    async def get_random_sec_point() -> Point:
        """
        주의: 한개 이상의 섹션이 존재해야 함
        """
        row = None
        cur = await db.execute(f"SELECT x, y FROM {TABLE_NAME} ORDER BY RANDOM() LIMIT 1")
        row = await cur.fetchone()

        return Point(x=row[0], y=row[1])

    async def get(p: Point) -> Section | None:
        row = None
        cur = await db.execute(
            f"SELECT data FROM {TABLE_NAME} WHERE x=:x AND y=:y",
            {"x": p.x, "y": p.y}
        )
        row = await cur.fetchone()

        if row is None:
            return None

        return Section(p=p, data=bytearray(row[0]))

    async def get_all() -> list[Section] | None:
        row = None
        cur = await db.execute(
            f"SELECT x, y, data FROM {TABLE_NAME}",
        )
        row = await cur.fetchall()

        if row is None:
            return None

        return [
            Section(p=Point(x, y), data=bytearray(data))
            for x, y, data in row
        ]

    async def set(section: Section):
        await db.execute(
            f"""
            INSERT INTO {TABLE_NAME}(x, y, data)
            VALUES (:x, :y, :data)
            ON CONFLICT(x, y) DO UPDATE SET data = :data
            """,
            {
                "x": section.p.x,
                "y": section.p.y,
                "data": section.data
            }
        )
