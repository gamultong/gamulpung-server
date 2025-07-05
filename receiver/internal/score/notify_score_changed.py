from config import SCOREBOARD_SIZE

from data.score import Score

from data.payload import DataPayload

from handler.score import ScoreHandler, ScoreEvent, ScoreNotFoundException
from handler.cursor import CursorHandler

from event.message import Message
from event.broker import EventBroker
from .utils import broadcast_scoreboard_state


class NotifyScoreChangedReceiver():
    @EventBroker.add_receiver(ScoreEvent.CREATED)
    @EventBroker.add_receiver(ScoreEvent.DELETED)
    @EventBroker.add_receiver(ScoreEvent.UPDATED)
    @staticmethod
    async def notify_score_changed(message: Message[DataPayload[Score]]):
        old_score = message.payload.data

        cur_score = await get_current_score(message.payload.id)

        start, end = await get_rank_changed_range(old_score, cur_score)
        scores = await fetch_scoreboard(start, end)

        await broadcast_scoreboard_state(list(scores))


async def get_current_score(id: str):
    try:
        return await ScoreHandler.get(id)
    except ScoreNotFoundException:
        return None


async def fetch_scoreboard(start, end) -> tuple[Score]:
    if start > SCOREBOARD_SIZE:
        return tuple()
    end = min(end, SCOREBOARD_SIZE)

    scores = await ScoreHandler.get_by_rank(start, end)

    return scores


async def get_rank_changed_range(old: Score | None, new: Score | None) -> tuple[Score, Score]:
    if old is not None and new is not None:
        return sorted((old.rank, new.rank))

    length = await ScoreHandler.length()

    def rank_or_length(score: Score | None):
        if score is None:
            return length

        return score.rank

    start = rank_or_length(old)
    end = rank_or_length(new)

    return sorted((start, end))
