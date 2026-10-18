## Overview

<p class="intro" markdown>

A ReactPy **backend** is the piece that owns the HTTP routes, serves the client bundle, accepts the websocket, and drives a `#!python Layout` against it. `#!python ReactPy` and `#!python ReactPyMiddleware` are two backends. This page is about writing the third: what the framework actually does for you, which parts you have to reproduce, and where the quiet traps are. It is also the fastest way to understand the request lifecycle, even if you never ship a custom backend.

</p>

!!! summary "You will learn"

    -   The four jobs a backend performs, in the order a browser makes them necessary
    -   The three ASGI routes ReactPy needs, and the exact shapes of the messages on each
    -   How to run a `#!python Layout` by hand with `serve_layout()`
    -   Why `Connection` is yours to construct, and what `carrier` means

## What a backend owes you

Strip away the executors and there are exactly four responsibilities. Everything else — hot reloading, config validation, HTML assembly — is convenience on top.

1.  **Serve the client bundle** over HTTP, so the page can `#!js import` it.
2.  **Serve web modules** over HTTP, so the client can `#!js import` any `#!python importSource` you emitted.
3.  **Return a document** containing a mount element and a `#!js mountReactPy(...)` call.
4.  **Accept a websocket** and run one `#!python Layout` against it, pumping messages in both directions.

The protocol is four message types. A rendered update goes down as `#!python {"type": "layout-update", "path": ..., "model": ...}`; an event comes up as `#!python {"type": "layout-event", "target": ..., "data": [...]}`; and when a handler reads a property of that event, the request goes down as `#!python {"type": "event-proxy-request", ...}` and the browser's answer comes up as `#!python {"type": "event-proxy-response", ...}`. [Protocol Structure](../reference/protocol-structure.md) documents them in full — this page is about plumbing, not the schema.

The good news about the last pair: `serve_layout` wires both directions for you. It binds your `send` as the proxy sender, and `Layout.deliver` recognises a response and routes it to the proxy backend instead of treating it as an event. A backend which pumps every received frame into `deliver` and every message out through `send` supports live event access without knowing it exists. A backend that filters frames before `deliver` — the way the ASGI middleware does, matching on `#!python "layout-event"` first — must route the responses itself or every `#!python await` on an event stalls until it times out.

## The job, in one file

This is a complete, working backend: no framework, no executor. It was run, and the counter incremented in a real browser.

=== "main.py"

    ```python
    {% include "../../examples/creating_backends/custom_backend/main.py" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Run it with anything that speaks ASGI:

```bash linenums="0"
uvicorn main:app --port 8000
```

Read it top to bottom and the four jobs map onto four spots: `#!python static_app` and `#!python modules_app` are jobs 1 and 2, `#!python index_html()` is job 3, and `#!python serve_component()` is job 4. The rest is `#!python __call__` dispatching on `#!python scope["type"]`.

## The routes

| Route | Serves | Supplied by |
| --- | --- | --- |
| `{path_prefix}static/` | `#!python index.js` and its chunks | `reactpy/static/` inside the wheel |
| `{path_prefix}modules/` | authored JavaScript modules | `config.REACTPY_WEB_MODULES_DIR` |
| `{path_prefix}<name>/` (websocket) | the layout for `#!python <name>` | your `#!python components` mapping |

The trailing slash on the websocket path is not decoration. The stock executors match `#!python ^{path_prefix}(?P<dotted_path>[a-zA-Z0-9_.]+)/$`, and the client builds that URL by *concatenating* `#!js pathPrefix` and `#!js componentPath`. A custom backend can match anything — but then `#!js componentPath` has to agree with it, and `#!js pathPrefix` must start **and** end with `#!python /`. See [The URL is built by concatenation](../reference/client-api.md#the-url-is-built-by-concatenation) for why a missing slash fails loudly in development and silently in production.

### Serving the bundle

Two directories, both plain static files:

```python linenums="0"
import reactpy
from pathlib import Path

from servestatic import ServeStaticASGI

from reactpy.config import REACTPY_WEB_MODULES_DIR

static_app = ServeStaticASGI(
    not_found, root=Path(reactpy.__file__).parent / "static", prefix="/reactpy/static/"
)
modules_app = ServeStaticASGI(
    not_found, root=REACTPY_WEB_MODULES_DIR.current, prefix="/reactpy/modules/"
)
```

`#!python servestatic` is what the executors use, and it is a normal ASGI app — swap in your own static handler if you have one. Two details matter more than the choice of library.

**Resolve `#!python REACTPY_WEB_MODULES_DIR.current` at request time or shortly after, never at import time.** It is an `#!python Option`, and the executors repoint it. Reading it too early hands you a directory that later ceases to be the live one.

**The `#!html <script type="module">` must be a module.** The bundle uses static `#!js import` for its two sibling chunks, so an ordinary `#!html <script>` fails before any of your code runs, usually with a bare `#!python SyntaxError: Cannot use import statement outside a module` in the console.

!!! warning "Serve the bundle from your own path at your peril"

    The client imports its chunks by a path derived from where `#!js index.js` was loaded. Serve it under a prefix that does not also serve `#!python static/`, and the chunk requests 404 while `#!js index.js` itself loaded fine — which reads as a partial success and is easy to misdiagnose. Keep `#!python static/` a child of your mount prefix, exactly as the executors do.

## Driving a layout

This is the part that is genuinely yours. Everything else is file serving.

The two primitives are `#!python Layout` (`core/layout.py`) and `#!python serve_layout` (`core/serve.py`). The latter is about twenty lines: it opens the layout, then runs one loop sending `#!python await layout.render()` out and one loop calling `#!python await layout.deliver(event)` on each received message — with the deliver *not* awaited to completion, so a slow handler never blocks the next event.

You supply `#!python send` and `#!python recv` coroutines:

```python linenums="0"
async def send_model(message):
    await send({"type": "websocket.send", "text": orjson.dumps(message).decode()})


async def recv():
    return await queue.get()
```

Four things go wrong here, and all four are worth knowing before you hit them.

### 1. The first `receive()` is `websocket.connect`

`#!python await send({"type": "websocket.accept"})` completes the handshake, but the `#!python websocket.connect` event is still sitting in the incoming stream. A pump loop that treats every event as a message will `#!python orjson.loads()` a dict with no `#!python text` key and die, typically with `#!python TypeError` or `#!python KeyError: 'text'`, right at connection time. Skip it:

```python linenums="0"
async def pump():
    while True:
        event = await receive()
        if event["type"] == "websocket.disconnect":
            return
        if event["type"] == "websocket.connect":
            continue
        await queue.put(orjson.loads(event["text"]))
```

This is the single most common way a hand-written backend fails, because everything *looks* right until the client connects: the page serves, the bundle loads, and the socket opens and closes immediately. The console shows `#!python [ReactPy] Disconnected!` followed by an endless reconnect loop.

### 2. `recv()` must not return `None`

If your `#!python recv` returns `#!python None` — which is what an unguarded `await receive()` does on disconnect — `serve_layout` calls `#!python layout.deliver(None)` and raises inside a task group, surfacing as an `#!python ExceptionGroup` that names neither your code nor the cause. Return a valid message or raise; never `#!python None`.

### 3. `ResponseWebSocket` has no `send_text`, and `receive()` needs `raw=True`

`#!python asgi_tools.ResponseWebSocket` is what the built-in executors use — `#!python ReactPyWebsocket` subclasses it — and it works fine as a backend's socket. Two API details differ from raw ASGI, and getting either wrong fails inside an anyio task group with an `#!python ExceptionGroup` that names neither your code nor the cause:

```python linenums="0"
async with ResponseWebSocket(scope=scope, receive=receive, send=send) as ws:

    async def pump():
        while True:
            event = await ws.receive(raw=True)  # the ASGI dict, not the payload
            if event["type"] == "websocket.disconnect":
                return
            if event["type"] != "websocket.receive":
                continue
            await queue.put(orjson.loads(event["text"]))

    async def send_model(message):
        await ws.send(orjson.dumps(message).decode())  # not send_text(...)
```

-   There is **no `#!python send_text`**. On `#!python asgi_tools.response.ResponseWebSocket` the methods are `#!python send(msg)` — which wraps a `#!python str` as `#!python {"type": "websocket.send", "text": ...}` and `#!python bytes` as `#!python "bytes": ...` — plus `#!python send_json(data)`. **Send text frames.** The stock `#!python send_json` emits `#!python {"type": "websocket.send", "bytes": json_dumps(data)}`, i.e. a *binary* frame, and that is precisely why the executors do not use it: `executors/asgi/middleware.py`, `ReactPyWebsocket.send_json` overrides it to `#!python self._send({"type": "websocket.send", "text": orjson.dumps(data).decode()})`. The client never sets `#!python socket.binaryType` (`static/index.js`), so a binary frame arrives as a `#!python Blob`, and `#!python JSON.parse(blob)` throws `#!python SyntaxError: ... "[object Blob]" is not valid JSON` — verified in headless Chrome. Reusing a stock `#!python asgi_tools` websocket object instead of overriding `#!python send_json` therefore produces a socket that connects, accepts, and then parses nothing.
-   `#!python receive()` returns the **payload** by default, not the ASGI event. Without `#!python raw=True` you get a `#!python str`, and `#!python event["type"]` then raises `#!python TypeError: string indices must be integers`. Pass `#!python raw=True`.
-   Under `#!python async with`, the handshake is already done — do not send `#!python websocket.accept` yourself. That is why the `#!python websocket.connect` skip above tests for `#!python != "websocket.receive"` rather than naming `#!python connect`.

Raw `#!python send`/`#!python receive` from the ASGI callable, as the main example does, is the interface guaranteed to be present on any host; that is the reason it is the default here.

### 4. One layout per connection, and never share one

A `#!python Layout` owns the hook state for a single client. Creating it before the request, or caching it by component name, means every browser tab shares one set of `#!python use_state` values — one user's click changes another's screen. Build the `#!python Layout` inside the connection handler, as above, and let it be garbage-collected with the socket.

The mirror-image bug is at the component level: a module-level element rendered by every layout is shared too, and mutation by one client leaks to all of them. That is covered in [VDOM Mutations](./vdom-mutations.md#case-2-the-mutation-escapes-to-other-users).

## `Connection` and `carrier`

Wrap the component in `#!python ConnectionContext` so the connection hooks work:

```python linenums="0"
from reactpy.core.hooks import ConnectionContext
from reactpy.types import Connection, Location

connection = Connection(
    scope=scope,
    location=Location(path="/", query_string=""),
    carrier=None,
)
layout = Layout(ConnectionContext(my_component(), value=connection))
```

Without that wrapper, `#!python use_connection()`, `#!python use_location()`, and `#!python use_scope()` all raise `#!python RuntimeError: No backend established a connection.` — even inside a perfectly healthy socket.

`#!python Connection` is a three-field dataclass, and as the backend author you decide what goes in it:

-   **`#!python scope`** — pass the websocket scope through verbatim. `#!python use_scope()` returns it, and users expect headers and query strings to be there.
-   **`#!python location`** — the stock ASGI executors do **not** use `scope["path"]`. The browser reports where it is, and the executor parses it out of the websocket query string: `#!python ?path=%2Fdocs%2F&qs=a%3D1` becomes `#!python Location(path="/docs/", query_string="a=1")`. If you hard-code `#!python path="/"`, every `#!python use_location()` on your app reports the root regardless of the URL in the address bar. Parse it the same way if your app routes on it.
-   **`#!python carrier`** — whatever mediates the connection. Nothing in ReactPy reads it; the executors put their websocket object there so *your* components can reach it. Put your own in, and document what it is, because [User Connection](../reference/use-connection.md) tells people to check its type rather than assume. `#!python None` is fine if nothing needs it.

!!! warning "`Connection` is a read-only view by design"

    There is no `#!python deliver`, no `#!python send`, no `#!python close` on it. Components talk to the client through state, effects, and event handlers — not by pushing messages. Your backend is the only code allowed to touch the socket, precisely because letting a component write to the wire bypasses the protocol and desynchronizes the client. If you find yourself wanting a push channel, read [Communicating Data Between Server and Client](./communicate-data-between-server-and-client.md) first.

## When to write one

Almost never, and it is worth naming the honest cases:

-   **Embedding ReactPy in an ASGI app you cannot wrap.** `#!python ReactPyMiddleware` already covers this — it takes your existing app as its first argument. Reach for a custom backend only when the middleware's routing gets in your way, since it owns `#!python {path_prefix}*` and nothing else.
-   **A non-ASGI host.** ReactPy's core is host-agnostic: `#!python Layout` and `#!python serve_layout` need only two coroutines, so a socket server on another loop is a routing problem, not a rewrite. This is the case the design genuinely supports.
-   **Owning the document.** If you generate HTML yourself and want ReactPy components inside it, you need the mount markup and the import map. You usually want `#!python server_side_component_html` for that rather than a new backend — see [Serving a component from your own route](../reference/reactpy-middleware.md#serving-a-component-from-your-own-route).
-   **Understanding it.** Writing the backend once is the clearest way to learn where the boundary between layout and transport is. It is a good exercise even when the result is deleted.

What it does **not** buy you: performance. `serve_layout` in your own code is the same loop. And you take on the pieces the executors handle quietly — config validation, the import-map injection, `#!python pyscript_setup`, static caching, reconnect options, and the error paths in the four sections above.

## Summary

-   A backend serves the bundle, serves web modules, returns a mount document, and runs one `#!python Layout` per websocket.
-   The message shapes are fixed: `#!python layout-update` and `#!python event-proxy-request` down, `#!python layout-event` and `#!python event-proxy-response` up.
-   Feed every received frame to `layout.deliver` and `serve_layout` routes event-proxy responses for you; filter frames yourself and you must route them yourself.
-   Skip the `#!python websocket.connect` event in your pump; it is the most common cause of an instantly-dying socket.
-   Speak raw ASGI on the socket; framework websocket wrappers do not have the methods `serve_layout` needs.
-   Build the `#!python Layout` per connection, and wrap the component in `#!python ConnectionContext` or the connection hooks raise.
-   You populate `#!python Connection`; the stock executors parse `location` from the query string, not the scope path.
-   Components get a read-only view of the connection by design — that is the protocol's integrity, not an omission.

## Related

-   [Protocol Structure](../reference/protocol-structure.md) — all four message types, `#!python target`, `#!python seq`, and the event proxy round trip
-   [Client API](../reference/client-api.md) — what `#!js mountReactPy` expects from your URL layout
-   [ReactPy](../reference/reactpy.md) and [ReactPyMiddleware](../reference/reactpy-middleware.md) — the two built-in backends
-   [User Connection](../reference/use-connection.md), [User Scope](../reference/use-scope.md), [User Location](../reference/use-location.md) — what your `Connection` feeds
-   [Communicating Data Between Server and Client](./communicate-data-between-server-and-client.md) — the supported alternatives to pushing
