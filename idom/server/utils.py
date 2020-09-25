from socket import socket
from importlib import import_module
from typing import Any, Dict, Optional, Tuple, Type, TypeVar, cast

from idom.core.element import ElementConstructor
from idom.widgets.utils import multiview, hotswap, MultiViewMount, MountFunc

from .base import AbstractRenderServer


_S = TypeVar("_S", bound=AbstractRenderServer[Any, Any])


def _find_default_server_type() -> Optional[Type[AbstractRenderServer[Any, Any]]]:
    for name in ["sanic.PerClientStateServer"]:
        module_name, server_name = name.split(".")
        try:
            module = import_module(f"idom.server.{module_name}")
        except ImportError:  # pragma: no cover
            pass
        else:
            return getattr(module, server_name)
    else:
        return None


def run(
    element: ElementConstructor,
    server: Optional[
        Type[AbstractRenderServer[Any, Any]]
    ] = _find_default_server_type(),
    host: Optional[str] = "127.0.0.1",
    port: Optional[int] = None,
    run_options: Optional[Dict[str, Any]] = None,
) -> None:
    """A utility for quickly running a view with minimal boilerplat"""
    if server is None:
        raise ValueError("No default server available.")
    if port is None:
        port = find_available_port(host)
    server(element).run(host, port, **(run_options or {}))


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
