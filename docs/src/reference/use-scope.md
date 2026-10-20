## Overview

<p class="intro" markdown>

`use_scope` is a ReactPy hook that returns the ASGI connection scope behind the current websocket.

</p>

```python linenums="0"
scope = use_scope()
```

Use it for what the *server* knows about the connection: who the peer is, which headers arrived, which server accepted the request. For the page the visitor is looking at, use [`use_location`](./use-location.md) instead.

---

## Reference

### `use_scope()` { #use-scope }

Call it at the top level of a component. It takes no arguments.

```python linenums="0"
from reactpy import use_scope
```

#### Returns

The `#!python dict` at `#!python use_connection().scope` — the raw ASGI scope, with the same shape as any other ASGI app's `#!python scope`. It is a live dictionary: nothing copies it for you.

Read [ASGI: Websockets](https://asgi.readthedocs.io/en/latest/specs/www.html#connection-handling) for the specification; the keys below are what uvicorn's websocket implementation actually delivered, captured from a live Chrome session against `#!python ReactPy`:

| Key | What it holds |
| --- | --- |
| `#!python "type"` | `#!python "websocket"` for these connections. |
| `#!python "path"` | The **ReactPy websocket endpoint**, e.g. `#!python "/reactpy/"`. Not the page. |
| `#!python "headers"` | A list of `#!python (bytes, bytes)` pairs, lower-cased by the server. |
| `#!python "client"` | `#!python (ip, port)` of the peer, or `#!python None` if unknown. |
| `#!python "server"` | `#!python (host, port)` that accepted the connection. |
| `#!python "scheme"` | `#!python "ws"` or `#!python "wss"`. |
| `#!python "query_string"` | The websocket URL's query string, as `#!python bytes` — this carries ReactPy's own `#!python path`/`#!python qs` parameters. |
| `#!python "raw_path"` | The request path, as `#!python bytes`, un-decoded. |
| `#!python "root_path"` | The ASGI root path, normally `#!python ""`. |
| `#!python "http_version"` | e.g. `#!python "1.1"`. |
| `#!python "asgi"` | `#!python {"version": ..., "spec_version": ...}`. |
| `#!python "subprotocols"` | Requested websocket subprotocols, usually `#!python []`. |
| `#!python "state"` | A dict shared across the connection's tasks; empty unless something put values in it. |
| `#!python "extensions"` | Server-specific extras, e.g. `#!python {"websocket.http.response": {}}` under uvicorn. |

Which extras appear depends on the server: `#!python "state"` and that `#!python "extensions"` entry are uvicorn/`websockets` additions. Read them defensively, with `#!python scope.get(...)`.

#### Caveats

-   **`#!python "path"` is not the page.** For every component in the app it is the websocket endpoint — `#!python "/reactpy/"` under the default `path_prefix`. Verified: on the page `#!python /some/deep/page?tab=2&user=ada`, the scope still says `#!python "/reactpy/"`. Use `use_location().path` for the page.
-   **Headers are bytes.** Both halves of each pair are `#!python bytes` and lower-cased, so compare against `#!python b"user-agent"` and `#!python .decode()` the value before using it. There is no dict of headers; see the example.
-   **`#!python "query_string"` is the websocket's, not the page's.** It contains ReactPy's own `#!python path=` and `#!python qs=` parameters. Parse the page's query with `use_location()`.
-   **`#!python None` is possible.** `#!python "client"` can be absent or `#!python None` behind a proxy or in-process transport. `#!python scope["client"][0]` will raise on `None`; check first.
-   **It needs a live connection.** In a plain `Layout` render it raises `#!python RuntimeError: No backend established a connection.`
-   **It does not exist under client-side rendering.** With `#!python ReactPyCsr` there is no connection object, so the hook raises the same `RuntimeError`.
-   Like every hook, call it **only at the top level**.

---

## Usage

### Reading the peer and a header

=== "app.py"

    ```python
    {% include "../../examples/reference_use_scope/client_headers/app.py" start="# start" %}
    ```

`#!python header()` exists because the ASGI scope hands you raw bytes: it lower-cases the name, matches on `#!python bytes`, and decodes the value. The component reads `#!python scope["client"]` defensively because a proxy can leave it unset.

### What belongs here and what does not

| You want | Use |
| --- | --- |
| The visitor's IP address | `#!python use_scope()["client"]` |
| A request header | `#!python use_scope()["headers"]` |
| The page the visitor is on | [`use_location`](./use-location.md) |
| The query string | [`use_location`](./use-location.md) |
| The object mediating the connection | [`use_connection`](./use-connection.md) |

---

## Troubleshooting

### My header lookups always return `None`

You compared against a `#!python str`. The keys are `#!python bytes` and lower-cased: `#!python (b"user-agent", b"Mozilla/5.0 ...")`.

### It raises in my tests

A bare `Layout` render establishes no connection. Wrap the call in `#!python try`/`#!python except RuntimeError`, or inject a connection — see [`use_connection`](./use-connection.md).

### Every page shows `/reactpy/`

That is the scope's `#!python "path"`: the websocket endpoint, identical for all components. Use `use_location().path`.

### I need the request path before the websocket opens

`use_scope` only exists inside a component, which means inside an established websocket. For pre-connection decisions, handle it in ASGI middleware in front of the ReactPy app — see [ReactPyMiddleware](./reactpy-middleware.md).
