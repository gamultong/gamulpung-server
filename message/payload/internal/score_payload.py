from .base_payload import Payload
from dataclasses import dataclass
from enum import Enum


class ScoreEvent(str, Enum):
    SCORE_NOTIFY = "score-notify"
    ADD_SCORE = "add-score"


@dataclass
class ScoreNotifyPayload(Payload):
    cursor_id: str
    score: int


@dataclass
class AddScorePayload(Payload):
    cursor_id: str
    score: int
