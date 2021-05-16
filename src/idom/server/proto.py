from __future__ import annotations

from typing import Optional, TypeVar

from idom.core.component import ComponentConstructor


try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol  # type: ignore


_App = TypeVar("_App")
_Config = TypeVar("_Config", contravariant=True)


class ServerFactory(Protocol[_App, _Config]):
    """Setup a :class:`Server`"""

    def __call__(
        self,
        constructor: ComponentConstructor,
        config: Optional[_Config] = None,
        app: Optional[_App] = None,
    ) -> Server[_App]:
        ...


class Server(Protocol[_App]):
    """An object representing a server prepared to support IDOM's protocols"""

    app: _App
    """The server's underlying application"""

    def run(self, host: str, port: int) -> None:
        """Start running the server"""

    def run_in_thread(self, host: str, port: int) -> None:
        """Run the server in a thread"""

    def wait_until_started(self, timeout: Optional[float] = None) -> None:
        """Block until the server is able to receive requests"""

    def stop(self, timeout: Optional[float] = None) -> None:
        """Stop the running server"""
