"""
join(WebSocket)
quit(id)

multycast(list[id], external_event)
broadcast(list[id], external_event)
"""
from data.conn.event import ServerEvent
from .conn import Conn
from event.message import Message
from event.payload import Payload


class ConnectionHandler:
    conn_dict: dict[str, Conn] = {}

    @staticmethod
    async def join()

    @staticmethod
    async def broadcast(target_ids: list[str], external_event: ServerEvent.Base):

        for id in target_ids:
            conn = ConnectionHandler.conn_dict[id]

            Message(
                external_event.event_name,
                Payload(

                )
            )
            await conn.send()
