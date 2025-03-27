from dataclasses import dataclass

class DataObj:
    def copy(self):
        return self.__class__(
            **{
                key : self.__dict__[key]
                for key in self.__dataclass_fields__
            }
        )
    
def copy(item):
    if issubclass(type(item), DataObj):
        return item.copy()
    return item