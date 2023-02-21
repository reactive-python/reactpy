from __future__ import annotations

import sys
from collections import namedtuple
from collections.abc import Sequence
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Mapping,
    NamedTuple,
    Type,
    TypeVar,
    overload,
)

from typing_extensions import Literal, Protocol, TypeAlias, TypedDict, runtime_checkable


_Type = TypeVar("_Type")


if TYPE_CHECKING or sys.version_info < (3, 9) or sys.version_info >= (3, 11):

    class State(NamedTuple, Generic[_Type]):
        value: _Type
        set_value: Callable[[_Type | Callable[[_Type], _Type]], None]

else:  # pragma: no cover
    State = namedtuple("State", ("value", "set_value"))


ComponentConstructor = Callable[..., "ComponentType"]
"""Simple function returning a new component"""

RootComponentConstructor = Callable[[], "ComponentType"]
"""The root component should be constructed by a function accepting no arguments."""


Key: TypeAlias = "str | int"


_OwnType = TypeVar("_OwnType")


@runtime_checkable
class ComponentType(Protocol):
    """The expected interface for all component-like objects"""

    key: Key | None
    """An identifier which is unique amongst a component's immediate siblings"""

    type: Any
    """The function or class defining the behavior of this component

    This is used to see if two component instances share the same definition.
    """

    def render(self) -> VdomDict | ComponentType | str | None:
        """Render the component's view model."""


_Render = TypeVar("_Render", covariant=True)
_Event = TypeVar("_Event", contravariant=True)


@runtime_checkable
class LayoutType(Protocol[_Render, _Event]):
    """Renders and delivers, updates to views and events to handlers, respectively"""

    async def render(self) -> _Render:
        """Render an update to a view"""

    async def deliver(self, event: _Event) -> None:
        """Relay an event to its respective handler"""

    async def __aenter__(self) -> LayoutType[_Render, _Event]:
        """Prepare the layout for its first render"""

    async def __aexit__(
        self,
        exc_type: Type[Exception],
        exc_value: Exception,
        traceback: TracebackType,
    ) -> bool | None:
        """Clean up the view after its final render"""


VdomAttributes = Mapping[str, Any]
"""Describes the attributes of a :class:`VdomDict`"""

VdomChild: TypeAlias = "ComponentType | VdomDict | str"
"""A single child element of a :class:`VdomDict`"""

VdomChildren: TypeAlias = "Sequence[VdomChild] | VdomChild"
"""Describes a series of :class:`VdomChild` elements"""


class _VdomDictOptional(TypedDict, total=False):
    key: Key | None
    children: Sequence[
        # recursive types are not allowed yet:
        # https://github.com/python/mypy/issues/731
        ComponentType
        | dict[str, Any]
        | str
        | Any
    ]
    attributes: VdomAttributes
    eventHandlers: EventHandlerDict  # noqa
    importSource: ImportSourceDict  # noqa


class _VdomDictRequired(TypedDict, total=True):
    tagName: str  # noqa


class VdomDict(_VdomDictRequired, _VdomDictOptional):
    """A :ref:`VDOM` dictionary"""


class ImportSourceDict(TypedDict):
    source: str
    fallback: Any
    sourceType: str  # noqa
    unmountBeforeUpdate: bool  # noqa


class _OptionalVdomJson(TypedDict, total=False):
    key: Key
    error: str
    children: list[Any]
    attributes: dict[str, Any]
    eventHandlers: dict[str, _JsonEventTarget]  # noqa
    importSource: _JsonImportSource  # noqa


class _RequiredVdomJson(TypedDict, total=True):
    tagName: str  # noqa


class VdomJson(_RequiredVdomJson, _OptionalVdomJson):
    """A JSON serializable form of :class:`VdomDict` matching the :data:`VDOM_JSON_SCHEMA`"""


class _JsonEventTarget(TypedDict):
    target: str
    preventDefault: bool  # noqa
    stopPropagation: bool  # noqa


class _JsonImportSource(TypedDict):
    source: str
    fallback: Any


EventHandlerMapping = Mapping[str, "EventHandlerType"]
"""A generic mapping between event names to their handlers"""

EventHandlerDict: TypeAlias = "dict[str, EventHandlerType]"
"""A dict mapping between event names to their handlers"""


class EventHandlerFunc(Protocol):
    """A coroutine which can handle event data"""

    async def __call__(self, data: Sequence[Any]) -> None:
        ...


@runtime_checkable
class EventHandlerType(Protocol):
    """Defines a handler for some event"""

    prevent_default: bool
    """Whether to block the event from propagating further up the DOM"""

    stop_propagation: bool
    """Stops the default action associate with the event from taking place."""

    function: EventHandlerFunc
    """A coroutine which can respond to an event and its data"""

    target: str | None
    """Typically left as ``None`` except when a static target is useful.

    When testing, it may be useful to specify a static target ID so events can be
    triggered programatically.

    .. note::

        When ``None``, it is left to a :class:`LayoutType` to auto generate a unique ID.
    """


class VdomDictConstructor(Protocol):
    """Standard function for constructing a :class:`VdomDict`"""

    @overload
    def __call__(self, attributes: VdomAttributes, *children: VdomChildren) -> VdomDict:
        ...

    @overload
    def __call__(self, *children: VdomChildren) -> VdomDict:
        ...

    @overload
    def __call__(
        self, *attributes_and_children: VdomAttributes | VdomChildren
    ) -> VdomDict:
        ...


class LayoutUpdateMessage(TypedDict):
    """A message describing an update to a layout"""

    type: Literal["layout-update"]
    """The type of message"""
    path: str
    """JSON Pointer path to the model element being updated"""
    model: VdomJson
    """The model to assign at the given JSON Pointer path"""


class LayoutEventMessage(TypedDict):
    """Message describing an event originating from an element in the layout"""

    type: Literal["layout-event"]
    """The type of message"""
    target: str
    """The ID of the event handler."""
    data: Sequence[Any]
    """A list of event data passed to the event handler."""
