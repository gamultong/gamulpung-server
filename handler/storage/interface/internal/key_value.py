from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Iterable
from data.base import DataObj

KEY_TYPE = TypeVar(
    "KEY_TYPE",
    bound=DataObj
)
VALUE_TYPE = TypeVar(
    "VALUE_TYPE",
    bound=DataObj
)


class KeyValueInterface(Generic[KEY_TYPE, VALUE_TYPE], ABC):
    @abstractmethod
    async def keys(self) -> Iterable[KEY_TYPE]:
        pass

    @abstractmethod
    async def get(self, key: KEY_TYPE) -> VALUE_TYPE | None:
        pass

    @abstractmethod
    async def set(self, key: KEY_TYPE, value: VALUE_TYPE):
        pass

    @abstractmethod
    async def delete(self, key: KEY_TYPE):
        pass
