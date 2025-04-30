from data.base import DataObj
from dataclasses import dataclass

@dataclass
class ExampleData(DataObj):
    data: int