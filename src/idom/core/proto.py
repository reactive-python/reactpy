"""
Core Interfaces
===============
"""

from __future__ import annotations

from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
)

from typing_extensions import Protocol, runtime_checkable


if TYPE_CHECKING:
    from .vdom import VdomDict


ComponentConstructor = Callable[..., "ComponentType"]
"""Simple function returning a new component"""


@runtime_checkable
class ComponentType(Protocol):
    """The expected interface for all component-like objects"""

    key: Optional[Any]
    """An identifier which is unique amongst a component's immediate siblings"""

    def render(self) -> VdomDict:
        """Render the component's :class:`VdomDict`."""


_Self = TypeVar("_Self")
_Render = TypeVar("_Render", covariant=True)
_Event = TypeVar("_Event", contravariant=True)


@runtime_checkable
class LayoutType(Protocol[_Render, _Event]):
    """Renders and delivers, updates to views and events to handlers, respectively"""

    async def render(self) -> _Render:
        """Render an update to a view"""

    async def deliver(self, event: _Event) -> None:
        """Relay an event to its respective handler"""

    def __enter__(self: _Self) -> _Self:
        """Prepare the layout for its first render"""

    def __exit__(
        self, exc_type: Type[Exception], exc_value: Exception, traceback: TracebackType
    ) -> Optional[bool]:
        """Clean up the view after its final render"""


EventHandlerMapping = Mapping[str, "EventHandlerType"]
"""A generic mapping between event names to their handlers"""

EventHandlerDict = Dict[str, "EventHandlerType"]
"""A dict mapping between event names to their handlers"""

EventHandlerFunc = Callable[[List[Any]], Awaitable[None]]
"""A coroutine which can handle event data"""


@runtime_checkable
class EventHandlerType(Protocol):
    """Defines a handler for some event"""

    prevent_default: bool
    """Whether to block the event from propagating further up the DOM"""

    stop_propagation: bool
    """Stops the default action associate with the event from taking place."""

    function: EventHandlerFunc
    """A coroutine which can respond to an event and its data"""

    target: Optional[str]
    """Typically left as ``None`` except when a static target is useful.

    When testing, it may be useful to specify a static target ID so events can be
    triggered programatically.

    .. note::

        When ``None`` it is left to a :class:`LayoutType` to auto generate a unique ID.
    """
