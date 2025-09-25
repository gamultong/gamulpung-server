from typing import Generic, TypeVar
from event.payload import Payload, Empty, ExternalEventPayload
from .exceptions import InvalidEventTypeException

import json
from dataclasses import dataclass

EVENT_TYPE = TypeVar(
    "EVENT_TYPE",
    bound=Payload
)


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

        def __parse(obj):
            return {
                key: item
                for key in obj.__dict__
                if (item := obj.__dict__[key]) is not Empty
            }

        return json.dumps(
            data,
            default=__parse,
            sort_keys=True
        )
