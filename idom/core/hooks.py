import time
import asyncio
from functools import lru_cache
from typing import Dict, Any, TypeVar, Callable, Tuple, Optional, Type

from ._hooks import dispatch_hook, CreateContext, Context


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
    return dispatch_hook().use_update()


_StateType = TypeVar("_StateType")


def use_state(value: _StateType) -> Tuple[_StateType, Callable[[_StateType], None]]:
    hook = dispatch_hook()
    state: Dict[str, Any] = hook.use_state(dict)
    update = hook.use_update()

    if "value" not in state:
        state["value"] = value

    def set_state(new: _StateType) -> None:
        old = state["value"]
        if new is not old:
            state["value"] = new
            update()

    return state["value"], set_state


def _new_is_not_old(new: _StateType, old: _StateType) -> bool:
    return new is not old


def use_context(
    context_type: Type[Context[_StateType]],
    should_update: Callable[[_StateType, _StateType], bool] = _new_is_not_old,
) -> Tuple[_StateType, Callable[[_StateType], None]]:
    return dispatch_hook().use_context(context_type, should_update)


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
