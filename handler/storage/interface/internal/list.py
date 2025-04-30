from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from data.base import DataObj

DATA_TYPE = TypeVar(
    "DATA_TYPE",
    bound=DataObj
)

class IndexOutOfRangeException(BaseException):
    pass

class ListInterface(Generic[DATA_TYPE], ABC):
    @abstractmethod
    async def length(self) -> int:
        pass

    @abstractmethod
    async def get(self, idx:int) -> DATA_TYPE:
        pass

    @abstractmethod
    async def insert(self, idx: int, value: DATA_TYPE):
        """
        idx 자리에 삽입, 기존 idx는 idx+1로 옮겨짐
        """
        pass 

    @abstractmethod
    async def append(self, value: DATA_TYPE):
        """
        마지막에 추가
        """
        pass 

    @abstractmethod
    async def pop(self, idx:int|None=None) -> DATA_TYPE:
        """
        idx가 None이면 마지막 요소 삭제
        """
        pass
