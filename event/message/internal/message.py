from typing import Generic, TypeVar
from event.payload import Payload
from data.payload import (
    EventCollection,
    FetchTilesPayload,
    TilesPayload,
    SendChatPayload,
    PointingPayload,
    MovingPayload,
    SetViewSizePayload
)
from .exceptions import InvalidEventTypeException

import json
from dataclasses import dataclass

EVENT_TYPE = TypeVar(
    "EVENT_TYPE",
    bound=Payload
)

DECODABLE_PAYLOAD_DICT: dict[str, Payload] = {
    EventCollection.FETCH_TILES: FetchTilesPayload,
    EventCollection.TILES: TilesPayload,
    EventCollection.POINTING: PointingPayload,
    EventCollection.MOVING: MovingPayload,
    EventCollection.SET_VIEW_SIZE: SetViewSizePayload,
    EventCollection.SEND_CHAT: SendChatPayload
}

@dataclass
class Message(Generic[EVENT_TYPE]):
    event: str
    payload: EVENT_TYPE
    header: dict[str, object]

    def __init__(
        self,
        event: str,
        payload: EVENT_TYPE,
        header: dict[str, object] = {}
    ):
        self.event = event
        self.payload = payload
        self.header = header
    
    def to_str(self, del_header: bool = True):
        data = self
        if del_header:
            data = Message(event=self.event, payload=self.payload)
            del data.header

        return json.dumps(
            data,
            default=lambda o: o.__dict__,
            sort_keys=True
        )

    @staticmethod
    def from_str(msg: str):
        decoded = json.loads(msg)

        event = decoded["event"]
        payload = decode_data(event, decoded["payload"])

        message = Message(event=event, payload=payload)
        if "header" in decoded:
            message.header = decoded["header"]

        return message


def decode_data(event: str, data: dict):
    """
    data를 Payload로 decode
    """
    if not event in DECODABLE_PAYLOAD_DICT:
        raise InvalidEventTypeException(event)

    return DECODABLE_PAYLOAD_DICT[event]._from_dict(data)
