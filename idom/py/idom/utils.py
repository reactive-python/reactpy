import os
import uuid
import inspect
from weakref import finalize
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


def bound_id(obj, size=10):
    obj_id = uuid.uuid4().hex
    while obj_id in _LOCAL_IDS:
        obj_id = uuid.uuid4().hex
    _LOCAL_IDS.add(obj_id)
    finalize(obj, lambda oid=obj_id: _LOCAL_IDS.remove(oid))
    return obj_id


_LOCAL_IDS = set()
