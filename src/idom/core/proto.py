"""
Core Interfaces
===============
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, Callable, Optional, Type, TypeVar

from typing_extensions import Protocol, runtime_checkable

from .vdom import VdomDict


ComponentConstructor = Callable[..., "ComponentType"]


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
