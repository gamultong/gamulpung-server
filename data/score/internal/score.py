from data.base import DataObj
from dataclasses import dataclass

@dataclass
class Score(DataObj):
    id: str
    cursor_id: str
    score: int