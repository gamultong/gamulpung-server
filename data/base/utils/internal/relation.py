from data.base import DataObj
from data.base.utils import HaveId
from dataclasses import dataclass, field

from typing import TypeVar, Generic

ID_TYPE = TypeVar("ID_TYPE")


@dataclass
class Relation(Generic[ID_TYPE], DataObj, HaveId[ID_TYPE]):
    _id: ID_TYPE
    relations: list[ID_TYPE] = field(default_factory=list)

    @property
    def id(self) -> ID_TYPE: return self._id

    @id.setter
    def id(self, data: ID_TYPE): self._id = data

    def __iter__(self):
        for i in self.relations:
            yield i
        return

    def __len__(self):
        return self.relations.__len__()


if __name__ == "__main__":
    # iter 사용코드
    for i in Relation[str](_id="s", relations=["a", "b", "c"]):
        print(i)
