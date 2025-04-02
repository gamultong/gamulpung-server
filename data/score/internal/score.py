from data.base import DataObj
from dataclasses import dataclass

@dataclass
class Score(DataObj):
    cursor_id:str
    value    :int
    rank     :int|None = None
    
    @property
    def id(self):
        return self.cursor_id