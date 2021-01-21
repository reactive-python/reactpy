import json
import asyncio
import logging
from urllib.parse import urljoin
from asyncio import Queue as AsyncQueue
from threading import Event as ThreadEvent, Thread
from queue import Queue as ThreadQueue
from typing import Union, Tuple, Dict, Any, Optional, Callable, NamedTuple

from typing_extensions import TypedDict
from flask import Flask, Blueprint, send_from_directory, redirect, url_for
from flask_cors import CORS
from flask_sockets import Sockets
from geventwebsocket.websocket import WebSocket
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

import idom
from idom.client.manage import BUILD_DIR
from idom.core.layout import LayoutEvent, Layout
from idom.core.dispatcher import AbstractDispatcher, SingleViewDispatcher

from .base import AbstractRenderServer


class Config(TypedDict, total=False):
    """Render server config for :class:`FlaskRenderServer`"""

    import_name: str
    url_prefix: str
    cors: Union[bool, Dict[str, Any]]
    serve_static_files: bool
    redirect_root_to_index: bool


class FlaskRenderServer(AbstractRenderServer[Flask, Config]):
    """Base class for render servers which use Flask"""

    _dispatcher_type: AbstractDispatcher
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
        return Config(
            {
                "import_name": __name__,
                "url_prefix": "",
                "cors": False,
                "serve_static_files": True,
                "redirect_root_to_index": True,
                **(config or {}),
            }
        )

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

        @sockets.route(urljoin(config["url_prefix"], "/stream"))
        def model_stream(ws: WebSocket) -> None:
            def send(value: Any) -> None:
                ws.send(json.dumps(value))

            def recv() -> LayoutEvent:
                event = ws.receive()
                if event is not None:
                    return LayoutEvent(**json.loads(event))
                else:
                    return None

            run_dispatcher_in_thread(
                lambda: self._dispatcher_type(
                    Layout(self._root_component_constructor())
                ),
                send,
                recv,
                None,
            )

    def _setup_blueprint_routes(self, config: Config, blueprint: Blueprint) -> None:
        if config["serve_static_files"]:

            @blueprint.route("/client/<path:path>")
            def send_build_dir(path):
                return send_from_directory(str(BUILD_DIR), path)

            if config["redirect_root_to_index"]:

                @blueprint.route("/")
                def redirect_to_index():
                    return redirect(url_for("idom.send_build_dir", path="index.html"))

    def _setup_application_did_start_event(
        self, config: Config, app: Flask, event: ThreadEvent
    ) -> None:
        @app.before_first_request
        def server_did_start():
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
        **kwargs,
    ):
        if debug:
            logging.basicConfig(level=logging.DEBUG)  # pragma: no cover
        logging.debug("Starting server...")
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

    def run_dispatcher():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        thread_send_queue = ThreadQueue()
        async_recv_queue = AsyncQueue()

        async def send_coro(value: Any) -> None:
            thread_send_queue.put(value)

        async def recv_coro() -> Any:
            return await async_recv_queue.get()

        async def main():
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
    dispatch_thread_info = dispatch_thread_info_ref.current
    assert dispatch_thread_info is not None

    stop = ThreadEvent()

    def run_send():
        while not stop.is_set():
            send(dispatch_thread_info.thread_send_queue.get())

    Thread(target=run_send, daemon=True).start()

    try:
        while True:
            value = recv()
            if value is None:
                stop.set()
                break
            dispatch_thread_info.dispatch_loop.call_soon_threadsafe(
                dispatch_thread_info.async_recv_queue.put_nowait, value
            )
    finally:
        dispatch_thread_info.dispatch_loop.call_soon_threadsafe(
            dispatch_thread_info.dispatch_future.cancel
        )

    return None


class _DispatcherThreadInfo(NamedTuple):
    dispatch_loop: asyncio.AbstractEventLoop
    dispatch_future: asyncio.Future
    thread_send_queue: ThreadQueue
    async_recv_queue: AsyncQueue


class _StartCallbackWSGIServer(pywsgi.WSGIServer):
    def __init__(self, before_first_request: Callable[[], None], *args, **kwargs):
        self._before_first_request_callback = before_first_request
        super().__init__(*args, **kwargs)

    def update_environ(self):
        """
        Called before the first request is handled to fill in WSGI environment values.

        This includes getting the correct server name and port.
        """
        super().update_environ()
        # BUG: for some reason coverage doesn't seem to think this line is covered
        self._before_first_request_callback()  # pragma: no cover
