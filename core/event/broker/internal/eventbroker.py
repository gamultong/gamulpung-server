from typing import Callable, Type
from core.event.frame import Event, EventSet


class EventBroker:
    receiver_dict: dict[str, Callable] = {}

    @classmethod
    def add_receiver(cls, event: Type[Event]):
        def wrapper(func: Callable):
            cls.receiver_dict[event.name] = func
            return func
        return wrapper

    @classmethod
    async def publish(cls, event: Event):
        event_type = event.__class__
        receiver = cls.receiver_dict[event_type.name]
        await receiver(event)

    @classmethod
    async def set_external(cls, event_set):
        # TODO: Typing 및 구현
        return event_set
