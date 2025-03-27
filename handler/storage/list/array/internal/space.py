from typing import Generic, TypeVar
from data.base import DataObj, copy

DATA_TYPE = TypeVar(
    "DATA_TYPE",
    bound=DataObj
)
from handler.storage.interface import ListInterface, IndexOutOfRangeException

class ArrayListSpace(Generic[DATA_TYPE], ListInterface[DATA_TYPE]):
    def __init__(self, name: str, data: list[DATA_TYPE]):
        self.name = name
        self.data: list[DATA_TYPE] = data

    def is_in_range(self, idx):
        return 0 <= idx < len(self.data)

    async def length(self) -> int:
        return len(self.data)

    async def get(self, idx:int) -> DATA_TYPE:
        if not self.is_in_range(idx):
            raise IndexOutOfRangeException()
        
        return copy(self.data[idx])

    async def insert(self, idx: int, value: DATA_TYPE):
        if not self.is_in_range(idx):
            raise IndexOutOfRangeException()
        
        self.data.insert(idx, copy(value))

    async def append(self, value: DATA_TYPE):
        self.data.append(copy(value))

    async def pop(self, idx:int|None=None) -> DATA_TYPE:
        if idx is None:
            idx = len(self.data) - 1

        if not self.is_in_range(idx):
            raise IndexOutOfRangeException()
        
        return self.data.pop(idx)