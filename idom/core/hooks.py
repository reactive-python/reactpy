import time
import asyncio
from threading import get_ident
from types import coroutine
from weakref import WeakValueDictionary, finalize
from collections import defaultdict
from typing import (
    Dict,
    Any,
    Awaitable,
    Iterator,
    TypeVar,
    Callable,
    Tuple,
    Optional,
    Type,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from .element import AbstractElement
    from .layout import AbstractLayout


_UseState = TypeVar("_UseState")


def use_state(default: _UseState) -> Tuple[_UseState, Callable[[_UseState], None]]:
    layout, element, data, is_first_usage = use_hook(dict)

    if is_first_usage:
        data["value"] = default

    def set_state(new: _UseState) -> None:
        data["value"] = new
        layout.update(element)

    return data["value"], set_state


_AnimFunc = Callable[[], Awaitable[None]]


async def use_rate_limit(rate: float = 0) -> None:
    layout, element, limiter, _ = use_hook(_FramePacer, rate)
    await limiter.wait()


class _FramePacer:
    """Simple utility for pacing frames in an animation loop."""

    __slots__ = "_rate", "_last"

    def __init__(self, rate: float):
        self._rate = rate
        self._last = time.time()

    async def wait(self) -> None:
        await asyncio.sleep(self._rate - (time.time() - self._last))
        self._last = time.time()


_HookData = TypeVar("_HookData")


def use_hook(
    data_type: Type[_HookData], *args: Any, **kwargs: Any
) -> Tuple["AbstractLayout", "AbstractElement", _HookData, bool]:
    return current_hook_dispatcher().use_hook(data_type, args, kwargs)


def use_update() -> Callable[[], None]:
    return current_hook_dispatcher().use_update()


def current_hook_dispatcher() -> "HookDispatcher":
    dispatcher = HookDispatcher.current()
    if dispatcher is None:
        raise RuntimeError(
            "No hook dispatcher is active. "
            "Did you render your element using a Layout, "
            "or call a hook outside an Element's render method?"
        )
    return dispatcher


class HookDispatcher:

    _dispatchers: Dict[int, "HookDispatcher"] = WeakValueDictionary()

    __slots__ = (
        "_layout",
        "_current_element",
        "_element_state",
        "__weakref__",
    )

    def __init__(self, layout: "AbstractLayout") -> None:
        self._layout = layout
        self._current_element: Optional["AbstractElement"] = None
        self._element_state: Dict[str, _HookState] = defaultdict(_HookState)

    @classmethod
    def current(cls) -> Optional["HookDispatcher"]:
        return cls._dispatchers.get(get_ident())

    @coroutine
    def render(self, element: "AbstractElement") -> Iterator[None]:
        """Render an element which may use hooks.

        We use a coroutine here because we need to know when control is yielded
        back to the event loop since it might switch to render a different element.
        """
        eid = element.id
        if eid not in self._element_state:
            finalize(element, self._element_state.pop, eid, None)

        gen = element.render().__await__()

        try:
            while True:
                self._set_current()
                self._current_element = element
                try:
                    yield next(gen)
                except StopIteration as error:
                    return error.value
                finally:
                    self._current_element = None
                    self._unset_current()
        finally:
            self._element_state[eid].reset_hook_id()

    def use_hook(
        self, data_type: Type[_HookData], args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> Tuple["AbstractLayout", "AbstractElement", _HookData, bool]:
        element = self._current_element
        assert element is not None

        hook_state = self._element_state[element.id]
        data, is_first_usage = hook_state.use_hook_data(data_type, args, kwargs)

        return self._layout, element, data, is_first_usage

    def use_update(self) -> Callable[[], None]:
        element = self._current_element
        assert element is not None
        layout = self._layout

        def update() -> None:
            layout.update(element)

        return update

    def _set_current(self):
        self.__class__._dispatchers[get_ident()] = self

    @classmethod
    def _unset_current(cls):
        del cls._dispatchers[get_ident()]


class _HookState:

    __slots__ = "_next_hook_id", "_hook_data"

    def __init__(self):
        self._next_hook_id = 0
        self._hook_data = {}

    def use_hook_data(
        self, data_type: Type[_HookData], args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> Tuple[_HookData, bool]:
        hook_id = self._next_hook_id
        self._next_hook_id += 1

        if hook_id in self._hook_data:
            is_first_usage = False
            data = self._hook_data[hook_id]
        else:
            is_first_usage = True
            data = self._hook_data[hook_id] = data_type(*args, **kwargs)

        return data, is_first_usage

    def reset_hook_id(self):
        self._next_hook_id = 0
