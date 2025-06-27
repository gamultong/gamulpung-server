from data.base import DataObj
from dataclasses import dataclass
from unittest import TestCase
from typing import TypeVarTuple, Unpack
from data.base import DataObj, DomainObj

Ts = TypeVarTuple("Ts") 

@dataclass
class ExampleDomainObj(DomainObj[Unpack[Ts]]):
    feild:int

    @dataclass
    class ExampleSubObj(DataObj):
        feild:int

class DomainObj_TestCase(TestCase):
    def test_set_by_type(self):
        exp_sub_type = ExampleDomainObj.ExampleSubObj
        exp = ExampleDomainObj[exp_sub_type](1)
        exp_sub = exp_sub_type(1)
        exp.sub[exp_sub_type] = exp_sub
        self.assertIn(exp_sub_type, exp.sub._map) 
        self.assertEqual(exp_sub, exp.sub._map[exp_sub_type]) 

    def test_get_by_type(self):
        exp_sub_type = ExampleDomainObj.ExampleSubObj
        exp = ExampleDomainObj[exp_sub_type](1)
        exp_sub = exp_sub_type(1)
        exp.sub[exp_sub_type] = exp_sub

        self.assertEqual(exp.sub[exp_sub_type], exp_sub)

if __name__ == "__main__":
    from unittest import main
    main()