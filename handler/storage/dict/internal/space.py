from typing import Generic, TypeVar
from data.base import DataObj, copy

KEY_TYPE = TypeVar(
    "KEY_TYPE",
    bound=DataObj
)
VALUE_TYPE = TypeVar(
    "VALUE_TYPE",
    bound=DataObj
)
from handler.storage.interface import KeyValueInterface

class DictSpace(Generic[KEY_TYPE, VALUE_TYPE], KeyValueInterface[KEY_TYPE, VALUE_TYPE]):
    def __init__(self, name: str, data: dict):
        self.name = name
        self.data: dict[KEY_TYPE, VALUE_TYPE] = data

    async def get(self, key:KEY_TYPE) -> VALUE_TYPE:
        if key not in self.data:
            return None
        
        return copy(self.data[key])

    async def set(self, key:KEY_TYPE, value:VALUE_TYPE):
        self.data[key] = copy(value)
    
    async def delete(self, key:KEY_TYPE):
        del self.data[key]