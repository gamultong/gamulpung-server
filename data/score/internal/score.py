from data.base import DataObj
from dataclasses import dataclass

@dataclass
class Score(DataObj):
    cursor_id: str
    score: int
    
    @property
    def id(self):
        return self.cursor_id