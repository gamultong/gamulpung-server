import inspect


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
