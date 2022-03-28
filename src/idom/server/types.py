from __future__ import annotations

import asyncio
from typing import Any, MutableMapping, TypeVar

from typing_extensions import Protocol, runtime_checkable

from idom.types import RootComponentConstructor


_App = TypeVar("_App")


@runtime_checkable
class ServerImplementation(Protocol[_App]):
    """Common interface for IDOM's builti-in server implementations"""

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
