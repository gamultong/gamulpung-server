from data.base import DataObj

from dataclasses import dataclass
from typing import Type, TypeVar

class Event(DataObj):
    event_name:str

    def assert_valid(self):
        pass
    
EVENT_DICT: dict[str, Event] = {}

T = TypeVar('T', bound=Event)

def event(event: Type[T]) -> Type[T]:
    assert issubclass(event, Event)

    EVENT_DICT[event.event_name] = event

    return dataclass(event)


class ValidationException(Exception):
    def __init__(self, event:Event, msg: str):
        self.event = event
        self.msg = msg

class Empty:
    pass

class ClientEvent(Event):
    pass

class ServerEvent(Event):
    pass

def to_message(event: Event):
    return {
        "header": {
            "event": event.event_name
        },
        "content": event.to_dict()
    }

from typing import get_args, get_origin

def data_obj_parsing(data:dict, data_type:type[DataObj]):
    param = {}

    for key in data_type.__dataclass_fields__:
        field_type = data_type.__annotations__[key] # 받고자 하는 타입
        try:
            field_data = data.pop(key) # 실제 데이터
        except KeyError:
            # 원하는 필드가 존재하지 않음
            raise InvalidEventFormat

        origin_type = get_origin(field_type) # list[Event] 같이 감싸져있나
        if origin_type is None:
            
            if issubclass(field_type, DataObj):
                # DataObj이면 재귀로 매핑
                param[key] = data_obj_parsing(field_data, field_type)
                continue

            param[key] = field_data
            continue

        # list[T]
        assert origin_type is list 

        args_type = get_args(field_type)
        assert len(args_type) == 1 # 타입이 1개임을 검증
        
        arg_type = args_type[0]
        if issubclass(arg_type, DataObj):
            param[key] = [data_obj_parsing(fd, arg_type) for fd in field_data]
            continue

        param[key] = field_data

    if len(data) > 0:
        # 원하지 않는 필드가 들어있음
        raise InvalidEventFormat

    return data_type(**param)
                
def from_message(message:dict):
    try:
        heeader = message["header"]
        event = heeader["event"]
        content = message["content"]
    except KeyError:
        # 메시지 포맷이 잘못됨
        raise InvalidEventFormat
    
    try:
        type = EVENT_DICT[event]
    except KeyError:
        # event가 존재하지 않음
        raise InvalidEventFormat
    
    return data_obj_parsing(content, type)

class InvalidEventFormat(Exception):
    pass