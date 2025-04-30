from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock
from tests.utils import PathPatch
from dataclasses import dataclass

from data.base import DataObj
from handler.storage.list.array import ArrayListStorage

from handler.storage.interface.test.storage_test import Storage_TestCase, ExampleData 

class ArrayListStorage_TestCase(Storage_TestCase, TestCase):
    def setUp(self):
        super().setUp()
        ArrayListStorage.spaces = self.init_data
        self.storage = ArrayListStorage


    def tearDown(self):
        ArrayListStorage.spaces = {}