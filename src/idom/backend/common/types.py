from __future__ import annotations

import asyncio
from asyncio import TimeoutError, create_task
from dataclasses import dataclass
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Generic,
    MutableMapping,
    TypedDict,
    TypeVar,
    Union,
    get_type_hints,
)

from typing_extensions import Literal, Protocol, TypeGuard, runtime_checkable

from idom.core.types import RootComponentConstructor


_App = TypeVar("_App")


@runtime_checkable
class BackendImplementation(Protocol[_App]):
    """Common interface for built-in web server/framework integrations"""

    Options: Callable[..., Any]
    """A constructor for options passed to :meth:`BackendImplementation.configure`"""

    def configure(
        self,
        app: _App,
        component: RootComponentConstructor,
        options: Any | None = None,
    ) -> None:
        """Configure the given app instance to display the given component"""

    def create_development_app(self) -> _App:
        """Create an application instance for development purposes"""

    async def serve_development_app(
        self,
        app: _App,
        host: str,
        port: int,
        started: asyncio.Event | None = None,
    ) -> None:
        """Run an application using a development server"""


_Carrier = TypeVar("_Carrier")


@dataclass
class Connection(Generic[_Carrier]):
    """Represents a connection with a client"""

    scope: MutableMapping[str, Any]
    """An ASGI scope or WSGI environment dictionary"""

    location: Location
    """The current location (URL)"""

    carrier: _Carrier
    """How the connection is mediated. For example, a request or websocket.

    This typically depends on the backend implementation.
    """


@dataclass
class Location:
    """Represents the current location (URL)

    Analogous to, but not necessarily identical to, the client-side
    ``document.location`` object.
    """

    pathname: str
    """the path of the URL for the location"""

    search: str
    """A search or query string - a '?' followed by the parameters of the URL.

    If there are no search parameters this should be an empty string
    """


_Type = TypeVar("_Type")


def _make_message_type_guard(
    msg_type: type[_Type],
) -> Callable[[Any], TypeGuard[_Type]]:
    annotations = get_type_hints(msg_type)
    type_anno_args = getattr(annotations["type"], "__args__")
    assert (
        isinstance(type_anno_args, tuple)
        and len(type_anno_args) == 1
        and isinstance(type_anno_args[0], str)
    )
    expected_type = type_anno_args[0]

    def type_guard(value: _Type) -> TypeGuard[_Type]:
        assert isinstance(value, dict)
        return value["type"] == expected_type

    type_guard.__doc__ = f"Check wheter the given value is a {expected_type!r} message"

    return type_guard


ServerMessageType = Union[
    "ServerHandshakeMessage",
    "LayoutUpdateMessage",
]

ClientMessageType = Union[
    "ClientHandshakeMessage",
    "LayoutEventMessage",
    "FileUploadMessage",
]

ServerHandshakeMessage = TypedDict(
    "ServerHandshakeMessage",
    {
        "type": Literal["server-handshake"],
        "version": str,
    },
)
is_server_handshake_message = _make_message_type_guard(ServerHandshakeMessage)

ClientHandshakeMessage = TypedDict(
    "ClientHandshakeMessage",
    {
        "type": Literal["client-handshake"],
        "version": str,
    },
)
is_client_handshake_message = _make_message_type_guard(ClientHandshakeMessage)

LayoutUpdateMessage = TypedDict(
    "LayoutUpdateMessage",
    {
        "type": Literal["layout-update"],
        "data": "list[Any]",
        "files": "list[str]",
    },
)
is_layout_udpate_message = _make_message_type_guard(LayoutUpdateMessage)

LayoutEventMessage = TypedDict(
    "LayoutEventMessage",
    {
        "type": Literal["layout-event"],
        "data": "list[Any]",
        "files": "list[str]",
    },
)
is_layout_event_message = _make_message_type_guard(LayoutEventMessage)

FileUploadMessage = TypedDict(
    "FileUploadMessage",
    {
        "type": Literal["file-upload"],
        "file": str,
        "data": bytes,
        "bytes-chunk-size": int,
        "bytes-sent": int,
        "bytes-remaining": int,
    },
)
is_file_upload_message = _make_message_type_guard(FileUploadMessage)
