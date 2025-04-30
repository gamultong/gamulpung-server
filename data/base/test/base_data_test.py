from data.base import DataObj, copy
from dataclasses import dataclass
from tests.utils import cases
from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase

@dataclass
class ExampleObj(DataObj):
    field:int

@dataclass
class Example2Obj(DataObj):
    field:ExampleObj

# 이에 대한 처리를 해주면 좋음(자세한건 DataObj 주석 참고)
class WrongObj(DataObj):
    pass

class DataObj_TestCase(TestCase):
    def test_copy_data_obj(self):
        original = ExampleObj(field=1)
        clone = copy(original)

        self.assertEqual(original, clone)
        self.assertIsNot(original, clone)
    
    def test_copy_builtin_obj_immutable(self):
        original = "example"
        clone = copy(original)

        self.assertEqual(original, clone)
        # imnutable한 obj들은 변경시 새 obj 생성해서 검사 할 필요 X
        # self.assertIsNot(original, clone) 

    @cases([
        {"mutable_obj":["example"]},
        {"mutable_obj":{"foo": "bar"}},
        {"mutable_obj":{"example"}}
    ])
    def test_copy_builtin_obj_mutable(self, mutable_obj):
        clone = copy(mutable_obj)

        self.assertEqual(mutable_obj, clone)
        self.assertIsNot(mutable_obj, clone) 
    
    def test_to_dict(self):
        obj = ExampleObj(field=1)
        dict = {
            "field": 1
        }

        self.assertDictEqual(
            obj.to_dict(),
            dict
        )

    def test_to_dict_recursive(self):
        obj = Example2Obj(
            field=ExampleObj(
                field=1
            )
        )
        dict = {
            "field": {
                "field": 1
            }
        }

        self.assertDictEqual(
            obj.to_dict(),
            dict
        )