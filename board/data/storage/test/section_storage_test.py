from board.data import Point, Section
from board.data.storage import SectionStorage
from .fixtures import teardown_board

import unittest


class SectionStorageTestCase(unittest.TestCase):
    def tearDown(self):
        teardown_board()

    def test_set_create(self):
        sec = Section.create(Point(0, 0))

        SectionStorage.set(sec)

    def test_get_not_exits(self):
        section = SectionStorage.get(Point(0, 0))
        self.assertIsNone(section)

    def test_get(self):
        sec = Section.create(Point(1, -1))
        SectionStorage.set(sec)

        got = SectionStorage.get(sec.p)
        self.assertIsNotNone(got)
        self.assertEqual(type(got), Section)
        self.assertEqual(got.p, sec.p)
        self.assertEqual(got.data, sec.data)

    def test_set_update(self):
        sec = Section.create(Point(0, 0))
        SectionStorage.set(sec)

        sec.data[0] = 0b11111111

        SectionStorage.set(sec)

        updated = SectionStorage.get(sec.p)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.data[0], 0b11111111)

    def test_get_random_sec_point(self):
        sec = Section.create(Point(0, 0))
        SectionStorage.set(sec)

        p = SectionStorage.get_random_sec_point()

        self.assertEqual(p, sec.p)
