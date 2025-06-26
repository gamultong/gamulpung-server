from dataclasses import dataclass
from .base_data import DataObj
from typing import (
    TypeVar, 
    Type, 
    Generic, 
    Dict, 
    Unpack, 
    TypeVarTuple
)

T = TypeVar("T", bound=DataObj)
Ts = TypeVarTuple("Ts") 

class SubMap(Generic[Unpack[Ts]]):
    def __init__(self):
        self._map: Dict[Type[DataObj], DataObj] = {}

    def __getitem__(self, key: Type[T]) -> T:
        return self._map[key] 

    def __setitem__(self, key: Type[T], value:T):
        self._map[key] = value

@dataclass
class DomainObj(Generic[Unpack[Ts]]):
    def __post_init__(self):
        self.sub = SubMap[Unpack[Ts]]()
        super().__init__()

if __name__ == "__main__":
    @dataclass
    class F(DomainObj[Unpack[Ts]]):
        feild:int

        @dataclass
        class Sub(DataObj):
            feild:int

    f = F[F.Sub](1)
    f.sub[F.Sub] = F.Sub(1)
    s = f.sub[F.Sub]
    print(s)
