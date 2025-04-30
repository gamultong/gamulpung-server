from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock
from tests.utils import PathPatch
from .example_data import ExampleData

from handler.storage.interface import (
    KeyValueInterface
)


class KeyValueInterface_TestCase():
    def setUp(self):
        self.storage: KeyValueInterface
        self.data = ExampleData(1)
        self.init_data = {
            "A": self.data,
        }
    
    async def test_get_normal(self: AsyncTestCase):
        expected = ExampleData(1)
        got = await self.storage.get("A")
        
        self.assertEqual(expected, got)
        self.assertIsNot(self.init_data["A"], got)

    async def test_get_not_found(self: AsyncTestCase):
        got = await self.storage.get("B")
        
        self.assertIsNone(got)

    async def test_set_normal(self: AsyncTestCase):
        input = ExampleData(1)
        await self.storage.set("A", input)

        got = await self.storage.get("A")

        self.assertEqual(input, got)
        self.assertIsNot(input, got)

    async def test_delete_normal(self: AsyncTestCase):
        await self.storage.delete("A")

        got = await self.storage.get("A")
        self.assertIsNone(got)
