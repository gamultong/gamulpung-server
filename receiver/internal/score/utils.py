from data.cursor import Cursor
from data.score import Score
from data.conn.event import ServerEvent, Empty

from ..utils import multicast, broadcast


async def multicast_scoreboard_state(target_conns: list[Cursor], scores: list[Score]):
    await multicast(
        target_conns=[c.id for c in target_conns],
        event=create_scoreboard_state_message(scores)
    )


async def broadcast_scoreboard_state(scores: list[Score]):
    await broadcast(
        event=create_scoreboard_state_message(scores)
    )


def create_scoreboard_state_message(scores: list[Score]):
    event = ServerEvent.ScoreboardState

    score_elements = [
        event.Elem(rank=score.rank, score=score.value, before_rank=Empty)
        for score in scores
    ]

    return event(scores=score_elements)
