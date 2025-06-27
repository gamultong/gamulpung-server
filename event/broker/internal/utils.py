from .event_broker import EventBroker
from data.base import DataObj
from data.base.utils import HaveId
from data.payload import EventEnum, DataPayload
from event.message import Message
from event.payload import DumbHumanException

# TODO: 테스트


async def publish_data_event(event: EventEnum, data: HaveId | None = None, id: str | None = None):
    if not ((data is None) ^ (id is None)):
        raise DumbHumanException

    if data is not None:
        id = data.id

    message = Message(
        event=event,
        payload=DataPayload(id=id, data=data)
    )
    await EventBroker.publish(message=message)
