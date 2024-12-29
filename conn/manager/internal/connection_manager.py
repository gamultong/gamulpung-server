import asyncio
from fastapi.websockets import WebSocket
from conn import Conn
from message import Message
from message.payload import (
    NewConnEvent, NewConnPayload, ConnClosedPayload, DumbHumanException, ErrorEvent, ErrorPayload
)
from event import EventBroker
from uuid import uuid4

from config import MESSAGE_RATE_LIMIT
from limits import storage, strategies, parse


def overwrite_event(msg: Message):
    if "origin_event" not in msg.header:
        return

    msg.event = msg.header["origin_event"]
    del msg.header["origin_event"]


class ConnectionManager:
    conns: dict[str, Conn] = {}
    limiter = strategies.FixedWindowRateLimiter(storage.MemoryStorage())
    rate_limit = parse(MESSAGE_RATE_LIMIT)

    @staticmethod
    def get_conn(id: str):
        if id in ConnectionManager.conns:
            return ConnectionManager.conns[id]
        return None

    @staticmethod
    async def add(conn: WebSocket, width: int, height: int) -> Conn:
        id = ConnectionManager.generate_conn_id()

        conn_obj = Conn(id=id, conn=conn)
        await conn_obj.accept()
        ConnectionManager.conns[id] = conn_obj

        message = Message(
            event=NewConnEvent.NEW_CONN,
            payload=NewConnPayload(
                conn_id=id,
                height=height,
                width=width
            )
        )

        await EventBroker.publish(message)

        return conn_obj

    @staticmethod
    async def close(conn: Conn) -> Conn:
        ConnectionManager.conns.pop(conn.id)

        message = Message(
            event=NewConnEvent.CONN_CLOSED,
            header={"sender": conn.id},
            payload=ConnClosedPayload()
        )
        await EventBroker.publish(message)

    @staticmethod
    def generate_conn_id():
        while (id := uuid4().hex) in ConnectionManager.conns:
            pass
        return id

    @EventBroker.add_receiver("broadcast")
    @staticmethod
    async def receive_broadcast_event(message: Message):
        overwrite_event(message)

        coroutines = []

        for id in ConnectionManager.conns:
            conn = ConnectionManager.conns[id]
            coroutines.append(conn.send(message))

        await asyncio.gather(*coroutines)

    @EventBroker.add_receiver("multicast")
    @staticmethod
    async def receive_multicast_event(message: Message):
        overwrite_event(message)
        if "target_conns" not in message.header:
            raise DumbHumanException()

        coroutines = []

        for conn_id in message.header["target_conns"]:
            conn = ConnectionManager.get_conn(conn_id)
            if not conn:
                raise DumbHumanException()

            coroutines.append(conn.send(message))

        await asyncio.gather(*coroutines)

    @staticmethod
    async def publish_client_event(conn_id: str, msg: Message):
        # 커넥션 rate limit 확인
        ok = ConnectionManager._check_rate_limit(conn_id)

        if not ok:
            conn = ConnectionManager.get_conn(conn_id)
            await conn.send(msg=create_rate_limit_exceeded_message())
            return

        msg.header = {"sender": conn_id}
        await EventBroker.publish(msg)

    @staticmethod
    def _check_rate_limit(conn_id: str) -> bool:
        limit = ConnectionManager.rate_limit
        ok = ConnectionManager.limiter.hit(limit, conn_id)
        return ok


def create_rate_limit_exceeded_message() -> Message:
    return Message(
        event=ErrorEvent.ERROR,
        payload=ErrorPayload(msg=f"rate limit exceeded. limit: {MESSAGE_RATE_LIMIT}")
    )
