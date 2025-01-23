from typing import Generic, TypeVar
from event.payload import Payload
from data.payload import (
    EventEnum,
    FetchTilesPayload,
    TilesPayload,
    SendChatPayload,
    PointingPayload,
    MovingPayload,
    SetViewSizePayload
)
from .exceptions import InvalidEventTypeException

import json

EVENT_TYPE = TypeVar(
    "EVENT_TYPE",
    bound=Payload
)

DECODABLE_PAYLOAD_DICT: dict[str, Payload] = {
    EventEnum.FETCH_TILES: FetchTilesPayload,
    EventEnum.TILES: TilesPayload,
    EventEnum.POINTING: PointingPayload,
    EventEnum.MOVING: MovingPayload,
    EventEnum.SET_VIEW_SIZE: SetViewSizePayload,
    EventEnum.SEND_CHAT: SendChatPayload
}


class Message(Generic[EVENT_TYPE]):
    def __init__(self, event: str, payload: EVENT_TYPE, header: dict[str, object] = {}):
        self.event = event
        self.header = header
        self.payload = payload

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
