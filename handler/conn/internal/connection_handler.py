"""
join(WebSocket)
quit(id)

multycast(list[id], external_event)
broadcast(list[id], external_event)
"""
from data.conn.event import ServerEvent, ClientEvent
from .conn import Conn
from event.message import Message
from event.payload import ExternalEventPayload, DataPayload, EventEnum
from event.broker import EventBroker


class CursorEvent(EventEnum):
    JOIN = "JOIN"
    QUIT = "QUIT"


class ConnectionHandler:
    conn_dict: dict[str, Conn] = {}

    @staticmethod
    async def join(conn: Conn):
        ConnectionHandler.conn_dict[conn.id] = conn

        await EventBroker.publish(
            Message(
                event=CursorEvent.JOIN,
                payload=DataPayload(
                    conn.id, data=None
                )
            )
        )

    @staticmethod
    async def quit(conn: Conn):
        del ConnectionHandler.conn_dict[conn.id]

        await EventBroker.publish(
            Message(
                event=CursorEvent.QUIT,
                payload=DataPayload(
                    conn.id, data=None
                )
            )
        )

    @staticmethod
    async def publish_client_event(conn: Conn, event: ClientEvent.Base):
        await EventBroker.publish(
            Message(
                event=event.event_name,
                payload=DataPayload(
                    conn.id, data=event
                )
            )
        )

    @staticmethod
    async def multicast(target_ids: list[str], external_event: ServerEvent.Base):

        for id in target_ids:
            conn = ConnectionHandler.conn_dict[id]

            # TODO
            # Payload랑 External Message랑 호환이 안됨
            msg = Message(
                external_event.event_name,
                payload=ExternalEventPayload(
                    external_event
                )
            )
            await conn.send(msg)

    @staticmethod
    async def broadcast(external_event: ServerEvent.Base):
        pass
