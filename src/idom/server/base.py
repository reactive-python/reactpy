import abc
from threading import Event, Thread
from typing import Any, Dict, Optional, Tuple, TypeVar

from idom.core.component import ComponentConstructor

from .proto import ServerFactory


_App = TypeVar("_App", bound=Any)
_Config = TypeVar("_Config", bound=Any)


class AbstractRenderServer(ServerFactory[_App, _Config], abc.ABC):
    """Base class for all IDOM server application and extension implementations.

    It is assumed that IDOM will be used in conjuction with some async-enabled server
    library (e.g. ``sanic`` or ``tornado``) so these server implementations should work
    standalone and as an extension to an existing application.

    Standalone usage:
        Construct the server then call ``:meth:`~AbstractRenderServer.run` or
        :meth:`~AbstractRenderServer.run_in_thread`
    Register as an extension:
        Simply construct the :meth:`~AbstractRenderServer` and pass it an ``app``
        instance.
    """

    def __init__(
        self,
        constructor: ComponentConstructor,
        config: Optional[_Config] = None,
        app: Optional[_App] = None,
    ) -> None:
        self._root_component_constructor = constructor
        self._daemon_thread: Optional[Thread] = None
        self._config = self._create_config(config)
        self._server_did_start = Event()
        self.app = app or self._default_application(self._config)
        self._setup_application(self._config, self.app)
        self._setup_application_did_start_event(
            self._config, self.app, self._server_did_start
        )

    def run(self, host: str, port: int, *args: Any, **kwargs: Any) -> None:
        """Run as a standalone application."""
        if self._daemon_thread is None:  # pragma: no cover
            return self._run_application(
                self._config, self.app, host, port, args, kwargs
            )
        else:
            return self._run_application_in_thread(
                self._config, self.app, host, port, args, kwargs
            )

    def run_in_thread(self, host: str, port: int, *args: Any, **kwargs: Any) -> Thread:
        """Run the standalone application in a seperate thread."""
        self._daemon_thread = thread = Thread(
            target=lambda: self.run(host, port, *args, **kwargs), daemon=True
        )

        thread.start()
        self.wait_until_started()

        return thread

    def wait_until_started(self, timeout: Optional[float] = 3.0) -> None:
        """Block until the underlying application has started"""
        if not self._server_did_start.wait(timeout=timeout):
            raise RuntimeError(  # pragma: no cover
                f"Server did not start within {timeout} seconds"
            )

    @abc.abstractmethod
    def stop(self, timeout: Optional[float] = None) -> None:
        """Stop a currently running application"""
        raise NotImplementedError()

    @abc.abstractmethod
    def _create_config(self, config: Optional[_Config]) -> _Config:
        """Return the default configuration options."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _default_application(self, config: _Config) -> _App:
        """If used standalone this should return an application."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _setup_application(self, config: _Config, app: _App) -> None:
        """General application setup - add routes, templates, static resource, etc."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _setup_application_did_start_event(
        self, config: _Config, app: _App, event: Event
    ) -> None:
        """Register a callback to the app indicating whether the server has started"""
        raise NotImplementedError()

    @abc.abstractmethod
    def _run_application(
        self,
        config: _Config,
        app: _App,
        host: str,
        port: int,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        """Run the application in the main thread"""
        raise NotImplementedError()

    @abc.abstractmethod
    def _run_application_in_thread(
        self,
        config: _Config,
        app: _App,
        host: str,
        port: int,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        """This function has been called inside a daemon thread to run the application"""
        raise NotImplementedError()

    def __repr__(self) -> str:
        cls = type(self)
        full_name = f"{cls.__module__}.{cls.__name__}"
        return f"{full_name}({self._config})"
