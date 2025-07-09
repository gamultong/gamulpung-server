from config import SCOREBOARD_SIZE

from data.score import Score

from data.payload import DataPayload

from handler.score import ScoreHandler, ScoreEvent, ScoreNotFoundException
from handler.cursor import CursorHandler

from event.message import Message
from event.broker import EventBroker


class SaveDeletedScoreReceiver():
    @EventBroker.add_receiver(ScoreEvent.DELETED)
    @staticmethod
    async def save_deleted_score(message: Message[DataPayload[Score]]):
        pass
