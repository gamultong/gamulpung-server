"""
join(WebSocket)
quit(id)

multycast(list[id], external_event)
broadcast(list[id], external_event)
"""
from .conn import Conn
from event.message import Message
from event.payload import ExternalEventPayload, IdDataPayload, EventEnum, IdPayload, Event, set_scope

from core.event.frame import Event, EventSet, IdPayload, set_scope
from core.event.broker import EventBroker
from data.conn.external_event import ClientPayload, ServerPayload


@EventBroker.set_external
class ClientEvent(EventSet):
    OPEN_TILE = Event[ClientPayload.OpenTile]
    SET_FLAG = Event[ClientPayload.SetFlag]
    MOVE = Event[ClientPayload.Move]
    CHAT = Event[ClientPayload.Chat]
    POINTING = Event[ClientPayload.Pointing]
    SET_WINDOW_SIZE = Event[ClientPayload.SetWindowSize]


@EventBroker.set_external
class ServerEvent(EventSet):
    CHAT = Event[ServerPayload.Chat]
    CURSORS_STATE = Event[ServerPayload.CursorsState]
    EXPLOSION = Event[ServerPayload.Explosion]
    MY_CURSOR = Event[ServerPayload.MyCursor]
    SCOREBOARD_STATE = Event[ServerPayload.ScoreboardState]
    TILES_STATE = Event[ServerPayload.TilesState]


@set_scope("Connection")
class ConnectionEvent(EventSet):
    JOIN = Event[IdPayload]
    QUIT = Event[IdPayload]


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
