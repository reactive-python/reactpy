from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Sequence
from functools import partial
from typing import Any, Literal, cast, overload

from anyio import create_task_group

from reactpy.core._event_inspect import inspect_event_handler
from reactpy.types import BaseEventHandler, EventHandlerFunc


def _unwrap_handler(function: Any) -> Any:
    """Get at the callable a user actually wrote, through wrappers and partials"""
    target = function
    while isinstance(target, partial):
        target = target.func
    return inspect.unwrap(target)


def _is_handler_coroutine(function: Any) -> bool:
    """Whether calling this object gives something awaitable

    :func:`inspect.iscoroutinefunction` says no to an object whose ``__call__`` is a
    coroutine, so that case is looked at directly.
    """
    target = _unwrap_handler(function)
    if inspect.iscoroutinefunction(target):
        return True
    call = type(target).__dict__.get("__call__", None)
    return call is not None and inspect.iscoroutinefunction(call)


def check_is_async_handler(function: Any) -> None:
    """Raise a :exc:`TypeError` unless ``function`` can be awaited as a handler

    Event handlers are always coroutines. There is no blocking flavour of event data,
    which is what makes it safe for a handler to call ``set_state()`` and keeps the
    layout's event loop free to render while a live value is fetched from the browser.
    """
    if _is_handler_coroutine(function):
        return

    name = getattr(function, "__qualname__", None) or repr(function)
    msg = (
        f"{name} cannot be used as an event handler because it is not a coroutine. "
        "Event handlers must be declared with 'async def':\n\n"
        "    async def on_click(event):\n        ...\n\n"
        "An event object reads from the browser as needed, and only a coroutine can "
        "await that round trip without stalling the event loop."
    )
    if name.startswith("_CurrentState.__init__") or name.endswith(".dispatch"):
        msg += (
            "\n\nA state setter is not an event handler - call it from one instead:\n\n"
            "    async def on_click(event):\n        set_value(...)"
        )
    raise TypeError(msg)


@overload
def event(
    function: Callable[..., Awaitable[Any]],
    *,
    stop_propagation: bool = ...,
    stop_immediate_propagation: bool = ...,
    prevent_default: bool = ...,
    debounce: int | None = ...,
    throttle: int | None = ...,
) -> EventHandler: ...


@overload
def event(
    function: Literal[None] = ...,
    *,
    stop_propagation: bool = ...,
    stop_immediate_propagation: bool = ...,
    prevent_default: bool = ...,
    debounce: int | None = ...,
    throttle: int | None = ...,
) -> Callable[[Callable[..., Awaitable[Any]]], EventHandler]: ...


def event(
    function: Callable[..., Awaitable[Any]] | None = None,
    *,
    stop_propagation: bool = False,
    stop_immediate_propagation: bool = False,
    prevent_default: bool = False,
    debounce: int | None = None,
    throttle: int | None = None,
) -> EventHandler | Callable[[Callable[..., Awaitable[Any]]], EventHandler]:
    """A decorator for constructing an :class:`EventHandler`.

    While you're always free to add callbacks by assigning them to an element's attributes

    .. code-block:: python

        element = reactpy.html.button({"onClick": my_callback})

    You may want the ability to prevent the default action associated with the event
    from taking place, or stopping the event from propagating up the DOM. This decorator
    allows you to add that functionality to your callbacks.

    .. code-block:: python

        @event(stop_propagation=True, prevent_default=True)
        async def my_callback(event): ...


        element = reactpy.html.button({"onClick": my_callback})

    The handler must be a coroutine. Anything which is not an ``async def`` raises a
    :exc:`TypeError`, because reading the object an event fired from means asking the
    browser for it, and only a coroutine can await that without stalling the layout.

    Parameters:
        function:
            A coroutine responsible for handling the event.
        stop_propagation:
            Block the event from propagating further up the DOM.
        prevent_default:
            Stops the default actional associate with the event from taking place.
        debounce:
            Rate-limit server-→client ``value`` updates for user-input elements.
            See :attr:`BaseEventHandler.debounce`.
        throttle:
            Rate-limit client-→server outgoing events for any element. See
            :attr:`BaseEventHandler.throttle`.
        stop_immediate_propagation:
            Also block any other listener of the same event in the browser.
    """

    def setup(function: Callable[..., Awaitable[Any]]) -> EventHandler:
        return EventHandler(
            to_event_handler_function(function, positional_args=True),
            stop_propagation,
            prevent_default,
            debounce=debounce,
            throttle=throttle,
            stop_immediate_propagation=stop_immediate_propagation,
        )

    return setup(function) if function is not None else setup


class EventHandler(BaseEventHandler):
    """Turn a coroutine into an event handler

    Parameters:
        function:
            The coroutine which handles the event. A plain ``def`` raises a
            :exc:`TypeError`, since only a coroutine can await the browser for the
            object an event fired from. See :func:`event`.
        stop_propagation:
            Block the event from propagating further up the DOM.
        prevent_default:
            Stops the default action associate with the event from taking place.
        target:
            A unique identifier for this event handler (auto-generated by default)
        debounce:
            Server-→client rate limit (ms) for ``value`` updates on user-input
            elements. See :attr:`BaseEventHandler.debounce`.
        throttle:
            Client-→server rate limit (ms) for outgoing events. See
            :attr:`BaseEventHandler.throttle`.
        stop_immediate_propagation:
            Also block any other listener of the same event in the browser.
    """

    def __init__(
        self,
        function: Callable[..., Awaitable[Any]],
        stop_propagation: bool = False,
        prevent_default: bool = False,
        target: str | None = None,
        debounce: int | None = None,
        throttle: int | None = None,
        stop_immediate_propagation: bool = False,
    ) -> None:
        check_is_async_handler(function)
        self.function = to_event_handler_function(function, positional_args=False)
        self.prevent_default = prevent_default
        self.stop_propagation = stop_propagation
        self.stop_immediate_propagation = stop_immediate_propagation
        self.debounce = debounce
        self.throttle = throttle
        self.target = target

        # Check what the handler says about the event it is handed by inspecting the
        # bytecode of the function the user actually wrote
        (
            found_prevent_default,
            found_stop_propagation,
            found_debounce,
        ) = inspect_event_handler(_unwrap_handler(function))

        if found_prevent_default:
            self.prevent_default = True
        if found_stop_propagation:
            self.stop_propagation = True
            if found_stop_propagation == "immediate":
                self.stop_immediate_propagation = True
        if found_debounce is not None:
            self.debounce = found_debounce

    __hash__ = None  # type: ignore

    _PUBLIC_ATTRS = (
        "function",
        "prevent_default",
        "stop_propagation",
        "stop_immediate_propagation",
        "debounce",
        "target",
        "throttle",
    )

    def __eq__(self, other: object) -> bool:
        undefined = object()
        return not any(
            not attr.startswith("_")
            and not getattr(other, attr, undefined) == getattr(self, attr)
            for attr in self._PUBLIC_ATTRS
        )

    def __repr__(self) -> str:
        items = ", ".join([f"{n}={getattr(self, n)!r}" for n in self._PUBLIC_ATTRS])
        return f"{type(self).__name__}({items})"


def to_event_handler_function(
    function: Callable[..., Awaitable[Any]],
    positional_args: bool = True,
) -> EventHandlerFunc:
    """Make a :data:`~reactpy.types.EventHandlerFunc` from an event handler coroutine

    Parameters:
        function:
            A coroutine accepting a number of positional arguments.
        positional_args:
            Whether to pass the event parameters as positional args or as a list.

    Handlers are always coroutines, and the :class:`~reactpy.types.Event` handed to them
    reaches back into the browser by being awaited. Nothing here ever blocks, which is
    what allows a handler to call ``set_state()`` from the loop it renders on.
    """
    check_is_async_handler(function)

    if positional_args:

        async def wrapper(data: Sequence[Any]) -> None:
            await function(*data)

        cast(Any, wrapper).__wrapped__ = function
        return wrapper

    return cast(EventHandlerFunc, function)


def merge_event_handlers(
    event_handlers: Sequence[BaseEventHandler],
) -> BaseEventHandler:
    """Merge multiple event handlers into one

    Raises a ValueError if any handlers have conflicting
    :attr:`~reactpy.core.proto.EventHandlerType.stop_propagation`,
    :attr:`~reactpy.core.proto.EventHandlerType.prevent_default`,
    :attr:`~reactpy.core.proto.EventHandlerType.debounce`,
    :attr:`~reactpy.core.proto.EventHandlerType.throttle` attributes.
    """
    if not event_handlers:
        msg = "No event handlers to merge"
        raise ValueError(msg)
    elif len(event_handlers) == 1:
        return event_handlers[0]

    first_handler = event_handlers[0]

    stop_propagation = first_handler.stop_propagation
    prevent_default = first_handler.prevent_default
    debounce = first_handler.debounce
    throttle = first_handler.throttle
    target = first_handler.target
    stop_immediate_propagation = getattr(
        first_handler, "stop_immediate_propagation", False
    )
    for handler in event_handlers:
        if (
            handler.stop_propagation != stop_propagation
            or handler.prevent_default != prevent_default
            or handler.debounce != debounce
            or handler.throttle != throttle
            or handler.target != target
            or getattr(handler, "stop_immediate_propagation", False)
            != stop_immediate_propagation
        ):
            msg = (
                "Cannot merge handlers - 'stop_propagation', 'prevent_default', "
                "'debounce', 'throttle', 'target', or "
                "'stop_immediate_propagation' mismatch."
            )
            raise ValueError(msg)

    return EventHandler(
        merge_event_handler_funcs([h.function for h in event_handlers]),
        stop_propagation,
        prevent_default,
        target,
        debounce,
        throttle,
        stop_immediate_propagation=stop_immediate_propagation,
    )


def merge_event_handler_funcs(
    functions: Sequence[EventHandlerFunc],
) -> EventHandlerFunc:
    """Make one event handler function from many

    Every handler is handed the very same event data. There is a single flavour of it,
    and each handler awaits whatever it needs from the browser in its own task.
    """
    if not functions:
        msg = "No event handler functions to merge"
        raise ValueError(msg)
    elif len(functions) == 1:
        return functions[0]

    async def await_all_event_handlers(data: Sequence[Any]) -> None:
        async with create_task_group() as group:
            for func in functions:
                group.start_soon(func, data)

    return await_all_event_handlers
