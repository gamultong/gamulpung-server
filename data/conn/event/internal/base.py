from typing import get_args, get_origin
from data.base import DataObj

from dataclasses import dataclass
from typing import Type, TypeVar


class Event(DataObj):
    event_name: str

    def assert_valid(self):
        pass


EVENT_DICT: dict[str, Type[Event]] = {}

T = TypeVar('T', bound=Event)


def event(event: Type[T]) -> Type[T]:
    assert issubclass(event, Event)

    EVENT_DICT[event.event_name] = event

    return event


class ValidationException(Exception):
    def __init__(self, event: Event, msg: str):
        self.event = event
        self.msg = msg


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


def get_anno_items(data_type: type[DataObj]):
    for key in data_type.__dataclass_fields__:
        yield key, data_type.__annotations__[key]


def parsing_type(field_type: type):
    origin_type = get_origin(field_type)
    if origin_type is None:
        return field_type, None
    args_type = get_args(field_type)
    assert len(args_type) == 1

    return origin_type, args_type[0]


def data_obj_parsing(data: dict, data_type: type[DataObj]):
    param = {}
    for key, field_type in get_anno_items(data_type):

        if key not in data:
            raise InvalidEventFormat

        field_data = data[key]

        origin_type, arg_type = parsing_type(field_type)

        if arg_type is None:
            if issubclass(origin_type, DataObj):
                # ex) DataObj
                param[key] = data_obj_parsing(field_data, field_type)
            else:
                # ex) str
                param[key] = field_data
        else:
            def func(fd): return data_obj_parsing(fd, arg_type)
            assert origin_type is list
            if issubclass(arg_type, DataObj):
                if origin_type is list:
                    # ex) list[DataObj]
                    param[key] = [func(fd) for fd in field_data]
                if origin_type is dict:
                    # ex) dict[DataObj]
                    param[key] = {
                        key: func(fd)
                        for key, fd in field_data.items()
                    }
            else:
                # ex) list[str]
                param[key] = field_data

    if len(data) > len(param):
        # 원하지 않는 필드가 들어있음
        raise InvalidEventFormat

    return data_type(**param)


def from_message(message: dict):
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
