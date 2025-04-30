from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from data.base import DataObj

class DuplicateSpaceException(BaseException):
    pass
class SpaceNotFoundException(BaseException):
    pass


SPACE_TYPE = TypeVar(
    "SPACE_TYPE",
    bound=DataObj
)

class Storage(Generic[SPACE_TYPE], ABC):
    spaces: dict[str, SPACE_TYPE] = {}

    @abstractmethod
    def create_space(key: str) -> SPACE_TYPE:
        """
        key에 따른 space를 만듦. 이미 있는 key면 에러.
        """
        pass

    @abstractmethod
    def get_space(key: str):
        """
        key에 따른 space를 가져옴. 없으면 에러.
        """
        pass