import unittest
from data.board import Point


class PointTestCase(unittest.TestCase):
    def test_marshal_bytes(self):
        p = Point(5, -1)
        b = p.marshal_bytes()

        self.assertEqual(len(b), 16)

        x = int.from_bytes(bytes=b[:8], signed=True)
        self.assertEqual(x, p.x)

        y = int.from_bytes(bytes=b[8:], signed=True)
        self.assertEqual(y, p.y)

    def test_unmarshal_bytes(self):
        expected = Point(5, -1)

        # 5, -1
        data = b'\x00\x00\x00\x00\x00\x00\x00\x05\xff\xff\xff\xff\xff\xff\xff\xff'

        p = Point.unmarshal_bytes(data)
        self.assertEqual(expected, p)
