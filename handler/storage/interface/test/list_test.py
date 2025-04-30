from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock
from tests.utils import PathPatch
from .example_data import ExampleData

from handler.storage.interface import (
    ListInterface,IndexOutOfRangeException
)


class ListInterface_TestCase:
    def setUp(self):
        self.storage: ListInterface
        self.data1 = ExampleData(1)
        self.data2 = ExampleData(2)
        self.init_data = [self.data1, self.data2]

    async def test_length_normal(self: AsyncTestCase):
        length = await self.storage.length()

        self.assertEqual(length, 2)

    async def test_get_normal(self: AsyncTestCase):
        got = await self.storage.get(0)
        
        self.assertEqual(got, self.data1)
        self.assertIsNot(got, self.data1)
    
    async def test_get_out_of_range(self: AsyncTestCase):
        with self.assertRaises(IndexOutOfRangeException) as cm:
            await self.storage.get(2)


    async def test_insert_normal(self: AsyncTestCase):
        data = ExampleData(3)

        await self.storage.insert(1, data)

        got = await self.storage.get(1)
        self.assertEqual(got, data)
        self.assertIsNot(got, data)

        got = await self.storage.get(2)
        self.assertEqual(got, self.data2)


    async def test_insert_out_of_range(self: AsyncTestCase):
        with self.assertRaises(IndexOutOfRangeException) as cm:
            await self.storage.insert(2, self.data2)

    async def test_append_normal(self: AsyncTestCase):
        data = ExampleData(3)

        await self.storage.append(data)

        got = await self.storage.get(2)
        self.assertEqual(got, data)
        self.assertIsNot(got, data)
    
    async def test_pop_normal(self: AsyncTestCase):
        got = await self.storage.pop(1)
        self.assertEqual(got, self.data2)

        count = await self.storage.length()
        self.assertEqual(count, 1)

    async def test_pop_out_of_range(self: AsyncTestCase):
        with self.assertRaises(IndexOutOfRangeException) as cm:
            await self.storage.pop(2)
