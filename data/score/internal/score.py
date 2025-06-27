from data.base import DataObj
from data.base.utils import HaveId
from dataclasses import dataclass


@dataclass
class Score(DataObj, HaveId[str]):
    cursor_id: str
    value: int
    rank: int | None = None

    @property
    def id(self):
        return self.cursor_id
