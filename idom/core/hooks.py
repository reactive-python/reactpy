import time
import asyncio
from threading import get_ident as get_thread_id
from types import coroutine
from weakref import WeakValueDictionary, finalize
from typing import (
    Dict,
    Any,
    Awaitable,
    Iterator,
    TypeVar,
    Callable,
    Tuple,
    Optional,
    TYPE_CHECKING,
)

if TYPE_CHECKING:  # pragma: no cover
    from .element import AbstractElement
    from .layout import AbstractLayout


_UseState = TypeVar("_UseState")


def use_state(default: _UseState) -> Tuple[_UseState, Callable[[_UseState], None]]:
    hook = dispatch_hook()
    data = hook.use_state(dict)

    if "value" not in data:
        data["value"] = default

    def set_state(new: _UseState) -> None:
        data["value"] = new
        hook.update()

    return data["value"], set_state


_AnimFunc = Callable[[], Awaitable[None]]


async def use_frame_rate(rate: float = 0) -> None:
    await dispatch_hook().use_state(_FramePacer, rate).wait()


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


def dispatch_hook() -> "Hook":
    return current_hook_dispatcher().dispatch_hook()


def current_hook_dispatcher() -> "HookDispatcher":
    dispatcher = HookDispatcher.current_dispatcher()

    if dispatcher is None:
        raise RuntimeError(
            "No hook dispatcher is active. "
            "Did you render your element using a Layout, "
            "or call a hook outside an Element's render method?"
        )

    # return a proxy to avoid accidentally holding references to dispatcher
    return dispatcher


class Hook:

    __slots__ = "layout", "element", "_next_state_id", "_state"

    def __init__(self, layout: "AbstractLayout", element: "AbstractElement") -> None:
        self.layout = layout
        self.element = element
        self._next_state_id = 0
        self._state: Dict[int, Any] = {}

    def reset(self) -> None:
        self._next_state_id = 0

    def update(self) -> None:
        self.layout.update(self.element)

    def use_state(
        self,
        _constructor_: Callable[..., _HookData],
        *args: Tuple[Any, ...],
        **kwargs: Dict[str, Any]
    ) -> _HookData:
        state_id = self._next_state_id
        self._next_state_id += 1

        if state_id not in self._state:
            data = self._state[state_id] = _constructor_(*args, **kwargs)
        else:
            data = self._state[state_id]

        return data


class HookDispatcher:

    _current_dispatchers: Dict[int, "HookDispatcher"] = WeakValueDictionary()

    __slots__ = (
        "_hooks",
        "_layout",
        "_current_element",
        "__weakref__",
    )

    def __init__(self, layout: "AbstractLayout") -> None:
        self._layout = layout
        self._current_element: Optional["AbstractElement"] = None
        self._hooks: Dict[str, Hook] = {}

    @classmethod
    def current_dispatcher(cls) -> Optional["HookDispatcher"]:
        return cls._current_dispatchers.get(get_thread_id())

    def dispatch_hook(self) -> Hook:
        element = self._current_element
        element_id = element.id
        if element_id not in self._hooks:
            hook = self._hooks[element_id] = Hook(self._layout, element)
        else:
            hook = self._hooks[element_id]
        return hook

    @coroutine
    def render(self, element: "AbstractElement") -> Iterator[None]:
        """Render an element which may use hooks.

        We use a coroutine here because we need to know when control is yielded
        back to the event loop since it might switch to render a different element.
        """
        element_id = element.id
        if element_id not in self._hooks:
            finalize(element, self._hooks.pop, element_id, None)

        gen = element.render().__await__()

        try:
            while True:
                self._set_current_dispatcher()
                self._current_element = element
                try:
                    yield next(gen)
                except StopIteration as error:
                    return error.value
                finally:
                    self._current_element = None
                    self._unset_current_dispatcher()
        finally:
            if element_id in self._hooks:
                self._hooks[element_id].reset()

    def _set_current_dispatcher(self):
        self.__class__._current_dispatchers[get_thread_id()] = self

    @classmethod
    def _unset_current_dispatcher(cls):
        del cls._current_dispatchers[get_thread_id()]
