import asyncio
from typing import Callable, TypeVar

from typing_extensions import Protocol, runtime_checkable

from idom.core.types import ComponentType


_App = TypeVar("_App")


@runtime_checkable
class ServerImplementation(Protocol):
    """Common interface for IDOM's builti-in server implementations"""

    def configure(self, app: _App, component: Callable[[], ComponentType]) -> None:
        """Configure the given app instance to display the given component"""

    def create_development_app(self) -> _App:
        """Create an application instance for development purposes"""

    async def serve_development_app(
        self, app: _App, host: str, port: int, started: asyncio.Event
    ) -> None:
        """Run an application using a development server"""
