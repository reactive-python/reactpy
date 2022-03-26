from __future__ import annotations

import shutil
import time
from functools import wraps
from inspect import iscoroutinefunction
from typing import Any, Awaitable, Callable, Generic, Optional, TypeVar, cast
from uuid import uuid4
from weakref import ref

from typing_extensions import ParamSpec, Protocol

from idom.config import IDOM_WEB_MODULES_DIR
from idom.core.events import EventHandler, to_event_handler_function
from idom.core.hooks import LifeCycleHook, current_hook


def clear_idom_web_modules_dir() -> None:
    """Clear the directory where IDOM stores registered web modules"""
    for path in IDOM_WEB_MODULES_DIR.current.iterdir():
        shutil.rmtree(path) if path.is_dir() else path.unlink()


_P = ParamSpec("_P")
_R = TypeVar("_R")
_RC = TypeVar("_RC", covariant=True)
_DEFAULT_TIMEOUT = 3.0


class _UntilFunc(Protocol[_RC]):
    def __call__(
        self, condition: Callable[[_RC], bool], timeout: float = _DEFAULT_TIMEOUT
    ) -> Any:
        ...


class poll(Generic[_R]):  # noqa: N801
    """Wait until the result of an sync or async function meets some condition"""

    def __init__(
        self,
        function: Callable[_P, Awaitable[_R] | _R],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> None:
        self.until: _UntilFunc[_R]
        """Check that the coroutines result meets a condition within the timeout"""

        if iscoroutinefunction(function):
            coro_function = cast(Callable[_P, Awaitable[_R]], function)

            async def coro_until(
                condition: Callable[[_R], bool], timeout: float = _DEFAULT_TIMEOUT
            ) -> None:
                started_at = time.time()
                while True:
                    result = await coro_function(*args, **kwargs)
                    if condition(result):
                        break
                    elif (time.time() - started_at) > timeout:  # pragma: no cover
                        raise TimeoutError(
                            f"Condition not met within {timeout} "
                            f"seconds - last value was {result!r}"
                        )

            self.until = coro_until
        else:
            sync_function = cast(Callable[_P, _R], function)

            def sync_until(
                condition: Callable[[_R], bool] | Any, timeout: float = _DEFAULT_TIMEOUT
            ) -> None:
                started_at = time.time()
                while True:
                    result = sync_function(*args, **kwargs)
                    if condition(result):
                        break
                    elif (time.time() - started_at) > timeout:  # pragma: no cover
                        raise TimeoutError(
                            f"Condition not met within {timeout} "
                            f"seconds - last value was {result!r}"
                        )

            self.until = sync_until

    def until_is(self, right: Any, timeout: float = _DEFAULT_TIMEOUT) -> Any:
        """Wait until the result is identical to the given value"""
        return self.until(lambda left: left is right, timeout)

    def until_equals(self, right: Any, timeout: float = _DEFAULT_TIMEOUT) -> Any:
        """Wait until the result is equal to the given value"""
        # not really sure why I need a type ignore comment here
        return self.until(lambda left: left == right, timeout)  # type: ignore


class HookCatcher:
    """Utility for capturing a LifeCycleHook from a component

    Example:
        .. code-block::

            hooks = HookCatcher(index_by_kwarg="thing")

            @idom.component
            @hooks.capture
            def MyComponent(thing):
                ...

            ...  # render the component

            # grab the last render of where MyComponent(thing='something')
            hooks.index["something"]
            # or grab the hook from the component's last render
            hooks.latest

        After the first render of ``MyComponent`` the ``HookCatcher`` will have
        captured the component's ``LifeCycleHook``.
    """

    latest: LifeCycleHook

    def __init__(self, index_by_kwarg: Optional[str] = None):
        self.index_by_kwarg = index_by_kwarg
        self.index: dict[Any, LifeCycleHook] = {}

    def capture(self, render_function: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator for capturing a ``LifeCycleHook`` on each render of a component"""

        # The render function holds a reference to `self` and, via the `LifeCycleHook`,
        # the component. Some tests check whether components are garbage collected, thus
        # we must use a `ref` here to ensure these checks pass once the catcher itself
        # has been collected.
        self_ref = ref(self)

        @wraps(render_function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self = self_ref()
            assert self is not None, "Hook catcher has been garbage collected"

            hook = current_hook()
            if self.index_by_kwarg is not None:
                self.index[kwargs[self.index_by_kwarg]] = hook
            self.latest = hook
            return render_function(*args, **kwargs)

        return wrapper


class StaticEventHandler:
    """Utility for capturing the target of one event handler

    Example:
        .. code-block::

            static_handler = StaticEventHandler()

            @idom.component
            def MyComponent():
                state, set_state = idom.hooks.use_state(0)
                handler = static_handler.use(lambda event: set_state(state + 1))
                return idom.html.button({"onClick": handler}, "Click me!")

            # gives the target ID for onClick where from the last render of MyComponent
            static_handlers.target

        If you need to capture event handlers from different instances of a component
        the you should create multiple ``StaticEventHandler`` instances.

        .. code-block::

            static_handlers_by_key = {
                "first": StaticEventHandler(),
                "second": StaticEventHandler(),
            }

            @idom.component
            def Parent():
                return idom.html.div(Child(key="first"), Child(key="second"))

            @idom.component
            def Child(key):
                state, set_state = idom.hooks.use_state(0)
                handler = static_handlers_by_key[key].use(lambda event: set_state(state + 1))
                return idom.html.button({"onClick": handler}, "Click me!")

            # grab the individual targets for each instance above
            first_target = static_handlers_by_key["first"].target
            second_target = static_handlers_by_key["second"].target
    """

    def __init__(self) -> None:
        self.target = uuid4().hex

    def use(
        self,
        function: Callable[..., Any],
        stop_propagation: bool = False,
        prevent_default: bool = False,
    ) -> EventHandler:
        return EventHandler(
            to_event_handler_function(function),
            stop_propagation,
            prevent_default,
            self.target,
        )
