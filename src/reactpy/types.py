from __future__ import annotations

import sys
from collections import namedtuple
from collections.abc import Awaitable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Literal,
    NamedTuple,
    NotRequired,
    Protocol,
    TypeVar,
    overload,
    runtime_checkable,
)

from typing_extensions import TypeAlias, TypedDict

CarrierType = TypeVar("CarrierType")
_Type = TypeVar("_Type")


if TYPE_CHECKING or sys.version_info >= (3, 11):

    class State(NamedTuple, Generic[_Type]):
        value: _Type
        set_value: Callable[[_Type | Callable[[_Type], _Type]], None]

else:  # nocov
    State = namedtuple("State", ("value", "set_value"))


ComponentConstructor = Callable[..., "ComponentType"]
"""Simple function returning a new component"""

RootComponentConstructor = Callable[[], "ComponentType"]
"""The root component should be constructed by a function accepting no arguments."""


Key: TypeAlias = str | int


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


_Render_co = TypeVar("_Render_co", covariant=True)
_Event_contra = TypeVar("_Event_contra", contravariant=True)


@runtime_checkable
class LayoutType(Protocol[_Render_co, _Event_contra]):
    """Renders and delivers, updates to views and events to handlers, respectively"""

    async def render(
        self,
    ) -> _Render_co: ...  # Render an update to a view

    async def deliver(
        self, event: _Event_contra
    ) -> None: ...  # Relay an event to its respective handler

    async def __aenter__(
        self,
    ) -> LayoutType[
        _Render_co, _Event_contra
    ]: ...  # Prepare the layout for its first render

    async def __aexit__(
        self,
        exc_type: type[Exception],
        exc_value: Exception,
        traceback: TracebackType,
    ) -> bool | None:
        """Clean up the view after its final render"""


EventFunc = Callable[[dict[str, Any]], Awaitable[None] | None]

# TODO: It's probably better to break this one attributes dict down into what each specific
# HTML node's attributes can be, and make sure those types are resolved correctly within `HtmlConstructor`
_VdomAttributes = TypedDict(
    "_VdomAttributes",
    {
        "key": Key,
        "value": Any,
        "defaultValue": Any,
        "dangerouslySetInnerHTML": dict[str, str],
        "suppressContentEditableWarning": bool,
        "suppressHydrationWarning": bool,
        "style": dict[str, Any],
        "accessKey": str,
        "aria-": None,
        "autoCapitalize": str,
        "className": str,
        "contentEditable": bool,
        "data-": None,
        "dir": Literal["ltr", "rtl"],
        "draggable": bool,
        "enterKeyHint": str,
        "htmlFor": str,
        "hidden": bool | str,
        "id": str,
        "is": str,
        "inputMode": str,
        "itemProp": str,
        "lang": str,
        "onAnimationEnd": EventFunc,
        "onAnimationEndCapture": EventFunc,
        "onAnimationIteration": EventFunc,
        "onAnimationIterationCapture": EventFunc,
        "onAnimationStart": EventFunc,
        "onAnimationStartCapture": EventFunc,
        "onAuxClick": EventFunc,
        "onAuxClickCapture": EventFunc,
        "onBeforeInput": EventFunc,
        "onBeforeInputCapture": EventFunc,
        "onBlur": EventFunc,
        "onBlurCapture": EventFunc,
        "onClick": EventFunc,
        "onClickCapture": EventFunc,
        "onCompositionStart": EventFunc,
        "onCompositionStartCapture": EventFunc,
        "onCompositionEnd": EventFunc,
        "onCompositionEndCapture": EventFunc,
        "onCompositionUpdate": EventFunc,
        "onCompositionUpdateCapture": EventFunc,
        "onContextMenu": EventFunc,
        "onContextMenuCapture": EventFunc,
        "onCopy": EventFunc,
        "onCopyCapture": EventFunc,
        "onCut": EventFunc,
        "onCutCapture": EventFunc,
        "onDoubleClick": EventFunc,
        "onDoubleClickCapture": EventFunc,
        "onDrag": EventFunc,
        "onDragCapture": EventFunc,
        "onDragEnd": EventFunc,
        "onDragEndCapture": EventFunc,
        "onDragEnter": EventFunc,
        "onDragEnterCapture": EventFunc,
        "onDragOver": EventFunc,
        "onDragOverCapture": EventFunc,
        "onDragStart": EventFunc,
        "onDragStartCapture": EventFunc,
        "onDrop": EventFunc,
        "onDropCapture": EventFunc,
        "onFocus": EventFunc,
        "onFocusCapture": EventFunc,
        "onGotPointerCapture": EventFunc,
        "onGotPointerCaptureCapture": EventFunc,
        "onKeyDown": EventFunc,
        "onKeyDownCapture": EventFunc,
        "onKeyPress": EventFunc,
        "onKeyPressCapture": EventFunc,
        "onKeyUp": EventFunc,
        "onKeyUpCapture": EventFunc,
        "onLostPointerCapture": EventFunc,
        "onLostPointerCaptureCapture": EventFunc,
        "onMouseDown": EventFunc,
        "onMouseDownCapture": EventFunc,
        "onMouseEnter": EventFunc,
        "onMouseLeave": EventFunc,
        "onMouseMove": EventFunc,
        "onMouseMoveCapture": EventFunc,
        "onMouseOut": EventFunc,
        "onMouseOutCapture": EventFunc,
        "onMouseUp": EventFunc,
        "onMouseUpCapture": EventFunc,
        "onPointerCancel": EventFunc,
        "onPointerCancelCapture": EventFunc,
        "onPointerDown": EventFunc,
        "onPointerDownCapture": EventFunc,
        "onPointerEnter": EventFunc,
        "onPointerLeave": EventFunc,
        "onPointerMove": EventFunc,
        "onPointerMoveCapture": EventFunc,
        "onPointerOut": EventFunc,
        "onPointerOutCapture": EventFunc,
        "onPointerUp": EventFunc,
        "onPointerUpCapture": EventFunc,
        "onPaste": EventFunc,
        "onPasteCapture": EventFunc,
        "onScroll": EventFunc,
        "onScrollCapture": EventFunc,
        "onSelect": EventFunc,
        "onSelectCapture": EventFunc,
        "onTouchCancel": EventFunc,
        "onTouchCancelCapture": EventFunc,
        "onTouchEnd": EventFunc,
        "onTouchEndCapture": EventFunc,
        "onTouchMove": EventFunc,
        "onTouchMoveCapture": EventFunc,
        "onTouchStart": EventFunc,
        "onTouchStartCapture": EventFunc,
        "onTransitionEnd": EventFunc,
        "onTransitionEndCapture": EventFunc,
        "onWheel": EventFunc,
        "onWheelCapture": EventFunc,
        "role": str,
        "slot": str,
        "spellCheck": bool | None,
        "tabIndex": int,
        "title": str,
        "translate": Literal["yes", "no"],
        "onReset": EventFunc,
        "onResetCapture": EventFunc,
        "onSubmit": EventFunc,
        "onSubmitCapture": EventFunc,
        "formAction": str | Callable,
        "checked": bool,
        "defaultChecked": bool,
        "accept": str,
        "alt": str,
        "capture": str,
        "autoComplete": str,
        "autoFocus": bool,
        "dirname": str,
        "disabled": bool,
        "form": str,
        "formEnctype": str,
        "formMethod": str,
        "formNoValidate": str,
        "formTarget": str,
        "height": str,
        "list": str,
        "max": int,
        "maxLength": int,
        "min": int,
        "minLength": int,
        "multiple": bool,
        "name": str,
        "onChange": EventFunc,
        "onChangeCapture": EventFunc,
        "onInput": EventFunc,
        "onInputCapture": EventFunc,
        "onInvalid": EventFunc,
        "onInvalidCapture": EventFunc,
        "pattern": str,
        "placeholder": str,
        "readOnly": bool,
        "required": bool,
        "size": int,
        "src": str,
        "step": int | Literal["any"],
        "type": str,
        "width": str,
        "label": str,
        "cols": int,
        "rows": int,
        "wrap": Literal["hard", "soft", "off"],
        "rel": str,
        "precedence": str,
        "media": str,
        "onError": EventFunc,
        "onLoad": EventFunc,
        "as": str,
        "imageSrcSet": str,
        "imageSizes": str,
        "sizes": str,
        "href": str,
        "crossOrigin": str,
        "referrerPolicy": str,
        "fetchPriority": str,
        "hrefLang": str,
        "integrity": str,
        "blocking": str,
        "async": bool,
        "noModule": bool,
        "nonce": str,
        "referrer": str,
        "defer": str,
        "onToggle": EventFunc,
        "onToggleCapture": EventFunc,
        "onLoadCapture": EventFunc,
        "onErrorCapture": EventFunc,
        "onAbort": EventFunc,
        "onAbortCapture": EventFunc,
        "onCanPlay": EventFunc,
        "onCanPlayCapture": EventFunc,
        "onCanPlayThrough": EventFunc,
        "onCanPlayThroughCapture": EventFunc,
        "onDurationChange": EventFunc,
        "onDurationChangeCapture": EventFunc,
        "onEmptied": EventFunc,
        "onEmptiedCapture": EventFunc,
        "onEncrypted": EventFunc,
        "onEncryptedCapture": EventFunc,
        "onEnded": EventFunc,
        "onEndedCapture": EventFunc,
        "onLoadedData": EventFunc,
        "onLoadedDataCapture": EventFunc,
        "onLoadedMetadata": EventFunc,
        "onLoadedMetadataCapture": EventFunc,
        "onLoadStart": EventFunc,
        "onLoadStartCapture": EventFunc,
        "onPause": EventFunc,
        "onPauseCapture": EventFunc,
        "onPlay": EventFunc,
        "onPlayCapture": EventFunc,
        "onPlaying": EventFunc,
        "onPlayingCapture": EventFunc,
        "onProgress": EventFunc,
        "onProgressCapture": EventFunc,
        "onRateChange": EventFunc,
        "onRateChangeCapture": EventFunc,
        "onResize": EventFunc,
        "onResizeCapture": EventFunc,
        "onSeeked": EventFunc,
        "onSeekedCapture": EventFunc,
        "onSeeking": EventFunc,
        "onSeekingCapture": EventFunc,
        "onStalled": EventFunc,
        "onStalledCapture": EventFunc,
        "onSuspend": EventFunc,
        "onSuspendCapture": EventFunc,
        "onTimeUpdate": EventFunc,
        "onTimeUpdateCapture": EventFunc,
        "onVolumeChange": EventFunc,
        "onVolumeChangeCapture": EventFunc,
        "onWaiting": EventFunc,
        "onWaitingCapture": EventFunc,
    },
    total=False,
    # extra_items=Any,
)

# TODO: Enable `extra_items` when PEP 728 is merged, likely in Python 3.14. Ref: https://peps.python.org/pep-0728/
VdomAttributes = _VdomAttributes | dict[str, Any]


class VdomDict(TypedDict):
    """A :ref:`VDOM` dictionary"""

    tagName: str
    key: NotRequired[Key | None]
    children: NotRequired[Sequence[ComponentType | VdomChild]]
    attributes: NotRequired[VdomAttributes]
    eventHandlers: NotRequired[EventHandlerDict]
    importSource: NotRequired[ImportSourceDict]


VdomChild: TypeAlias = ComponentType | VdomDict | str | None | Any
"""A single child element of a :class:`VdomDict`"""

VdomChildren: TypeAlias = Sequence[VdomChild] | VdomChild
"""Describes a series of :class:`VdomChild` elements"""


class ImportSourceDict(TypedDict):
    source: str
    fallback: Any
    sourceType: str
    unmountBeforeUpdate: bool


class VdomJson(TypedDict):
    """A JSON serializable form of :class:`VdomDict` matching the :data:`VDOM_JSON_SCHEMA`"""

    tagName: str
    key: NotRequired[Key]
    error: NotRequired[str]
    children: NotRequired[list[Any]]
    attributes: NotRequired[VdomAttributes]
    eventHandlers: NotRequired[dict[str, JsonEventTarget]]
    importSource: NotRequired[JsonImportSource]


class JsonEventTarget(TypedDict):
    target: str
    preventDefault: bool
    stopPropagation: bool


class JsonImportSource(TypedDict):
    source: str
    fallback: Any


class EventHandlerFunc(Protocol):
    """A coroutine which can handle event data"""

    async def __call__(self, data: Sequence[Any]) -> None: ...


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
    triggered programmatically.

    .. note::

        When ``None``, it is left to a :class:`LayoutType` to auto generate a unique ID.
    """


EventHandlerMapping = Mapping[str, EventHandlerType]
"""A generic mapping between event names to their handlers"""

EventHandlerDict: TypeAlias = dict[str, EventHandlerType]
"""A dict mapping between event names to their handlers"""


class VdomDictConstructor(Protocol):
    """Standard function for constructing a :class:`VdomDict`"""

    @overload
    def __call__(
        self, attributes: VdomAttributes, /, *children: VdomChildren
    ) -> VdomDict: ...

    @overload
    def __call__(self, *children: VdomChildren) -> VdomDict: ...

    def __call__(
        self, *attributes_and_children: VdomAttributes | VdomChildren
    ) -> VdomDict: ...


class LayoutUpdateMessage(TypedDict):
    """A message describing an update to a layout"""

    type: Literal["layout-update"]
    """The type of message"""
    path: str
    """JSON Pointer path to the model element being updated"""
    model: VdomJson | dict[str, Any]
    """The model to assign at the given JSON Pointer path"""


class LayoutEventMessage(TypedDict):
    """Message describing an event originating from an element in the layout"""

    type: Literal["layout-event"]
    """The type of message"""
    target: str
    """The ID of the event handler."""
    data: Sequence[Any]
    """A list of event data passed to the event handler."""


class Context(Protocol[_Type]):
    """Returns a :class:`ContextProvider` component"""

    def __call__(
        self,
        *children: Any,
        value: _Type = ...,
        key: Key | None = ...,
    ) -> ContextProviderType[_Type]: ...


class ContextProviderType(ComponentType, Protocol[_Type]):
    """A component which provides a context value to its children"""

    type: Context[_Type]
    """The context type"""

    @property
    def value(self) -> _Type: ...  # Current context value


@dataclass
class Connection(Generic[CarrierType]):
    """Represents a connection with a client"""

    scope: dict[str, Any]
    """A scope dictionary related to the current connection."""

    location: Location
    """The current location (URL)"""

    carrier: CarrierType
    """How the connection is mediated. For example, a request or websocket.

    This typically depends on the backend implementation.
    """


@dataclass
class Location:
    """Represents the current location (URL)

    Analogous to, but not necessarily identical to, the client-side
    ``document.location`` object.
    """

    path: str
    """The URL's path segment. This typically represents the current
    HTTP request's path."""

    query_string: str
    """HTTP query string - a '?' followed by the parameters of the URL.

    If there are no search parameters this should be an empty string
    """


class ReactPyConfig(TypedDict, total=False):
    path_prefix: str
    web_modules_dir: Path
    reconnect_interval: int
    reconnect_max_interval: int
    reconnect_max_retries: int
    reconnect_backoff_multiplier: float
    async_rendering: bool
    debug: bool
    tests_default_timeout: int


class PyScriptOptions(TypedDict, total=False):
    extra_py: Sequence[str]
    extra_js: dict[str, Any] | str
    config: dict[str, Any] | str
