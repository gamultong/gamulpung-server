import os
from dotenv import load_dotenv
from datetime import timedelta
from typing import Callable, TypeVar, Generic

T = TypeVar("T")

if os.environ.get("ENV") != "prod":
    load_dotenv(".dev.env")


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
