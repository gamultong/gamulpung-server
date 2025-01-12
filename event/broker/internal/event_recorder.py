from event.message import Message
from db import db
from datetime import datetime
import asyncio
import json

TABLE_NAME = "events"


async def init_table():
    await db.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
        event TEXT NOT NULL,
        timestamp FLOAT NOT NULL,
        header TEXT NOT NULL,
        payload TEXT NOT NULL
    )""")

asyncio.run(init_table())


class EventRecorder:
    async def record(timestamp: datetime, msg: Message):
        header = json.dumps(obj=msg.header, sort_keys=True)
        payload = json.dumps(obj=msg.payload, default=lambda o: o.__dict__, sort_keys=True)

        await db.execute(
            f"""
                INSERT INTO {TABLE_NAME} (event, timestamp, header, payload)
                VALUES (:event, :timestamp, :header, :payload)
            """,
            {
                "event": msg.event,
                "timestamp": timestamp.timestamp(),
                "header": header,
                "payload": payload
            }
        )
