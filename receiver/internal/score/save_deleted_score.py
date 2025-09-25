from utils.config import Config

from data.score import Score

from event.payload import IdDataPayload

from handler.score import ScoreHandler, ScoreEvent, ScoreNotFoundException
from handler.cursor import CursorHandler

from event.message import Message
from event.broker import EventBroker


class SaveDeletedScoreReceiver():
    @EventBroker.add_receiver(ScoreEvent.DELETED)
    @staticmethod
    async def save_deleted_score(message: Message[IdDataPayload[str, Score]]):
        pass
