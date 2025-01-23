import unittest

from event.message import Message


def assertMessageEqual(self: unittest.TestCase, actual: Message, expect: Message):
    self.assertEqual(actual.event, expect.event)
    self.assertEqual(type(actual.payload), type(expect.payload))

    self.assertEqual(actual.payload, expect.payload)
