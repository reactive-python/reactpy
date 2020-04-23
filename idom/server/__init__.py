from importlib import import_module
from typing import Any, Callable, Dict, Optional, Tuple, Type, TypeVar

from idom.core.element import ElementConstructor
from idom.widgets.common import hotswap

from .base import AbstractRenderServer


__all__ = []


for name in ["sanic"]:
    try:
        import_module(name)
    except ImportError:
        pass
    else:
        import_module(__name__ + "." + name)
        __all__.append(name)


_S = TypeVar("_S", bound=AbstractRenderServer[Any, Any])


def imperative_server_mount(
    server: Type[_S],
    host: str,
    port: int,
    run_options: Optional[Dict[str, Any]] = None,
    server_options: Optional[Dict[str, Any]] = None,
) -> Tuple[_S, Callable[[ElementConstructor], None]]:
    mount, element = hotswap()
    server_instance = server(element).configure(server_options or {})
    server_instance.daemon(host, port, **(run_options or {}))
    return server_instance, mount
