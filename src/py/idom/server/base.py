import abc
from asyncio import AbstractEventLoop
from typing import TypeVar, Dict, Any, Tuple, Type, Optional
from threading import Thread

from idom.core.element import ElementConstructor, AbstractElement
from idom.core.layout import AbstractLayout, Layout
from idom.core.render import AbstractRenderer


_S = TypeVar("_S", bound="AbstractRenderServer")
Config = Dict[str, Any]


class AbstractRenderServer(abc.ABC):
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
        self._app: Any = None
        self._root_element_constructor = constructor
        self._root_element_args = args
        self._root_element_kwargs = kwargs
        self._daemonized = False
        self._config: Config = {}
        self._init_config(self._config)

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run as a standalone application."""
        if self._app is None:
            self.register(self._default_application(self._config))
        return self._run_application(self._app, self._config, args, kwargs)

    def daemon(self, *args: Any, **kwargs: Any) -> Thread:
        """Run the standalone application in a seperate thread."""
        self._daemonized = True
        thread = Thread(target=self.run, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread

    def register(self: _S, app: Any) -> _S:
        """Register this as an extension."""
        self._setup_application(app, self._config)
        self._app = app
        return self

    def configure(self: _S, settings: Dict[str, Any]) -> _S:
        """Configure this extension."""
        for k, v in settings.items():
            if k not in self._config:
                raise ValueError(f"Unknown option {k!r}")
        self._config.update(settings)
        return self

    def _init_config(self, config: Config) -> None:
        """Set the default configuration options.

        Initialize configuration options by mutating the ``config`` dict.
        """

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

    def _get_renderer_event_loop(self) -> AbstractEventLoop:
        raise NotImplementedError()

    @abc.abstractmethod
    def _default_application(self, config: Config) -> Any:
        """If used standalone this should return an application."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _setup_application(self, app: Any, config: Config) -> None:
        ...

    @abc.abstractmethod
    def _run_application(
        self, app: Any, config: Config, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> Any:
        ...
