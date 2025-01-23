import unittest
from unittest.mock import _Call

from event.message import Message


def assertMessageEqual(self: unittest.TestCase, actual: Message, expect: Message):
    self.assertEqual(actual.event, expect.event)
    self.assertDictEqual(actual.header, expect.header)
    self.assertEqual(type(actual.payload), type(expect.payload))
    self.assertEqual(actual.payload, expect.payload)


def assertMulticast(self: unittest.TestCase, call: _Call, target_conns: list[str], message: Message):
    self.assertEqual(call.kwargs["target_conns"], target_conns)
    assertMessageEqual(self, actual=call.kwargs["message"], expect=message)
