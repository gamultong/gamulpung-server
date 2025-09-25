from typing import Generic, TypeVar, Type

from dataclasses import dataclass
from event.payload import Payload

from data.base import DataObj
from enum import Enum

DATA_TYPE = TypeVar(
    "DATA_TYPE",
    bound=DataObj
)
ID_TYPE = TypeVar(
    "ID_TYPE"
)


class _EventEnum:
    scope: str | None = None


class EventEnum(str, _EventEnum, Enum):
    pass


class Event():
    def __set_name__(self, owner: Type[EventEnum], name):
        assert issubclass(owner, EventEnum)
        self.event_name = name

    def __get__(self, instance, owner) -> str:
        assert issubclass(owner, EventEnum)
        if owner.scope is None:
            return self.event_name
        else:
            return f"{owner.scope}.{self.event_name}"


TYPE_EVENT_ENUM = TypeVar(
    "TYPE_EVENT_ENUM",
    bound=Type[EventEnum]
)


def set_scope(scope_name: str):
    def wrapper(event_enum: TYPE_EVENT_ENUM) -> TYPE_EVENT_ENUM:
        if event_enum.scope is None:
            event_enum.scope = scope_name
        else:
            event_enum.scope += f".{scope_name}"
        return event_enum
    return wrapper


@dataclass
class IdPayload(Generic[ID_TYPE], Payload):
    id: ID_TYPE


@dataclass
class IdDataPayload(Generic[ID_TYPE, DATA_TYPE], Payload):
    id: ID_TYPE
    data: DATA_TYPE


@dataclass
class ExternalEventPayload(Generic[DATA_TYPE], Payload):
    data: DATA_TYPE
