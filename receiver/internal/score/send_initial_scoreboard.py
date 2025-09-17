from config import SCOREBOARD_SIZE

from data.cursor import Cursor
from data.score import Score

from data.payload import DataPayload

from handler.score import ScoreHandler, ScoreEvent, ScoreNotFoundException
from handler.cursor import CursorHandler

from event.message import Message
from event.broker import EventBroker

from .utils import multicast_scoreboard_state


class SendInitialScoreboardReceiver():
    @EventBroker.add_receiver(ScoreEvent.CREATED)
    @staticmethod
    async def send_initial_scoreboard(message: Message[DataPayload[Score]]):
        cursor = await CursorHandler.get(message.payload.id)

        await deliver_whole_scoreboard(cursor)


async def deliver_whole_scoreboard(cursor: Cursor):
    length = min(SCOREBOARD_SIZE, await ScoreHandler.length())

    scores = await ScoreHandler.get_by_rank(start=1, end=length)

    await multicast_scoreboard_state(target_conns=[cursor], scores=scores)
