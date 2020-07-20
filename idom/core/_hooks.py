from contextlib import contextmanager
from threading import get_ident as get_thread_id
from types import coroutine
from weakref import WeakValueDictionary, finalize, ref, ReferenceType
from typing import (
    Dict,
    Any,
    Iterator,
    TypeVar,
    AsyncIterator,
    Generic,
    Callable,
    Tuple,
    Type,
    Optional,
    TypeVar,
    TYPE_CHECKING,
)

import idom

from .utils import asynccontextmanager
from .element import AbstractElement

if TYPE_CHECKING:  # pragma: no cover
    from .element import AbstractElement
    from .layout import AbstractLayout
    from .vdom import VdomDict


def current_hook() -> "Hook":
    return current_hook_dispatcher().current_hook()


_ContextData = TypeVar("_ContextData", bound=Optional[Any])


class Context(Generic[_ContextData]):

    __slots__ = "_callbacks", "_value"
    default_value: _ContextData

    def __init__(self, value: _ContextData):
        self._callbacks: Dict[str, Callable[[_ContextData], None]] = {}
        self._value = value

    @classmethod
    def Provider(
        cls, *children: Any, value: _ContextData
    ) -> "ContextProvider[_ContextData]":
        value = value if value is not ... else cls.default_value
        return ContextProvider(cls(value), children)


class CreateContext(type):
    def __new__(
        cls, name: str, default_value: _ContextData
    ) -> Type[Context[_ContextData]]:
        return super().__new__(cls, name, (Context,), {"default_value": default_value})

    def __init__(self, name: str, default_value: _ContextData) -> None:  # noqa
        pass


class ContextProvider(AbstractElement, Generic[_ContextData]):

    __slots__ = "_context", "_children"

    def __init__(
        self, context: Context[_ContextData], children: Tuple[Any, ...]
    ) -> None:
        super().__init__()
        self._context = context
        self._children = children

    async def render(self) -> "VdomDict":
        return idom.html.div(*self._children)


_HookData = TypeVar("_HookData")


class Hook:

    __slots__ = (
        "_dispatcher",
        "_layout",
        "_element",
        "_current_state_index",
        "_state",
        "_did_update",
        "_has_rendered",
    )

    def __init__(
        self,
        dispatcher: "HookDispatcher",
        layout: "AbstractLayout",
        element: "ReferenceType[AbstractElement]",
    ) -> None:
        self._dispatcher = dispatcher
        self._layout = layout
        self._element = element
        self._current_state_index = 0
        self._state: Tuple[Any, ...] = ()
        self._did_update = False
        self._has_rendered = False

    def element(self) -> "AbstractElement":
        element = self._element()
        if element is None:
            raise RuntimeError(f"Element for hook {self} no longer exists.")
        return element

    @contextmanager
    def enter(self) -> Iterator[None]:
        self._current_state_index = 0
        self._did_update = False
        yield
        self._has_rendered = True

    def use_update(self) -> Callable[[], None]:
        element = self.element()  # deref to keep element alive
        if element is not None:

            def update() -> None:
                if not self._did_update:
                    self._did_update = True
                    self._layout.update(element)

            return update
        else:
            raise RuntimeError(f"Element for hook {self} no longer exists.")

    def use_context(
        self,
        context_type: Type[Context[_ContextData]],
        should_update: Callable[[_ContextData, _ContextData], bool],
    ) -> Tuple[_ContextData, Callable[[_ContextData], None]]:
        context = self.use_state(lambda: self._dispatcher.get_context(context_type))

        if context is None:
            return context_type.default_value, None
        else:
            element_id = self.element().id
            update = self.use_update()
            self.use_finalizer(context._callbacks.pop, element_id, None)
            context._callbacks[element_id] = (
                lambda new, old=context._value: update()
                if should_update(new, old)
                else None
            )

            def set_state(new: _ContextData) -> None:
                context._value = new
                for cb in context._callbacks.values():
                    cb(new)

            return context._value, set_state

    def use_finalizer(
        self, _function_: Callable[..., None], *args: Any, **kwargs: Any
    ) -> None:
        if not self._has_rendered:
            finalize(self.element(), _function_, *args, **kwargs)

    def use_state(
        self, _function_: Callable[..., _HookData], *args: Any, **kwargs: Any
    ) -> _HookData:
        if not self._has_rendered:
            # since we're not intialized yet we're just appending state
            result = _function_(*args, **kwargs)
            self._state += (result,)
        else:
            # once finalized we iterate over each succesively used piece of state
            result = self._state[self._current_state_index]
        self._current_state_index += 1
        return result


_current_dispatchers: "WeakValueDictionary[int, HookDispatcher]" = WeakValueDictionary()


def current_hook_dispatcher() -> "HookDispatcher":
    dispatcher = _current_dispatchers.get(get_thread_id())

    if dispatcher is None:
        raise RuntimeError(
            "No hook dispatcher is active. "
            "Did you render your element using a Layout, "
            "or call a hook outside an Element's render method?"
        )

    return dispatcher


class HookDispatcher:

    __slots__ = (
        "_hooks",
        "_layout",
        "_current_element",
        "_active_contexts",
        "__weakref__",
    )

    def __init__(self, layout: "AbstractLayout") -> None:
        self._layout = layout
        self._active_contexts: Dict[Type[Context], Context] = {}
        self._current_element: Optional[AbstractElement] = None
        self._hooks: Dict[str, Hook] = {}

    async def unmount(self, element_id: str) -> None:
        hook = self._hooks.get(element_id)
        if hook is not None:
            self._hooks.umount()

    def current_hook(self) -> Hook:
        element = self._current_element
        if element is None:
            raise RuntimeError(f"Hook dispatcher {self} is not rendering any element")
        return self.get_hook(element)

    def get_hook(self, element: "AbstractElement") -> Hook:
        element_id = element.id
        if element_id not in self._hooks:
            hook = self._hooks[element_id] = Hook(self, self._layout, ref(element))
            finalize(element, self._hooks.pop, element_id, None)
        else:
            hook = self._hooks[element_id]
        return hook

    def get_context(
        self, context_type: Type[Context[_ContextData]]
    ) -> Optional[Context[_ContextData]]:
        return self._active_contexts.get(context_type)

    @asynccontextmanager
    async def render(self, element: "AbstractElement") -> AsyncIterator[Any]:
        if isinstance(element, ContextProvider):
            with self._activate_context_provider(element):
                with self.get_hook(element).enter():
                    yield await self._render(element)
        else:
            with self.get_hook(element).enter():
                yield await self._render(element)

    @coroutine
    def _render(self, element: "AbstractElement") -> Iterator[None]:
        """Render an element which may use hooks.

        We use a coroutine here because we need to know when control is yielded
        back to the event loop since it might switch to render a different element.
        """
        gen = element.render().__await__()
        while True:
            _current_dispatchers[get_thread_id()] = self
            self._current_element = element
            try:
                yield next(gen)
            except StopIteration as error:
                return error.value
            finally:
                self._current_element = None
                del _current_dispatchers[get_thread_id()]

    @contextmanager
    def _activate_context_provider(
        self, context_provider: ContextProvider
    ) -> Iterator[None]:
        context = context_provider._context
        context_type = type(context)
        if context_type in self._active_contexts:
            msg = f"Context {type(context)} has already been activated"
            raise RuntimeError(msg)
        self._active_contexts[context_type] = context
        try:
            yield
        finally:
            del self._active_contexts[context_type]
