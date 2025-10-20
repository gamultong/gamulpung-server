from typing import TypeVar, Generic
from core.data import DataObj


class Payload(DataObj):
    pass


class Empty:
    pass


class ExternalPayload(Payload):
    """
    external Event
    상속으로 사용
    """

    def to_dict(self):
        return {
            key: item
            for key, item in super().to_dict().items()
            if item is not Empty
        }


ID_TYPE = TypeVar("ID_TYPE")
DATA_TYPE = TypeVar("DATA_TYPE", bound=DataObj)


class IdPayload(Generic[ID_TYPE], Payload):
    """
    Internal Event
    Id만 있는 경우 
    ex) create
    """
    id: ID_TYPE


class IdDataPayload(Generic[ID_TYPE, DATA_TYPE], Payload):
    """
    Internal Event
    id: 변경 결과에 접근 가능한 id
    data : 변경 전 data
    """
    id: ID_TYPE
    data: DATA_TYPE
