import abc
from typing import TypeVar, Dict, Any, Tuple
from threading import Thread

from idom.core.element import ElementConstructor, Element


_S = TypeVar("_S", bound="AbstractServerExtension")
Config = Dict[str, Any]


class AbstractServerExtension(abc.ABC):
    def __init__(
        self, constructor: ElementConstructor, *args: Any, **kwargs: Any
    ) -> None:
        self._app: Any = None
        self._element_constructor = constructor
        self._element_args = args
        self._element_kwargs = kwargs
        self._daemonized = False
        self._config: Config = {}
        self._init_config(self._config)

    def register(self: _S, app: Any) -> _S:
        self._setup_application(app, self._config)
        self._app = app
        return self

    def configure(self: _S, settings: Dict[str, Any]) -> _S:
        for k, v in settings.items():
            if k not in self._config:
                raise ValueError(f"Unknown option {k!r}")
        self._config.update(settings)
        return self

    def run(self, *args: Any, **kwargs: Any) -> Any:
        if self._app is None:
            self.register(self._default_application(self._config))
        return self._run_application(self._app, self._config, args, kwargs)

    def daemon(self, *args: Any, **kwargs: Any) -> Thread:
        self._daemonized = True
        thread = Thread(target=self.run, args=args, kwargs=kwargs, daemon=True)
        thread.start()
        return thread

    def _init_config(self, config: Config) -> None:
        ...

    def _create_element(self) -> Element:
        return self._element_constructor(*self._element_args, **self._element_kwargs)

    @abc.abstractmethod
    def _default_application(self, config: Config) -> Any:
        raise NotImplementedError()

    @abc.abstractmethod
    def _setup_application(self, app: Any, config: Config) -> None:
        ...

    @abc.abstractmethod
    def _run_application(
        self, app: Any, config: Config, args: Tuple[Any, ...], kwargs: Dict[str, Any]
    ) -> Any:
        ...
