from event.broker import EventBroker
from event.message import Message

from event.payload import IdDataPayload
from data.cursor import Cursor
from data.score import Score
from data.conn.event import ServerEvent

from handler.cursor import CursorEvent
from handler.score import ScoreHandler

from ..utils import multicast


class CursorDeathReceiver():
    @EventBroker.add_receiver(CursorEvent.DEATH)
    @staticmethod
    async def cursor_death(message: Message[IdDataPayload[str, Cursor]]):
        cursor = message.payload.data
        assert cursor is not None

        score = await ScoreHandler.get(cursor.id)
        await move_to_persistent_scores(score)

        await reserve_revival(cursor)


async def move_to_persistent_scores(score: Score):
    # TODO: Persistent score storage.
    await ScoreHandler.delete(id=score.id)


async def reserve_revival(cursor: Cursor):
    # TODO: Create scheduler.
    pass
