from typing import Generic, TypeVar
from abc import abstractmethod, ABC

ID_TYPE = TypeVar("ID_TYPE")

# TODO: test + vaildate_check(-> data_obj 인지)


class HaveId(Generic[ID_TYPE], ABC):
    @property
    @abstractmethod
    def id(self) -> ID_TYPE:
        raise "not implemented"

    @id.setter
    @abstractmethod
    def id(self, data: ID_TYPE):
        raise "not implemented"
