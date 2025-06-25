from dataclasses import dataclass, Field
from typing import Union



# TODO: validate_check(DataObj -> dataclasss)
class DataObj:
    # DataObj가 dataclass로 예측
    # dataclass인지 vaildate 처리를 해주면 좋음

    # hinting을 위해 명시
    __dataclass_fields__: dict[str, Field]

    def copy(self):
        return self.__class__(
            **{
                key: copy(self.__dict__[key])
                for key in self.__dataclass_fields__
            }
        )

    def to_dict(self):        
        def __item_parsing(item):
            if issubclass(type(item), DataObj):
                return item.to_dict()
            return item

        return {
            key: __item_parsing(self.__dict__[key])
            for key in self.__dataclass_fields__
        }

from typing import TypeVar, Generic, Union, _SpecialForm, SupportsBytes

DATAOBJ_TYPE = TypeVar("DATAOBJ_TYPE", DataObj)

# @_SpecialForm
# def SubDataObj(self, parameters):
#     assert len(parameters) == 1

#     return _UnionGenericAlias(self, parameters)

from typing import Optional 

class SubData(Generic[DATAOBJ_TYPE], Optional[DATAOBJ_TYPE]):
    pass

@dataclass
class Cursor(DataObj):
    a:SubData[str]

def a(a:Cursor):
    a.a

def copy(item):
    if hasattr(item, "copy"):
        return item.copy()
    return item
