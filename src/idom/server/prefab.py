import logging
from typing import Any, Dict, Optional, Tuple, Type, TypeVar

from idom.core.component import ComponentConstructor
from idom.widgets.utils import MountFunc, MultiViewMount, hotswap, multiview

from .base import AbstractRenderServer
from .utils import find_available_port, find_builtin_server_type


logger = logging.getLogger(__name__)
_S = TypeVar("_S", bound=AbstractRenderServer[Any, Any])


def run(
    component: ComponentConstructor,
    server_type: Type[_S] = find_builtin_server_type("PerClientStateServer"),
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    server_config: Optional[Any] = None,
    run_kwargs: Optional[Dict[str, Any]] = None,
    app: Optional[Any] = None,
    daemon: bool = False,
) -> _S:
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
            Keyword arguments passed to the :meth:`~AbstractRenderServer.daemon`
            or :meth:`~AbstractRenderServer.run` method of the server
        app:
            Register the server to an existing application and run that.
        daemon:
            Whether the server should be run in a daemon thread.

    Returns:
        The server instance. This isn't really useful unless the server is spawned
        as a daemon. Otherwise this function blocks until the server has stopped.
    """
    if server_type is None:  # pragma: no cover
        raise ValueError("No default server available.")
    if port is None:  # pragma: no cover
        port = find_available_port(host)

    logger.info(f"Using {server_type.__module__}.{server_type.__name__}")

    server = server_type(component, server_config)

    if app is not None:  # pragma: no cover
        server.register(app)

    run_server = server.run if not daemon else server.daemon
    run_server(host, port, **(run_kwargs or {}))  # type: ignore

    return server


def multiview_server(
    server_type: Type[_S],
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    server_config: Optional[Any] = None,
    run_kwargs: Optional[Dict[str, Any]] = None,
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
        server_config: Value passed to :meth:`AbstractRenderServer.configure`
        run_kwargs: Keyword args passed to :meth:`AbstractRenderServer.daemon`
        app: Optionally provide a prexisting application to register to

    Returns:
        The server instance and a function for adding views.
        See :func:`idom.widgets.common.multiview` for details.
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
    server_type: Type[_S],
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    server_config: Optional[Any] = None,
    run_kwargs: Optional[Dict[str, Any]] = None,
    app: Optional[Any] = None,
    sync_views: bool = False,
) -> Tuple[MountFunc, _S]:
    """Set up a server where views can be dynamically swapped out.

    In other words this allows the user to work with IDOM in an imperative manner.
    Under the hood this uses the :func:`idom.widgets.common.hotswap` function to
    swap the views on the fly.

    Parameters:
        server: The server type to start up as a daemon
        host: The server hostname
        port: The server port number
        server_config: Value passed to :meth:`AbstractRenderServer.configure`
        run_kwargs: Keyword args passed to :meth:`AbstractRenderServer.daemon`
        app: Optionally provide a prexisting application to register to
        sync_views: Whether to update all displays with newly mounted components

    Returns:
        The server instance and a function for swapping views.
        See :func:`idom.widgets.common.hotswap` for details.
    """
    mount, component = hotswap(shared=sync_views)

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
