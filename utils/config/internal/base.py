import os
from typing import Callable, TypeVar, Generic

T = TypeVar("T")

class Env(Generic[T]):
    def __init__(self, func: Callable[[str], T] | None = None) -> None:
        self.func = func

    def __set_name__(self, owner, name):
        res = os.environ.get(name)
        assert res

        if self.func:
            res = self.func(res)

        self.value = res

    def __get__(self, instance, owner) -> T:
        return self.value  # type:ignore
