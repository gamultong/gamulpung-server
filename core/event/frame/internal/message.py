from .payload import Payload, ExternalPayload
from .event import Event, EventSet
from typing import TypeVar, Generic, ClassVar, Type
from json import loads

EVENT_TYPE = TypeVar("EVENT_TYPE", bound=Event)
EVENTSET_TYPE = TypeVar("EVENTSET_TYPE", bound=EventSet)

EXTERNAL_SCOPE = "External"


class Message(Generic[EVENT_TYPE]):
    """EventBroker가 통신에 사용할 통신단위(Frame)"""
    _external_event_sets: ClassVar[list[EventSet]] = []
    _external_events_dict: ClassVar[dict[str, Type[Event[ExternalPayload]]]] = {}

    def __init__(self, event: EVENT_TYPE):
        self.event: EVENT_TYPE = event

    def to_dict(self):
        """Message를 dict으로 변환"""
        return {
            "header": {
                "event": self.event.name
            },
            "payload": self.event.payload
        }

    @staticmethod
    def parsing_external_to_interanl(event_name: str):
        """External Event 이름을 Internal Event Convention에 맞춤"""
        res = event_name.replace("-", "_")
        return f"{EXTERNAL_SCOPE}.{res}"

    @staticmethod
    def parsing_interanl_to_external(event_name: str):
        """Internal Event 이름을 External Event Convention에 맞춤"""
        scope, name = event_name.split(".")
        assert scope == EXTERNAL_SCOPE

        return name.replace("_", "-")

    @classmethod
    def external_scope(cls, event_set: EVENTSET_TYPE):
        """EventSet의 scope를 External로 맞춤"""
        cls._external_event_sets.append(event_set)
        event_set.set_scope(EXTERNAL_SCOPE)

        cls._external_events_dict.update(
            event_set.events()
        )
        return event_set

    @classmethod
    def from_str(cls, str: str):
        """문자열을 Message로 변경"""
        json = loads(str)

        header = json["header"]
        event_name = header["event"]
        event_name = cls.parsing_external_to_interanl(event_name)

        payload = json["payload"]

        event_type = cls._external_events_dict[event_name]
        payload_obj = event_type.payload_type.from_dict(payload)

        event = event_type(
            payload=payload_obj
        )

        return Message(
            event=event
        )
