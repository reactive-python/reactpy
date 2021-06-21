"""
Server Prefabs
==============
"""

import logging
from typing import Any, Dict, Optional, Tuple, TypeVar

from idom.core.component import ComponentConstructor
from idom.widgets import MountFunc, MultiViewMount, hotswap, multiview

from .proto import Server, ServerFactory
from .utils import find_available_port, find_builtin_server_type


logger = logging.getLogger(__name__)

_App = TypeVar("_App")
_Config = TypeVar("_Config")


def run(
    component: ComponentConstructor,
    server_type: Optional[ServerFactory[_App, _Config]] = None,
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    server_config: Optional[Any] = None,
    run_kwargs: Optional[Dict[str, Any]] = None,
    app: Optional[Any] = None,
    daemon: bool = False,
) -> Server[_App]:
    """A utility for quickly running a render server with minimal boilerplate

    Parameters:
        component:
            The root of the view.
        server_type:
            What server to run. Defaults to a builtin implementation if available.
        host:
            The host string.
        port:
            The port number. Defaults to a dynamically discovered available port.
        server_config:
            Options passed to configure the server.
        run_kwargs:
            Keyword arguments passed to the :meth:`~idom.server.proto.Server.run`
            or :meth:`~idom.server.proto.Server.run_in_thread` methods of the server
            depending on whether ``daemon`` is set or not.
        app:
            Register the server to an existing application and run that.
        daemon:
            Whether the server should be run in a daemon thread.

    Returns:
        The server instance. This isn't really useful unless the server is spawned
        as a daemon. Otherwise this function blocks until the server has stopped.
    """
    if server_type is None:
        server_type = find_builtin_server_type("PerClientStateServer")
    if port is None:  # pragma: no cover
        port = find_available_port(host)

    server = server_type(component, server_config, app)
    logger.info(f"Using {type(server).__name__}")

    run_server = server.run if not daemon else server.run_in_thread
    run_server(host, port, **(run_kwargs or {}))  # type: ignore
    server.wait_until_started()

    return server


def multiview_server(
    server_type: Optional[ServerFactory[_App, _Config]] = None,
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    server_config: Optional[_Config] = None,
    run_kwargs: Optional[Dict[str, Any]] = None,
    app: Optional[Any] = None,
) -> Tuple[MultiViewMount, Server[_App]]:
    """Set up a server where views can be dynamically added.

    In other words this allows the user to work with IDOM in an imperative manner. Under
    the hood this uses the :func:`idom.widgets.multiview` function to add the views on
    the fly.

    Parameters:
        server: The server type to start up as a daemon
        host: The server hostname
        port: The server port number
        server_config: Value passed to :meth:`~idom.server.proto.ServerFactory`
        run_kwargs: Keyword args passed to :meth:`~idom.server.proto.Server.run_in_thread`
        app: Optionally provide a prexisting application to register to

    Returns:
        The server instance and a function for adding views. See
        :func:`idom.widgets.multiview` for details.
    """
    mount, component = multiview()

    server = run(
        component,
        server_type,
        host,
        port,
        server_config=server_config,
        run_kwargs=run_kwargs,
        daemon=True,
        app=app,
    )

    return mount, server


def hotswap_server(
    server_type: Optional[ServerFactory[_App, _Config]] = None,
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    server_config: Optional[_Config] = None,
    run_kwargs: Optional[Dict[str, Any]] = None,
    app: Optional[Any] = None,
    sync_views: bool = False,
) -> Tuple[MountFunc, Server[_App]]:
    """Set up a server where views can be dynamically swapped out.

    In other words this allows the user to work with IDOM in an imperative manner. Under
    the hood this uses the :func:`idom.widgets.hotswap` function to swap the views on
    the fly.

    Parameters:
        server: The server type to start up as a daemon
        host: The server hostname
        port: The server port number
        server_config: Value passed to :meth:`~idom.server.proto.ServerFactory`
        run_kwargs: Keyword args passed to :meth:`~idom.server.proto.Server.run_in_thread`
        app: Optionally provide a prexisting application to register to
        sync_views: Whether to update all displays with newly mounted components

    Returns:
        The server instance and a function for swapping views. See
        :func:`idom.widgets.hotswap` for details.
    """
    mount, component = hotswap(update_on_change=sync_views)

    server = run(
        component,
        server_type,
        host,
        port,
        server_config=server_config,
        run_kwargs=run_kwargs,
        daemon=True,
        app=app,
    )

    return mount, server
