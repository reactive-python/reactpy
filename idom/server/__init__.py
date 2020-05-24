from importlib import import_module
from socket import socket
from typing import Any, Dict, Optional, Tuple, Type, TypeVar, cast

from idom.widgets.utils import multiview, hotswap, MultiViewMount, MountFunc

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


def find_available_port(host: str) -> int:
    """Get a port that's available for the given host"""
    sock = socket()
    sock.bind((host, 0))
    return cast(int, sock.getsockname()[1])


def multiview_server(
    server: Type[_S],
    host: str,
    port: int,
    server_options: Optional[Any] = None,
    run_options: Optional[Dict[str, Any]] = None,
    app: Optional[Any] = None,
) -> Tuple[MultiViewMount, _S]:
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
        app: Optionally provide a prexisting application to register to

    Returns:
        The server instance and a function for adding views.
        See :func:`idom.widgets.common.multiview` for details.
    """
    mount, element = multiview()
    server_instance = server(element)
    server_instance.configure(server_options)
    if app is not None:
        server_instance.register(app)
    server_instance.daemon(host, port, **(run_options or {}))
    return mount, server_instance


def hotswap_server(
    server: Type[_S],
    host: str,
    port: int,
    server_options: Optional[Any] = None,
    run_options: Optional[Dict[str, Any]] = None,
    sync_views: bool = True,
    app: Optional[Any] = None,
) -> Tuple[MountFunc, _S]:
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
        sync_views: Whether to update all displays with newly mounted elements
        app: Optionally provide a prexisting application to register to

    Returns:
        The server instance and a function for swapping views.
        See :func:`idom.widgets.common.hotswap` for details.
    """
    mount, element = hotswap(shared=sync_views)
    server_instance = server(element)
    server_instance.configure(server_options)
    if app is not None:
        server_instance.register(app)
    server_instance.daemon(host, port, **(run_options or {}))
    return mount, server_instance
