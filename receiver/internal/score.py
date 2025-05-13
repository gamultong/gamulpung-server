from config import SCOREBOARD_SIZE

from data.cursor import Cursor
from data.score import Score
from data.payload import (
    EventCollection,
    DataPayload
)

from data.conn.event import (
    ServerEvent
)

from handler.score import ScoreHandler, ScoreEvent, ScoreNotFoundException
from handler.cursor import CursorHandler

from event.message import Message
from event.broker import EventBroker
from event.payload import Empty

from .utils import multicast, broadcast


class ScoreReceiver():
    @EventBroker.add_receiver(ScoreEvent.CREATED)
    @EventBroker.add_receiver(ScoreEvent.DELETED)
    @EventBroker.add_receiver(ScoreEvent.UPDATED)
    @staticmethod
    async def notify_score_changed(message: Message[DataPayload[Score]]):
        old_score = message.payload.data

        cur_score = await get_current_score(message.payload.id)

        start, end = await get_rank_changed_range(old_score, cur_score)
        scores = await fetch_scoreboard(start, end)

        await broadcast_scoreboard_state(scores)

    @EventBroker.add_receiver(ScoreEvent.CREATED)
    @staticmethod
    async def score_created_initial_board(message: Message[DataPayload[Score]]):
        cursor = CursorHandler.get_cursor(message.payload.id)

        await deliver_whole_scoreboard(cursor)

    @EventBroker.add_receiver(ScoreEvent.DELETED)
    @staticmethod
    async def save_deleted_score(message: Message[DataPayload[Score]]):
        pass


async def get_current_score(id: str):
    try:
        return await ScoreHandler.get_by_id(id)
    except ScoreNotFoundException:
        return None


async def deliver_whole_scoreboard(cursor: Cursor):
    length = min(SCOREBOARD_SIZE, await ScoreHandler.length())

    scores = await ScoreHandler.get_by_rank(start=1, end=length)

    await multicast_scoreboard_state(
        target_conns=[cursor], scores=scores
    )


def create_scoreboard_state_message(scores: list[Score]):
    score_elements = [
        ServerEvent.ScoreboardState.Elem(rank=score.rank, score=score.value, before_rank=Empty)
        for score in scores
    ]

    payload = ServerEvent.ScoreboardState(scores=score_elements)
    return Message(
        event=EventCollection.SCOREBOARD_STATE,
        payload=payload
    )


async def multicast_scoreboard_state(target_conns: list[Cursor], scores: list[Score]):
    await multicast(
        target_conns=[c.id for c in target_conns],
        message=create_scoreboard_state_message(scores)
    )


async def broadcast_scoreboard_state(scores: list[Score]):
    await broadcast(
        message=create_scoreboard_state_message(scores)
    )


async def fetch_scoreboard(start, end):
    if start > SCOREBOARD_SIZE:
        return []
    end = min(end, SCOREBOARD_SIZE)
    return await ScoreHandler.get_by_rank(start, end)


async def get_rank_changed_range(old: Score | None, new: Score | None):
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
