import time
import asyncio
from functools import lru_cache
from typing import (
    Dict,
    Any,
    TypeVar,
    Callable,
    Tuple,
    Optional,
    Union,
    Generic,
)

from ._hooks import dispatch_hook


def use_update() -> Callable[[], None]:
    hook = dispatch_hook()
    return hook.create_update_callback()


_StateType = TypeVar("_StateType")


class Shared(Generic[_StateType]):

    __slots__ = "_callbacks", "_value"

    def __init__(self, value: _StateType) -> None:
        self._callbacks: Dict[str, Callable[[], None]] = {}
        self._value = value


def use_state(
    value: Union[_StateType, Shared[_StateType]]
) -> Tuple[_StateType, Callable[[_StateType], None]]:
    if not isinstance(value, Shared):
        return _use_state(value)
    else:
        return _use_shared_state(value)


def _use_state(value: _StateType) -> Tuple[_StateType, Callable[[_StateType], None]]:
    hook = dispatch_hook()
    state: Dict[str, Any] = hook.use_state(dict)
    update = hook.create_update_callback()

    if "value" not in state:
        state["value"] = value

    def set_state(new: _StateType) -> None:
        state["value"] = new
        update()

    return state["value"], set_state


def _use_shared_state(
    shared: Shared[_StateType],
) -> [_StateType, Callable[[_StateType], None]]:
    hook = dispatch_hook()
    shared._callbacks[hook.element.id] = hook.create_update_callback()
    hook.on_unmount(shared._callbacks.pop, hook.element.id, None)

    def set_state(new: _StateType) -> None:
        shared._value = new
        for cb in shared._callbacks.values():
            cb()

    return shared._value, set_state


_MemoValue = TypeVar("_MemoValue")


def use_memo(
    function: Callable[..., _MemoValue], *args: Any, **kwargs: Any
) -> _MemoValue:
    hook = dispatch_hook()
    cache: Dict[int, _MemoValue] = hook.use_state(dict)

    key = hash((args, tuple(kwargs.items())))
    if key in cache:
        result = cache[key]
    else:
        cache.clear()
        result = cache[key] = function(*args, **kwargs)

    return result


_LruFunc = TypeVar("_LruFunc")


def use_lru_cache(
    function: _LruFunc, maxsize: Optional[int] = 128, typed: bool = False
) -> _LruFunc:
    return dispatch_hook().use_state(lru_cache(maxsize, typed), function)


async def use_frame_rate(rate: float = 0) -> None:
    await dispatch_hook().use_state(FramePacer, rate).wait()


class FramePacer:
    """Simple utility for pacing frames in an animation loop."""

    __slots__ = "_rate", "_last"

    def __init__(self, rate: float):
        self._rate = rate
        self._last = time.time()

    async def wait(self) -> None:
        await asyncio.sleep(self._rate - (time.time() - self._last))
        self._last = time.time()
