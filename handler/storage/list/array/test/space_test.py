from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock
from tests.utils import PathPatch
from dataclasses import dataclass

from data.base import DataObj
from handler.storage.list.array import ArrayListSpace

from handler.storage.interface.test.list_test import ListInterface_TestCase, ExampleData 

class ArrayListSpace_TestCase(ListInterface_TestCase, AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.storage = ArrayListSpace(
            name="example", 
            data=self.init_data
        )
