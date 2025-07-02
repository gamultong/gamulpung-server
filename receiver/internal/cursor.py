from event.broker import EventBroker
from event.message import Message

from data.payload import DataPayload
from data.cursor import Cursor
from data.score import Score
from data.conn.event import ServerEvent

from handler.cursor import CursorEvent
from handler.score import ScoreHandler

from .utils import multicast


class CursorReceiver():
    @EventBroker.add_receiver(CursorEvent.CREATED)
    @staticmethod
    async def cursor_created(message: Message[DataPayload[Cursor]]):
        cursor = message.payload.data
        assert cursor is not None

        await ScoreHandler.create(id=cursor.id)

        await multicast_my_cursor(cursor)

    @EventBroker.add_receiver(CursorEvent.DEATH)
    @staticmethod
    async def cursor_death(message: Message[DataPayload[Cursor]]):
        cursor = message.payload.data
        assert cursor is not None

        score = await ScoreHandler.get(cursor.id)
        await move_to_persistent_scores(score)

        await reserve_revival(cursor)


async def multicast_my_cursor(cursor: Cursor):
    event = ServerEvent.MyCursor(id=cursor.id)

    await multicast(target_conns=[cursor.conn_id], event=event)


async def move_to_persistent_scores(score: Score):
    # TODO: Persistent score storage.
    await ScoreHandler.delete(id=score.id)


async def reserve_revival(cursor: Cursor):
    # TODO: Create scheduler.
    pass
