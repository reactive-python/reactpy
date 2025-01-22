from __future__ import annotations

import asyncio
import inspect
import shutil
import time
from collections.abc import Awaitable
from functools import wraps
from typing import Any, Callable, Generic, TypeVar, cast
from uuid import uuid4
from weakref import ref

from typing_extensions import ParamSpec

from reactpy.config import REACTPY_TESTING_DEFAULT_TIMEOUT, REACTPY_WEB_MODULES_DIR
from reactpy.core._life_cycle_hook import LifeCycleHook, current_hook
from reactpy.core.events import EventHandler, to_event_handler_function


def clear_reactpy_web_modules_dir() -> None:
    """Clear the directory where ReactPy stores registered web modules"""
    for path in REACTPY_WEB_MODULES_DIR.current.iterdir():
        shutil.rmtree(path) if path.is_dir() else path.unlink()


_P = ParamSpec("_P")
_R = TypeVar("_R")


_DEFAULT_POLL_DELAY = 0.1


class poll(Generic[_R]):  # noqa: N801
    """Wait until the result of an sync or async function meets some condition"""

    def __init__(
        self,
        function: Callable[_P, Awaitable[_R] | _R],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> None:
        coro: Callable[_P, Awaitable[_R]]
        if not inspect.iscoroutinefunction(function):

            async def coro(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                return cast(_R, function(*args, **kwargs))

        else:
            coro = cast(Callable[_P, Awaitable[_R]], function)
        self._func = coro
        self._args = args
        self._kwargs = kwargs

    async def until(
        self,
        condition: Callable[[_R], bool],
        timeout: float = REACTPY_TESTING_DEFAULT_TIMEOUT.current,
        delay: float = _DEFAULT_POLL_DELAY,
        description: str = "condition to be true",
    ) -> None:
        """Check that the coroutines result meets a condition within the timeout"""
        started_at = time.time()
        while True:
            await asyncio.sleep(delay)
            result = await self._func(*self._args, **self._kwargs)
            if condition(result):
                break
            elif (time.time() - started_at) > timeout:  # nocov
                msg = f"Expected {description} after {timeout} seconds - last value was {result!r}"
                raise asyncio.TimeoutError(msg)

    async def until_is(
        self,
        right: _R,
        timeout: float = REACTPY_TESTING_DEFAULT_TIMEOUT.current,
        delay: float = _DEFAULT_POLL_DELAY,
    ) -> None:
        """Wait until the result is identical to the given value"""
        return await self.until(
            lambda left: left is right,
            timeout,
            delay,
            f"value to be identical to {right!r}",
        )

    async def until_equals(
        self,
        right: _R,
        timeout: float = REACTPY_TESTING_DEFAULT_TIMEOUT.current,
        delay: float = _DEFAULT_POLL_DELAY,
    ) -> None:
        """Wait until the result is equal to the given value"""
        return await self.until(
            lambda left: left == right,
            timeout,
            delay,
            f"value to equal {right!r}",
        )


class HookCatcher:
    """Utility for capturing a LifeCycleHook from a component

    Example:
        .. code-block::

            hooks = HookCatcher(index_by_kwarg="thing")

            @reactpy.component
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

    def __init__(self, index_by_kwarg: str | None = None):
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
            if self is None:
                raise RuntimeError("Hook catcher has been garbage collected")

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

            @reactpy.component
            def MyComponent():
                state, set_state = reactpy.hooks.use_state(0)
                handler = static_handler.use(lambda event: set_state(state + 1))
                return reactpy.html.button({"onClick": handler}, "Click me!")

            # gives the target ID for onClick where from the last render of MyComponent
            static_handlers.target

        If you need to capture event handlers from different instances of a component
        the you should create multiple ``StaticEventHandler`` instances.

        .. code-block::

            static_handlers_by_key = {
                "first": StaticEventHandler(),
                "second": StaticEventHandler(),
            }

            @reactpy.component
            def Parent():
                return reactpy.html.div(Child(key="first"), Child(key="second"))

            @reactpy.component
            def Child(key):
                state, set_state = reactpy.hooks.use_state(0)
                handler = static_handlers_by_key[key].use(lambda event: set_state(state + 1))
                return reactpy.html.button({"onClick": handler}, "Click me!")

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
