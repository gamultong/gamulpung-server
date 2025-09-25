from event.broker import EventBroker
from event.message import Message

from event.payload import IdPayload
from data.cursor import Cursor

from handler.cursor import CursorEvent
from handler.score import ScoreHandler


class CreateScoreReceiver():
    @EventBroker.add_receiver(CursorEvent.CREATED)
    @EventBroker.add_receiver(CursorEvent.REVIVE)
    @staticmethod
    async def create_score(message: Message[IdPayload[str]]):
        id = message.payload.id

        _ = await ScoreHandler.create(id=id)
