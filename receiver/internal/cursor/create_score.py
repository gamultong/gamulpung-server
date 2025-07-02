from event.broker import EventBroker
from event.message import Message

from data.payload import DataPayload
from data.cursor import Cursor

from handler.cursor import CursorEvent
from handler.score import ScoreHandler


class CreateScoreReceiver():
    @EventBroker.add_receiver(CursorEvent.CREATED)
    @EventBroker.add_receiver(CursorEvent.REVIVE)
    @staticmethod
    async def rcreate_score(message: Message[DataPayload[Cursor]]):
        cursor = message.payload.data
        assert cursor is not None

        _ = await ScoreHandler.create(id=cursor.id)
