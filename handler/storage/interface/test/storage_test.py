from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock
from tests.utils import PathPatch
from .example_data import ExampleData

from handler.storage.interface import (
    Storage, DuplicateSpaceException, SpaceNotFoundException
)

class Storage_TestCase:
    def setUp(self):
        self.storage: Storage
        self.data1 = ExampleData(1)
        self.init_data = {"A": self.data1}

    def test_get_normal(self):
        space = self.storage.get_space("A")

        self.assertIs(space, self.data1)

    def test_get_not_found(self):
        with self.assertRaises(SpaceNotFoundException) as cm:
            self.storage.get_space("B")

    def test_create_normal(self):
        space = self.storage.create_space("B")

        got = self.storage.get_space("B")

        self.assertIs(got, space)

    def test_create_duplicate(self):
        with self.assertRaises(DuplicateSpaceException) as cm:
            self.storage.create_space("A")

