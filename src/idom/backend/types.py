from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, MutableMapping, TypeVar

from typing_extensions import Protocol, runtime_checkable

from idom.core.types import RootComponentConstructor


_App = TypeVar("_App")


@runtime_checkable
class BackendImplementation(Protocol[_App]):
    """Common interface for built-in web server/framework integrations"""

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

    def use_scope(self) -> MutableMapping[str, Any]:
        """Get an ASGI scope or WSGI environment dictionary"""

    def use_location(self) -> Location:
        """Get the current location (URL)"""


@dataclass
class Location:
    """Represents the current location (URL)

    Analogous to, but not necessarily identical to, the client-side
    ``document.location`` object.
    """

    pathname: str
    """the path of the URL for the location"""

    search: str = ""
    """A search or query string - a '?' followed by the parameters of the URL."""
