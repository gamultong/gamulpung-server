import unittest
from unittest.mock import _Call, patch

from data.cursor import Cursor

from event.message import Message

def assertMulticast(self: unittest.TestCase, call: _Call, target_conns: list[str], message: Message):
    self.assertEqual(call.kwargs["target_conns"], target_conns)
    self.assertEqual(call.kwargs["message"], message)

def get_cur_set(n: int) -> list[Cursor]:
    if n > 24:
        raise "test ninja"

    return [
        Cursor.create(chr(ord("A")+i))
        for i in range(n)
    ]


class PathPatch:
    def __init__(self, path):
        self.path = path

    def __call__(self, name, *args, **kwargs):
        def wrapper(func):
            func = patch(self.path+"."+name, *args, **kwargs)(func)
            return func
        return wrapper