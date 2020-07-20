import time
import asyncio
from functools import lru_cache
from typing import Dict, Any, TypeVar, Callable, Tuple, Optional, Type, Generic, Union

from ._hooks import current_hook, CreateContext, Context


__all__ = [
    "use_update",
    "use_state",
    "use_context",
    "use_memo",
    "use_lru_cache",
    "use_frame_rate",
    "CreateContext",
    "Context",
]


def use_update() -> Callable[[], None]:
    return current_hook().use_update()


_StateType = TypeVar("_StateType")


class Shared(Generic[_StateType]):

    __slots__ = "_callbacks", "_value"

    def __init__(self, value: _StateType) -> None:
        self._callbacks: Dict[str, Callable[[_StateType], None]] = {}
        self._value = value

    def update(self, value: _StateType) -> None:
        self._value = value
        for cb in self._callbacks.values():
            cb(value)


def _new_is_not_old(old: _StateType, new: _StateType) -> bool:
    return new is not old


def use_state(
    value: Union[_StateType, Shared[_StateType]],
    should_update: Callable[[_StateType, _StateType], bool] = _new_is_not_old,
) -> Tuple[_StateType, Callable[[_StateType], None]]:
    if isinstance(value, Shared):
        return _use_shared(value, should_update)
    else:
        return _use_state(value, should_update)


def _use_shared(
    shared: Shared[_StateType], should_update: Callable[[_StateType, _StateType], bool],
) -> [_StateType, Callable[[_StateType], None]]:
    hook = current_hook()
    element_id = hook.element().id
    update = hook.use_update()
    hook.use_finalizer(shared._callbacks.pop, element_id, None)
    shared._callbacks[element_id] = (
        lambda value: update() if should_update(shared._value, value) else None
    )

    def set_state(new: _StateType) -> None:
        shared.update(new)

    return shared._value, set_state


def _use_state(
    value: _StateType, should_update: Callable[[_StateType, _StateType], bool],
) -> Tuple[_StateType, Callable[[_StateType], None]]:
    hook = current_hook()
    state: Dict[str, Any] = hook.use_state(dict)
    update = hook.use_update()

    if "value" not in state:
        state["value"] = value

    def set_state(new: _StateType) -> None:
        old = state["value"]
        if should_update(new, old):
            state["value"] = new
            update()

    return state["value"], set_state


def use_context(
    context_type: Type[Context[_StateType]],
    should_update: Callable[[_StateType, _StateType], bool] = _new_is_not_old,
) -> Tuple[_StateType, Callable[[_StateType], None]]:
    return current_hook().use_context(context_type, should_update)


_MemoValue = TypeVar("_MemoValue")


def use_memo(
    function: Callable[..., _MemoValue], *args: Any, **kwargs: Any
) -> _MemoValue:
    hook = current_hook()
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
    return current_hook().use_state(lru_cache(maxsize, typed), function)


async def use_frame_rate(rate: float = 0) -> None:
    await current_hook().use_state(FramePacer, rate).wait()


class FramePacer:
    """Simple utility for pacing frames in an animation loop."""

    __slots__ = "_rate", "_last"

    def __init__(self, rate: float):
        self._rate = rate
        self._last = time.time()

    async def wait(self) -> None:
        await asyncio.sleep(self._rate - (time.time() - self._last))
        self._last = time.time()
