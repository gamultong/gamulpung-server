import unittest
from unittest.mock import _Call

from event.message import Message

def assertMulticast(self: unittest.TestCase, call: _Call, target_conns: list[str], message: Message):
    self.assertEqual(call.kwargs["target_conns"], target_conns)
    self.assertEqual(call.kwargs["message"], message)
