import asyncio
import json
import logging
from asyncio import Queue as AsyncQueue
from queue import Queue as ThreadQueue
from threading import Event as ThreadEvent
from threading import Thread
from typing import Any, Callable, Dict, NamedTuple, Optional, Tuple, Type, Union, cast
from urllib.parse import parse_qs as parse_query_string

from flask import Blueprint, Flask, redirect, request, send_from_directory, url_for
from flask_cors import CORS
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.websocket import WebSocket
from typing_extensions import TypedDict

import idom
from idom.config import IDOM_CLIENT_BUILD_DIR
from idom.core.dispatcher import AbstractDispatcher, SingleViewDispatcher
from idom.core.layout import Layout, LayoutEvent, LayoutUpdate

from .base import AbstractRenderServer


logger = logging.getLogger(__name__)


class Config(TypedDict, total=False):
    """Render server config for :class:`FlaskRenderServer`"""

    import_name: str
    url_prefix: str
    cors: Union[bool, Dict[str, Any]]
    serve_static_files: bool
    redirect_root_to_index: bool


class FlaskRenderServer(AbstractRenderServer[Flask, Config]):
    """Base class for render servers which use Flask"""

    _dispatcher_type: Type[AbstractDispatcher]
    _wsgi_server: pywsgi.WSGIServer

    def stop(self, timeout: Optional[float] = None) -> None:
        try:
            server = self._wsgi_server
        except AttributeError:  # pragma: no cover
            raise RuntimeError(
                f"Application is not running or was not started by {self}"
            )
        else:
            server.stop(timeout)

    def _create_config(self, config: Optional[Config]) -> Config:
        new_config: Config = {
            "import_name": __name__,
            "url_prefix": "",
            "cors": False,
            "serve_static_files": True,
            "redirect_root_to_index": True,
            **(config or {}),  # type: ignore
        }
        return new_config

    def _default_application(self, config: Config) -> Flask:
        return Flask(config["import_name"])

    def _setup_application(self, config: Config, app: Flask) -> None:
        bp = Blueprint("idom", __name__, url_prefix=config["url_prefix"])

        self._setup_blueprint_routes(config, bp)

        cors_config = config["cors"]
        if cors_config:  # pragma: no cover
            cors_params = cors_config if isinstance(cors_config, dict) else {}
            CORS(bp, **cors_params)

        app.register_blueprint(bp)

        sockets = Sockets(app)

        @sockets.route(_join_url_paths(config["url_prefix"], "/stream"))  # type: ignore
        def model_stream(ws: WebSocket) -> None:
            def send(value: Any) -> None:
                ws.send(json.dumps(value))

            def recv() -> Optional[LayoutEvent]:
                event = ws.receive()
                if event is not None:
                    return LayoutEvent(**json.loads(event))
                else:
                    return None

            query_params = {
                k: v if len(v) > 1 else v[0]
                for k, v in parse_query_string(ws.environ["QUERY_STRING"]).items()
            }

            run_dispatcher_in_thread(
                lambda: self._dispatcher_type(
                    Layout(self._root_component_constructor(**query_params))
                ),
                send,
                recv,
                None,
            )

    def _setup_blueprint_routes(self, config: Config, blueprint: Blueprint) -> None:
        if config["serve_static_files"]:

            @blueprint.route("/client/<path:path>")
            def send_build_dir(path: str) -> Any:
                return send_from_directory(str(IDOM_CLIENT_BUILD_DIR.get()), path)

            if config["redirect_root_to_index"]:

                @blueprint.route("/")
                def redirect_to_index() -> Any:
                    return redirect(
                        url_for(
                            "idom.send_build_dir",
                            path="index.html",
                            **request.args,
                        )
                    )

    def _setup_application_did_start_event(
        self, config: Config, app: Flask, event: ThreadEvent
    ) -> None:
        @app.before_first_request
        def server_did_start() -> None:
            event.set()

    def _run_application(
        self,
        config: Config,
        app: Flask,
        host: str,
        port: int,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self._generic_run_application(app, host, port, *args, **kwargs)

    def _run_application_in_thread(
        self,
        config: Config,
        app: Flask,
        host: str,
        port: int,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> None:
        self._generic_run_application(app, host, port, *args, **kwargs)

    def _generic_run_application(
        self,
        app: Flask,
        host: str = "",
        port: int = 5000,
        debug: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if debug:
            logging.basicConfig(level=logging.DEBUG)  # pragma: no cover
        logger.info(f"Running at http://{host}:{port}")
        self._wsgi_server = _StartCallbackWSGIServer(
            self._server_did_start.set,
            (host, port),
            app,
            *args,
            handler_class=WebSocketHandler,
            **kwargs,
        )
        self._wsgi_server.serve_forever()


class PerClientStateServer(FlaskRenderServer):
    """Each client view will have its own state."""

    _dispatcher_type = SingleViewDispatcher


def run_dispatcher_in_thread(
    make_dispatcher: Callable[[], AbstractDispatcher],
    send: Callable[[Any], None],
    recv: Callable[[], Optional[LayoutEvent]],
    context: Optional[Any],
) -> None:
    dispatch_thread_info_created = ThreadEvent()
    dispatch_thread_info_ref: idom.Ref[Optional[_DispatcherThreadInfo]] = idom.Ref(None)

    def run_dispatcher() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        thread_send_queue: "ThreadQueue[LayoutUpdate]" = ThreadQueue()
        async_recv_queue: "AsyncQueue[LayoutEvent]" = AsyncQueue()

        async def send_coro(value: Any) -> None:
            thread_send_queue.put(value)

        async def recv_coro() -> Any:
            return await async_recv_queue.get()

        async def main() -> None:
            async with make_dispatcher() as dispatcher:
                await dispatcher.run(send_coro, recv_coro, context)

        main_future = asyncio.ensure_future(main())

        dispatch_thread_info_ref.current = _DispatcherThreadInfo(
            dispatch_loop=loop,
            dispatch_future=main_future,
            thread_send_queue=thread_send_queue,
            async_recv_queue=async_recv_queue,
        )
        dispatch_thread_info_created.set()

        loop.run_until_complete(main_future)

    Thread(target=run_dispatcher, daemon=True).start()

    dispatch_thread_info_created.wait()
    dispatch_thread_info = cast(_DispatcherThreadInfo, dispatch_thread_info_ref.current)
    assert dispatch_thread_info is not None

    stop = ThreadEvent()

    def run_send() -> None:
        while not stop.is_set():
            send(dispatch_thread_info.thread_send_queue.get())

    Thread(target=run_send, daemon=True).start()

    try:
        while True:
            value = recv()
            if value is None:
                stop.set()
                break
            # BUG: https://github.com/nedbat/coveragepy/issues/1012
            # Coverage isn't able to support concurrency coverage for both threading and gevent
            dispatch_thread_info.dispatch_loop.call_soon_threadsafe(  # pragma: no cover
                dispatch_thread_info.async_recv_queue.put_nowait, value
            )
    finally:
        dispatch_thread_info.dispatch_loop.call_soon_threadsafe(
            dispatch_thread_info.dispatch_future.cancel
        )

    return None


class _DispatcherThreadInfo(NamedTuple):
    dispatch_loop: asyncio.AbstractEventLoop
    dispatch_future: "asyncio.Future[Any]"
    thread_send_queue: "ThreadQueue[LayoutUpdate]"
    async_recv_queue: "AsyncQueue[LayoutEvent]"


class _StartCallbackWSGIServer(pywsgi.WSGIServer):  # type: ignore
    def __init__(
        self, before_first_request: Callable[[], None], *args: Any, **kwargs: Any
    ) -> None:
        self._before_first_request_callback = before_first_request
        super().__init__(*args, **kwargs)

    def update_environ(self) -> None:
        """
        Called before the first request is handled to fill in WSGI environment values.

        This includes getting the correct server name and port.
        """
        super().update_environ()
        # BUG: https://github.com/nedbat/coveragepy/issues/1012
        # Coverage isn't able to support concurrency coverage for both threading and gevent
        self._before_first_request_callback()  # pragma: no cover


def _join_url_paths(*args: str) -> str:
    # urllib.parse.urljoin performs more logic than is needed. Thus we need a util func
    # to join paths as if they were POSIX paths.
    return "/".join(map(lambda x: str(x).rstrip("/"), filter(None, args)))
