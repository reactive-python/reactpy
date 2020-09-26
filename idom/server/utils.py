from socket import socket
from importlib import import_module
from typing import Any, Dict, Optional, Tuple, Type, TypeVar, cast

from idom.core.element import ElementConstructor
from idom.widgets.utils import multiview, hotswap, MultiViewMount, MountFunc

from .base import AbstractRenderServer


_S = TypeVar("_S", bound=AbstractRenderServer[Any, Any])


def _find_default_server_type() -> Optional[Type[_S]]:
    for name in ["sanic.PerClientStateServer"]:
        module_name, server_name = name.split(".")
        try:
            module = import_module(f"idom.server.{module_name}")
        except ImportError:  # pragma: no cover
            pass
        else:
            return cast(Type[_S], getattr(module, server_name))
    else:  # pragma: no cover
        return None


def run(
    element: ElementConstructor,
    server_type: Optional[Type[_S]] = _find_default_server_type(),
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    server_options: Optional[Any] = None,
    run_options: Optional[Dict[str, Any]] = None,
    daemon: bool = False,
    app: Optional[Any] = None,
) -> _S:
    """A utility for quickly running a render server with minimal boilerplate

    Parameters:
        element: The root of the view.
        server_type: What server to run. Defaults to a builtin implementation if available.
        host: The host string.
        port: The port number. Defaults to a dynamically discovered available port.
        server_options: Options passed to configure the server.
        run_options: Options passed to the server to run it.
        daemon: Whether the server should be run in a daemon thread.
        app: Register the server to an existing application and run that.

    Returns:
        The server instance. This isn't really useful unless the server is spawned
        as a daemon. Otherwise this function blocks until the server has stopped.
    """
    if server_type is None:  # pragma: no cover
        raise ValueError("No default server available.")
    if port is None:  # pragma: no cover
        port = find_available_port(host)

    server = server_type(element, server_options)

    if app is not None:
        server.register(app)

    run_server = server.run if not daemon else server.daemon
    run_server(host, port, **(run_options or {}))

    return server


def multiview_server(
    server_type: Type[_S],
    host: str = "127.0.0.1",
    port: Optional[int] = None,
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

    server = run(
        element,
        server_type,
        host,
        port,
        server_options=server_options,
        run_options=run_options,
        daemon=True,
        app=app,
    )

    return mount, server


def hotswap_server(
    server_type: Type[_S],
    host: str = "127.0.0.1",
    port: Optional[int] = None,
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

    server = run(
        element,
        server_type,
        host,
        port,
        server_options=server_options,
        run_options=run_options,
        daemon=True,
        app=app,
    )

    return mount, server


def find_available_port(host: str) -> int:
    """Get a port that's available for the given host"""
    sock = socket()
    sock.bind((host, 0))
    return cast(int, sock.getsockname()[1])
