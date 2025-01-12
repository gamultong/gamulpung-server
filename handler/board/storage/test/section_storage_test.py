from data.board import Point, Section
from handler.board.storage import SectionStorage
from .fixtures import teardown_board

import unittest


class SectionStorageTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        await teardown_board()

    async def test_set_create(self):
        sec = Section.create(Point(0, 0))

        await SectionStorage.set(sec)

    async def test_get_not_exits(self):
        section = await SectionStorage.get(Point(0, 0))
        self.assertIsNone(section)

    async def test_get(self):
        sec = Section.create(Point(1, -1))
        await SectionStorage.set(sec)

        got = await SectionStorage.get(sec.p)
        self.assertIsNotNone(got)
        self.assertEqual(type(got), Section)
        self.assertEqual(got.p, sec.p)
        self.assertEqual(got.data, sec.data)

    async def test_set_update(self):
        sec = Section.create(Point(0, 0))
        await SectionStorage.set(sec)

        sec.data[0] = 0b11111111

        await SectionStorage.set(sec)

        updated = await SectionStorage.get(sec.p)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.data[0], 0b11111111)

    async def test_get_random_sec_point(self):
        sec = Section.create(Point(0, 0))
        await SectionStorage.set(sec)

        p = await SectionStorage.get_random_sec_point()

        self.assertEqual(p, sec.p)
