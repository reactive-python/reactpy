from threading import get_ident as get_thread_id
from types import coroutine
from weakref import WeakValueDictionary, finalize, ref, ReferenceType
from typing import (
    Dict,
    Any,
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


_HookData = TypeVar("_HookData")


def dispatch_hook() -> "Hook":
    dispatcher = HookDispatcher.current_dispatcher()

    if dispatcher is None:
        raise RuntimeError(
            "No hook dispatcher is active. "
            "Did you render your element using a Layout, "
            "or call a hook outside an Element's render method?"
        )

    return dispatcher.dispatch_hook()


class Hook:

    __slots__ = "_layout", "_element", "_current_state_index", "_state", "_finalized"

    def __init__(
        self, layout: "AbstractLayout", element: "ReferenceType[AbstractElement]"
    ) -> None:
        self._layout = layout
        self._element = element
        self._current_state_index = 0
        self._state: Tuple[Any, ...] = ()
        self._finalized = False

    @property
    def element(self) -> "AbstractElement":
        return self._element()

    def reset(self) -> None:
        self._current_state_index = 0
        self._finalized = True

    def create_update_callback(self) -> Callable[[], None]:
        element = self._element()  # deref to keep element alive
        if element is not None:
            # BUG: addressed by https://github.com/python/mypy/issues/2608
            return lambda: self._layout.update(element)  # type: ignore
        else:
            raise RuntimeError(f"Element for hook {self} no longer exists.")

    def on_unmount(
        self, _function_: Callable[..., None], *args: Any, **kwargs: Any
    ) -> None:
        if not self._finalized:
            finalize(self._element(), _function_, *args, **kwargs)

    def use_state(
        self, _function_: Callable[..., _HookData], *args: Any, **kwargs: Any
    ) -> _HookData:
        if not self._finalized:
            # since we're not intialized yet we're just appending state
            result = _function_(*args, **kwargs)
            self._state += (result,)
        else:
            # once finalized we iterate over each succesively used piece of state
            result = self._state[self._current_state_index]
        self._current_state_index += 1
        return result


class HookDispatcher:

    _current_dispatchers: "WeakValueDictionary[int, HookDispatcher]" = WeakValueDictionary()

    __slots__ = "_hooks", "_layout", "_current_element", "__weakref__"

    def __init__(self, layout: "AbstractLayout") -> None:
        self._layout = layout
        self._current_element: Optional[AbstractElement] = None
        self._hooks: Dict[str, Hook] = {}

    @classmethod
    def current_dispatcher(cls) -> Optional["HookDispatcher"]:
        return cls._current_dispatchers.get(get_thread_id())

    def dispatch_hook(self) -> Hook:
        element = self._current_element
        if element is None:
            raise RuntimeError(f"Hook dispatcher {self} is not rendering any element")
        element_id = element.id
        if element_id not in self._hooks:
            hook = self._hooks[element_id] = Hook(self._layout, ref(element))
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

    def _set_current_dispatcher(self) -> None:
        self.__class__._current_dispatchers[get_thread_id()] = self

    @classmethod
    def _unset_current_dispatcher(cls) -> None:
        del cls._current_dispatchers[get_thread_id()]
