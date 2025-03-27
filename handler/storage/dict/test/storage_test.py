from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock
from tests.utils import PathPatch
from dataclasses import dataclass

from data.base import DataObj
from handler.storage.dict import DictSpace, DictStorage
from handler.storage.interface.test.storage_test import (
    Storage_TestCase
)

class DictStorage_TestCase(Storage_TestCase, TestCase):
    def setUp(self):
        super().setUp()
        self.storage = DictStorage
        DictStorage.spaces = self.init_data


    def tearDown(self):
        DictStorage.spaces = {}