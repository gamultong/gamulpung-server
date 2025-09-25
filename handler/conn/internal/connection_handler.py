"""
join(WebSocket)
quit(id)

multycast(list[id], external_event)
broadcast(list[id], external_event)
"""
from data.conn.event import ServerEvent, ClientEvent
from .conn import Conn
from event.message import Message
from event.payload import ExternalEventPayload, IdDataPayload, EventEnum, IdPayload, Event, set_scope
from event.broker import EventBroker


# @set_scope("Connection")
class ConnectionEvent(EventEnum):
    JOIN = Event()
    QUIT = Event()
    OPEN_TILE = Event()
    SET_FLAG = Event()
    MOVE = Event()
    CHAT = Event()
    POINTING = Event()
    SET_WINDOW_SIZE = Event()


class ConnectionHandler:
    conn_dict: dict[str, Conn] = {}

    @classmethod
    async def join(cls, conn: Conn):
        ConnectionHandler.conn_dict[conn.id] = conn

        await EventBroker.publish(
            Message(
                event=ConnectionEvent.JOIN,
                payload=IdPayload(
                    conn.id
                )
            )
        )

    @classmethod
    async def quit(cls, conn: Conn):
        del ConnectionHandler.conn_dict[conn.id]

        await EventBroker.publish(
            Message(
                event=ConnectionEvent.QUIT,
                payload=IdPayload(
                    conn.id
                )
            )
        )

    @classmethod
    async def publish_client_event(cls, conn: Conn, event: ClientEvent.Base):
        await EventBroker.publish(
            Message(
                event=event.event_name,
                payload=IdDataPayload(
                    conn.id, data=event
                )
            )
        )

    @classmethod
    async def multicast(cls, target_ids: list[str], external_event: ServerEvent.Base):

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

    @classmethod
    async def broadcast(cls, external_event: ServerEvent.Base):
        pass
