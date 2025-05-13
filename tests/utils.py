from dataclasses import dataclass
from typing import Literal
import inspect
from unittest.mock import patch, AsyncMock, MagicMock


def cases(case_list):
    def wrapper(func):
        if inspect.iscoroutinefunction(func):
            async def async_func_wrapper(*arg, **kwargs):
                for i in case_list:
                    kwargs.update(i)
                    await func(*arg, **kwargs)

            return async_func_wrapper

        def func_wrapper(*arg, **kwargs):
            for i in case_list:
                kwargs.update(i)
                func(*arg, **kwargs)
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

            # patch 대신 받아주는 함수
            def func_wrapper(*args, **kwargs):
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
                return func(*args, mock_set=mock_set, **kwargs)

            # 네임스페이스 patch 실행 -> func_wrapper 인자로 들어감.
            for key, _type in cls.__annotations__.items():
                if _type not in (AsyncMock, MagicMock):
                    continue
                item: override = cls.__dict__[key]

                func_wrapper = patch(
                    item.name,
                    return_value=item.return_value,
                    side_effect=item.side_effect,
                )(func_wrapper)

                queue.append(key)

            return func_wrapper
        return wrapper
