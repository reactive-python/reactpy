from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

CarrierType = TypeVar("CarrierType")


@dataclass
class Connection(Generic[CarrierType]):
    """Represents a connection with a client"""

    scope: MutableMapping[str, Any]
    """An ASGI scope or WSGI environment dictionary"""

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

    pathname: str
    """the path of the URL for the location"""

    search: str
    """A search or query string - a '?' followed by the parameters of the URL.

    If there are no search parameters this should be an empty string
    """
