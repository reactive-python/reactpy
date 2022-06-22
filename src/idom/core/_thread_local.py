from threading import Thread, current_thread
from typing import Any, Callable, Generic, TypeVar, cast
from weakref import WeakKeyDictionary


_StateType = TypeVar("_StateType")


class ThreadLocal(Generic[_StateType]):
    """Utility for managing per-thread state information"""

    def __init__(self, default: Callable[[], _StateType] = cast(Any, lambda: None)):
        self._default = default
        self._state: WeakKeyDictionary[Thread, _StateType] = WeakKeyDictionary()

    def get(self) -> _StateType:
        thread = current_thread()
        if thread not in self._state:
            state = self._state[thread] = self._default()
        else:
            state = self._state[thread]
        return state

    def set(self, state: _StateType) -> None:
        self._state[current_thread()] = state
