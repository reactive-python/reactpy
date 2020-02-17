import abc
from asyncio import AbstractEventLoop
from typing import TypeVar, Dict, Any, Tuple, Type, Optional, Generic, TypeVar
from threading import Thread

from idom.core.element import ElementConstructor, AbstractElement
from idom.core.layout import AbstractLayout, Layout
from idom.core.render import AbstractRenderer


_App = TypeVar("_App", bound=Any)
_Config = TypeVar("_Config", bound=Any)
_Self = TypeVar("_Self", bound="AbstractRenderServer[Any, Any]")


class AbstractRenderServer(Generic[_App, _Config]):
    """Base class for all IDOM server application and extension implementations.

    It is assumed that IDOM will be used in conjuction with some async-enabled server
    library (e.g. ``sanic`` or ``tornado``) so these server implementations should work
    standalone and as an extension to an existing application.

    Standalone usage:
        :meth:`AbstractServerExtension.run` or :meth:`AbstractServerExtension.daemon`
    Register an extension:
        :meth:`AbstractServerExtension.register`
    """

    _renderer_type: Type[AbstractRenderer]
    _layout_type: Type[AbstractLayout] = Layout

    def __init__(
        self, constructor: ElementConstructor, *args: Any, **kwargs: Any
    ) -> None:
        self._app: Optional[_App] = None
        self._root_element_constructor = constructor
        self._root_element_args = args
        self._root_element_kwargs = kwargs
        self._daemonized = False
        self._config = self._init_config()

    @property
    def application(self) -> _App:
        if self._app is None:
            raise RuntimeError("No application registered.")
        return self._app

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run as a standalone application."""
        if self._app is None:
            app = self._default_application(self._config)
            self.register(app)
        else:
            app = self._app
        return self._run_application(app, self._config, args, kwargs)

    def daemon(self, *args: Any, **kwargs: Any) -> Thread:
        """Run the standalone application in a seperate thread."""
        self._daemonized = True
        thread = Thread(target=self.run, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread

    def register(self: _Self, app: _App) -> _Self:
        """Register this as an extension."""
        self._setup_application(app, self._config)
        self._app = app
        return self

    def configure(self: _Self, config: _Config) -> _Self:
        """Configure this extension."""
        self._config = self._update_config(self._config, config)
        return self

    @abc.abstractmethod
    def _init_config(self) -> _Config:
        """Return the default configuration options."""

    @abc.abstractmethod
    def _default_application(self, config: _Config) -> _App:
        """If used standalone this should return an application."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _setup_application(self, app: _App, config: _Config) -> None:
        ...

    @abc.abstractmethod
    def _run_application(
        self, app: _App, config: _Config, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> Any:
        ...

    def _update_config(self, old: _Config, new: _Config) -> _Config:
        """Return the new configuration options

        Parameters:
            old: The existing configuration options
            new: The new configuration options
        """
        return new

    def _make_renderer(
        self, loop: Optional[AbstractEventLoop] = None
    ) -> AbstractRenderer:
        return self._renderer_type(self._make_layout(loop))

    def _make_layout(self, loop: Optional[AbstractEventLoop] = None) -> AbstractLayout:
        return self._layout_type(self._make_root_element(), loop)

    def _make_root_element(self) -> AbstractElement:
        return self._root_element_constructor(
            *self._root_element_args, **self._root_element_kwargs
        )
