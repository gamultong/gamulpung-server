from dataclasses import dataclass
from typing import Literal, TypeVar, Generic, Any
import inspect
from unittest.mock import patch, AsyncMock, MagicMock, Mock


def cases(case_list):
    def wrapper(func):
        if inspect.iscoroutinefunction(func):
            async def async_func_wrapper(*args, **kwargs):
                mock = args[0]
                if hasattr(mock, "setUp"):
                    mock.setUp()
                if hasattr(mock, "asyncSetUp"):
                    await mock.asyncSetUp()

                for i in case_list:
                    kwargs.update(i)
                    await func(*args, **kwargs)

            return async_func_wrapper

        def func_wrapper(*args, **kwargs):
            mock = args[0]
            if hasattr(mock, "setUp"):
                mock.setUp()
            for i in case_list:
                kwargs.update(i)
                func(*args, **kwargs)
        return func_wrapper
    return wrapper


class PathPatch:
    def __init__(self, path: str):
        self.path = path

    def __call__(self, name: str, *args, **kwargs):
        def wrapper(func):
            func = patch(self.path+"."+name, *args, **kwargs)(func)
            return func
        return wrapper


@dataclass
class override:
    name: str
    return_value: any = None
    side_effect: any = None


MOCK_TYPE = TypeVar("MOCK_TYPE")


class Wrapper(Generic[MOCK_TYPE]):
    def __get__(self, obj: Any, owner: type[Any] | None) -> MOCK_TYPE: ...


class MockSet:
    __path__: str

    @classmethod
    def patch(cls, *args: override):
        patch = PathPatch(cls.__path__)

        # 일시적 override하는것들
        override_dict = {
            i.name: i
            for i in args
        }

        def wrapper(func):
            queue = []

            def make_mockset(args):
                mock_set = cls()
                offset = len(queue)

                # patch된 객체 중 override_dict에 포함되면 다시 오버라이드.
                for i, key in enumerate(queue):
                    mock = args[-offset+i]
                    if key in override_dict:
                        mock.return_value = override_dict[key].return_value
                        mock.side_effect = override_dict[key].side_effect
                    mock_set.__dict__[key] = mock

                # 기존 patch 인자 제거하고 mock_set만 넘김
                args = args[:-offset]
                return args, mock_set

            # patch 대신 받아주는 함수

            def func_wrapper(*args, **kwargs):
                args, mock_set = make_mockset(args)
                return func(*args, mock_set, **kwargs)

            # patch 대신 받아주는 함수(async)
            async def async_func_wrapper(*args, **kwargs):
                args, mock_set = make_mockset(args)
                return await func(*args, mock_set, **kwargs)

            if inspect.iscoroutinefunction(func):
                wrap_func = async_func_wrapper
            else:
                wrap_func = func_wrapper

            # 네임스페이스 patch 실행 -> wrap_func 인자로 들어감.
            for key, _type in cls.__annotations__.items():
                if not hasattr(_type, "__origin__") or _type.__origin__ is not Wrapper:
                    continue
                item: override = cls.__dict__[key]

                wrap_func = patch(
                    item.name,
                    return_value=item.return_value,
                    side_effect=item.side_effect,
                )(wrap_func)

                queue.append(key)

            return wrap_func
        return wrapper
