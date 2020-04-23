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
    shared: bool = False,
    server_options: Optional[Any] = None,
    run_options: Optional[Dict[str, Any]] = None,
) -> Tuple[_S, Callable[[ElementConstructor], None]]:
    """Set up a server whose view can be swapped out on the fly.

    In other words this allows the user to work with IDOM in an imperative manner.
    Under the hood this uses the :func:`idom.widgets.common.hotswap` function to
    switch out views on the fly.

    Parameters:
        server: The server type to start up as a daemon
        host: The server hostname
        port: The server port number
        shared: Whether or not all views from the server should be updated when swapping
        server_options: Value passed to :meth:`AbstractRenderServer.configure`
        run_options: Keyword args passed to :meth:`AbstractRenderServer.daemon`

    Returns:
        The server instance and a function for swapping out the view.
    """
    mount, element = hotswap(shared)
    server_instance = server(element)
    if server_options:
        server_instance.configure(server_options)
    server_instance.daemon(host, port, **(run_options or {}))
    return server_instance, mount
