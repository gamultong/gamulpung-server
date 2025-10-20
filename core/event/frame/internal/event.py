from __future__ import annotations
from typing import TypeVar, Generic, get_origin, get_args, Any, Type, ClassVar
from .payload import Payload
from utils.property import classproperty


PAYLOAD_TYPE = TypeVar("PAYLOAD_TYPE", bound=Payload)


class Event(Generic[PAYLOAD_TYPE]):
    """Event"""
    name: ClassVar[str]
    scope: ClassVar[type[EventSet] | None] = None  # 스코프 역참조
    payload_type: ClassVar[Type[PAYLOAD_TYPE]]  # type:ignore

    def __init__(self, payload: PAYLOAD_TYPE):
        self.payload = payload

    @classmethod
    def set_scope(cls, event_set: type[EventSet]) -> None:
        """EventSet에서 Scope가 생길 시 name 변경"""
        # 재진입 방지: 이미 같은 스코프로 세팅돼 있으면 스킵
        assert cls.scope is None

        cls.scope = event_set
        cls.name = f"{event_set.scope_name}.{cls.name}"

# 1) 클래스 본문에 쓰일 네임스페이스(dct)를 커스터마이즈


class _EventSetNamespace(dict):
    """
    EventSet custom namespace 
    다음과 같은 사용 코드를 위해 제작->
    class ExampleEventSet(EventSet):
        EVENT_1 = Event[str]  
        EVENT_2 = Event[int]
    """

    def __init__(self):
        self._events: list[type[Event]] = []

    def __setitem__(self, key, value):
        origin = get_origin(value)
        if origin is Event:
            # Event[str] 같은 파라미터화된 타입을 감지
            (arg,) = get_args(value) or (Any,)
            # 실제 "클래스"를 만들어 넣는다 (=> 타입 힌팅 자리에도 사용 가능)
            new_cls: Event = type(key, (Event,), {
                "payload_type": arg,
                # IDE/타입체커 힌트를 위해 선택적으로 남겨 둔다
                "__orig_bases__": (Event[arg],),
            })
            # name 자동 주입
            new_cls.name = key
            value = new_cls

            self._events.append(new_cls)
        super().__setitem__(key, value)


# 2) 메타클래스: __prepare__로 커스텀 네임스페이스를 제공
class EventSetMeta(type):
    @classmethod
    def __prepare__(mcls, name, bases):
        # 클래스 본문에서의 모든 할당이 이 dict를 통해 들어온다
        return _EventSetNamespace()

    def __new__(mcls, name, bases, namespace: _EventSetNamespace, **kw):
        cls = super().__new__(mcls, name, bases, dict(namespace))
        # dict(namespace) -> 복제본 전달로 namespace가 가진 커스텀 로직은 더 이상 관여 X
        cls._events = tuple(namespace._events)
        return cls


class EventSet(metaclass=EventSetMeta):
    scope_name: ClassVar[str | None] = None
    _events: ClassVar[tuple[type[Event]]]  # 힌팅용

    @classmethod
    def set_scope(cls, scope_name: str):
        """scope setting"""
        cls.scope_name = scope_name
        for event in cls._events:
            event.set_scope(cls)

    @classmethod
    def events(cls):
        """event를 dict으로 반환"""
        return {
            event.name: event
            for event in cls._events
        }


T = TypeVar("T", bound=Type[EventSet])


def set_scope(scope_name: str):
    """scope 설정 deco"""
    def wrapper(event_set: T) -> T:
        assert issubclass(event_set, EventSet)

        event_set.set_scope(scope_name)
        return event_set
    return wrapper


if __name__ == "__main__":
    # 3) 사용

    @set_scope("Example")
    class ExampleEventSet(EventSet):
        EVENT_1 = Event[str]   # 한 줄 선언 OK → 실제 서브클래스로 치환됨
        EVENT_2 = Event[int]

    # 확인
    print(ExampleEventSet.EVENT_1, ExampleEventSet.EVENT_1.name)        # <class 'EVENT_1'> EVENT_1
    print(ExampleEventSet.EVENT_1.payload_type is str)                  # True
    print(ExampleEventSet._events)
    print(ExampleEventSet.EVENT_2, ExampleEventSet.EVENT_2.name)        # <class 'EVENT_2'> EVENT_2
    print(ExampleEventSet.EVENT_2.payload_type is int)                  # True

    def some_func(event: ExampleEventSet.EVENT_1) -> None:
        assert isinstance(event, ExampleEventSet.EVENT_1)
        print(event.payload)

    some_func(ExampleEventSet.EVENT_1("hi"))
