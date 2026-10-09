"""A ReactPy backend with no framework: routing, static files, and Layout."""

import asyncio
from pathlib import Path

import orjson
from asgi_tools import ResponseHTML
from servestatic import ServeStaticASGI

import reactpy
from reactpy import component, html, use_state
from reactpy.config import REACTPY_WEB_MODULES_DIR
from reactpy.core.hooks import ConnectionContext
from reactpy.core.layout import Layout
from reactpy.core.serve import serve_layout
from reactpy.types import Connection, Location

PATH_PREFIX = "/reactpy/"
STATIC_PATH = f"{PATH_PREFIX}static/"
MODULES_PATH = f"{PATH_PREFIX}modules/"

STATIC_DIR = Path(reactpy.__file__).parent / "static"


@component
def counter():
    count, set_count = use_state(0)
    return html.div(
        html.h1(f"Count: {count}"),
        html.button({"onClick": lambda event: set_count(count + 1)}, "Increment"),
    )


def index_html() -> str:
    mount = (
        "mountReactPy({mountElement: document.getElementById('app'),"
        "  pathPrefix:'" + PATH_PREFIX + "', componentPath:'counter/'});"
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>Custom backend</title>"
        "<script type='module'>"
        f"import {{ mountReactPy }} from '{STATIC_PATH}index.js';"
        + mount
        + "</script></head><body><div id='app'>Loading...</div></body></html>"
    )


class Backend:
    def __init__(self) -> None:
        self.components = {"counter": counter}
        self.static_app = ServeStaticASGI(
            self.not_found, root=STATIC_DIR, prefix=STATIC_PATH
        )
        self.modules_app = ServeStaticASGI(
            self.not_found, root=REACTPY_WEB_MODULES_DIR.current, prefix=MODULES_PATH
        )

    async def not_found(self, scope, receive, send) -> None:
        await ResponseHTML("Resource not found on this server.", status_code=404)(
            scope, receive, send
        )

    async def __call__(self, scope, receive, send) -> None:
        path = scope["path"]
        if scope["type"] == "http" and path.startswith(STATIC_PATH):
            return await self.static_app(scope, receive, send)
        if scope["type"] == "http" and path.startswith(MODULES_PATH):
            return await self.modules_app(scope, receive, send)
        if scope["type"] == "http" and path == "/":
            return await ResponseHTML(index_html())(scope, receive, send)
        if scope["type"] == "websocket" and path.startswith(PATH_PREFIX):
            return await self.serve_component(scope, receive, send)
        return await self.not_found(scope, receive, send)

    async def serve_component(self, scope, receive, send) -> None:
        name = scope["path"][len(PATH_PREFIX) :].strip("/")
        if name not in self.components:
            raise RuntimeError(f"Attempting to use an unregistered root {name}.")

        await send({"type": "websocket.accept"})
        queue: asyncio.Queue = asyncio.Queue(1000)

        async def pump() -> None:
            while True:
                event = await receive()
                if event["type"] == "websocket.disconnect":
                    return
                if event["type"] == "websocket.connect":
                    continue
                await queue.put(orjson.loads(event["text"]))

        async def recv():
            return await queue.get()

        async def send_model(message):
            await send(
                {"type": "websocket.send", "text": orjson.dumps(message).decode()}
            )

        task = asyncio.create_task(pump())
        connection = Connection(
            scope=scope,
            location=Location(path="/", query_string=""),
            carrier=None,
        )
        try:
            await serve_layout(
                Layout(ConnectionContext(self.components[name](), value=connection)),
                send_model,
                recv,
            )
        finally:
            task.cancel()


app = Backend()
