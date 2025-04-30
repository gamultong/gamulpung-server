from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock
from tests.utils import PathPatch
from dataclasses import dataclass

from data.base import DataObj
from handler.storage.dict import DictSpace
from handler.storage.interface.test.key_value_test import KeyValueInterface_TestCase

# 숙제
# 사용성 개선

class DictSpace_TestCase(KeyValueInterface_TestCase, AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.storage = DictSpace(
            name="example", 
            data=self.init_data
        )
