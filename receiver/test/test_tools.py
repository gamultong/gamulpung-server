import unittest
from unittest.mock import _Call, patch

from data.cursor import Cursor
from data.conn.event import ServerEvent


def assertMulticast(self: unittest.TestCase, call: _Call, target_conns: list[str], event: ServerEvent):
    self.assertEqual(call.kwargs["target_conns"], target_conns)
    self.assertEqual(call.kwargs["event"], event)


def get_cur_set(n: int) -> list[Cursor]:
    if n > 24:
        raise "test ninja"

    return [
        Cursor.create(chr(ord("A")+i))
        for i in range(n)
    ]
