import inspect
from unittest.mock import patch

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