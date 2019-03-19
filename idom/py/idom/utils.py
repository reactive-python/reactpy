import os
import inspect
from functools import wraps

from typing import Callable

STATIC = os.path.join(os.path.dirname(__file__), "static")


def to_coroutine(function: Callable) -> Callable:
    if inspect.iscoroutinefunction(function):
        return function
    else:

        @wraps(function)
        async def wrapper(*args, **kwargs):
            return function(*args, **kwargs)

        return wrapper


class Sentinel:

    __slots__ = ("__name",)

    def __init__(self, name):
        self.__name = name

    def __repr__(self):
        return self.__name
