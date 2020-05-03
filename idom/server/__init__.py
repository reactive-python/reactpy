from importlib import import_module
from typing import Any, Callable, Dict, Optional, Tuple, Type, TypeVar

from idom.core.element import ElementConstructor
from idom.widgets.utils import multiview, hotswap

from .base import AbstractRenderServer


__all__ = []


for name in ["sanic"]:
    try:
        import_module(name)
    except ImportError:  # pragma: no cover
        pass
    else:
        import_module(__name__ + "." + name)
        __all__.append(name)


_S = TypeVar("_S", bound=AbstractRenderServer[Any, Any])


def multiview_server(
    server: Type[_S],
    host: str,
    port: int,
    server_options: Optional[Any] = None,
    run_options: Optional[Dict[str, Any]] = None,
) -> Tuple[Callable[[ElementConstructor], int], _S]:
    """Set up a server where views can be dynamically added.

    In other words this allows the user to work with IDOM in an imperative manner.
    Under the hood this uses the :func:`idom.widgets.common.multiview` function to
    add the views on the fly.

    Parameters:
        server: The server type to start up as a daemon
        host: The server hostname
        port: The server port number
        server_options: Value passed to :meth:`AbstractRenderServer.configure`
        run_options: Keyword args passed to :meth:`AbstractRenderServer.daemon`

    Returns:
        The server instance and a function for adding views.
        See :func:`idom.widgets.common.multiview` for details.
    """
    mount, element = multiview()
    server_instance = server(element)
    server_instance.configure(server_options)
    server_instance.daemon(host, port, **(run_options or {}))
    return mount, server_instance


def hotswap_server(
    server: Type[_S],
    host: str,
    port: int,
    server_options: Optional[Any] = None,
    run_options: Optional[Dict[str, Any]] = None,
) -> Tuple[Callable[[ElementConstructor], None], _S]:
    """Set up a server where views can be dynamically swapped out.

    In other words this allows the user to work with IDOM in an imperative manner.
    Under the hood this uses the :func:`idom.widgets.common.hotswap` function to
    swap the views on the fly.

    Parameters:
        server: The server type to start up as a daemon
        host: The server hostname
        port: The server port number
        server_options: Value passed to :meth:`AbstractRenderServer.configure`
        run_options: Keyword args passed to :meth:`AbstractRenderServer.daemon`

    Returns:
        The server instance and a function for swapping views.
        See :func:`idom.widgets.common.hotswap` for details.
    """
    mount, element = hotswap(shared=True)
    server_instance = server(element)
    server_instance.configure(server_options)
    server_instance.daemon(host, port, **(run_options or {}))
    return mount, server_instance
