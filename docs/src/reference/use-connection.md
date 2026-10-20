## Overview

<p class="intro" markdown>

`use_connection` is a ReactPy hook that returns the `Connection` object describing the websocket your component is rendering into.

</p>

```python linenums="0"
connection = use_connection()
```

Each connected browser tab has its own. The object carries three things: the ASGI scope of the websocket, the location the browser reports, and the server's object mediating the connection.

---

## Reference

### `use_connection()` { #use-connection }

Call it at the top level of a component. It takes no arguments.

```python linenums="0"
from reactpy import use_connection
```

#### Returns

A `reactpy.types.Connection` dataclass with three fields:

-   **`scope`**: The ASGI scope of the websocket — the same dict [`use_scope`](./use-scope.md) returns.
-   **`location`**: A [`Location`](./use-location.md) describing the page the browser is on — the same object `use_location()` returns.
-   **`carrier`**: The object mediating the connection. What it is depends on the executor; under the ASGI executors it is a `#!python ReactPyWebsocket`. Capture `#!python type(connection.carrier).__name__` rather than assuming.

Import the type with `#!python from reactpy.types import Connection`; it is not exported from the `#!python reactpy` namespace.

#### Caveats

-   **This is a read-only view.** `Connection` has no `#!python deliver`, no `#!python send`, no `#!python close`, no `#!python id` — verified against the class. You cannot push a message to this client from here; communicate through state, effects, and event handlers. The `carrier` object under the ASGI executors is an internal `#!python ReactPyWebsocket`, not a supported API to call into.
-   **`scope` and `location` are live, mutable objects**, not copies. Writing into `#!python connection.scope` changes what every other read sees. Treat both as read-only.
-   **There is one per connection, not per render.** Each connected tab gets its own — verified: two concurrent clients saw distinct scopes and distinct locations — but within one tab the same object comes back on every render.
-   **It needs a live connection.** Two distinct failures:
    -   Called outside any component render → `#!python RuntimeError: No life cycle hook is active. Are you rendering in a layout?`
    -   Called inside a plain `Layout` render with no provider → `#!python RuntimeError: No backend established a connection.`

    Both messages are verbatim. In practice the second is the one you meet in tests; see [injecting a connection in tests](#injecting-a-connection-in-tests).
-   **It does not exist under client-side rendering.** `#!python ReactPyCsr` runs components without a `Connection` at all, so the hook raises there even though Python is in the browser. Verified in Chrome.
-   Like every hook, call it **only at the top level**.

---

## Usage

### Who is connected

Each field answers a different question, and mixing them up is the usual source of confusion.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_connection/inspect_client/app.py" start="# start" %}
    ```

`#!python scope['client']` is what the *server* saw when the websocket opened. `#!python location.path` is what the *browser* reported. They are independent sources, which is why the page path is not in the scope — see [`use_location`](./use-location.md) for why that matters.

### Injecting a connection in tests

Components that use any of the connection hooks fail in a bare `Layout` render. For a unit test, build the `Connection` yourself and wrap the component in the provider — `ConnectionContext` is meant to be set by the backend at the root of an app, and a test is a backend.

```python linenums="0"
import asyncio

from reactpy.core.hooks import ConnectionContext
from reactpy.core.layout import Layout
from reactpy.types import Connection, Location

from .app import page  # the component under test

connection = Connection(
    scope={"type": "websocket", "client": ("127.0.0.1", 5000)},
    location=Location(path="/reports", query_string="?tab=2"),
    carrier=None,
)


def test_page():
    async def render():
        async with Layout(ConnectionContext(page(), value=connection)) as layout:
            update = await layout.render()
        return str(update["model"])

    rendered = asyncio.run(render())
    assert "/reports" in rendered  # came from the injected Location
```

`carrier` can be anything — `#!python None` is fine, since nothing in a unit test dispatches over it. Note that `ConnectionContext` lives in `reactpy.core.hooks` rather than the public `reactpy` namespace: it is deliberately the backend's knob, and in a test your code is the backend.

!!! note "The hooks consume no hook slot"
    All three connection hooks ultimately call `use_context`, which reads the provider without reserving a hook slot. Unlike `use_state` or `use_effect`, they are safe to call conditionally or on only some renders; they will not shift other hooks' state. Verified: a component calling `use_connection()` only on even renders re-rendered cleanly across five renders.

---

## Troubleshooting

### `RuntimeError: No backend established a connection.`

No `ConnectionContext` was set. Under `#!python ReactPy` or `#!python ReactPyMiddleware` it is set for you once the websocket opens, so in production this means the component rendered somewhere the executor does not cover — most commonly a plain `Layout` render, a `#!python reactpy_to_string` call, or a `#!python ReactPyCsr` page. Either inject one as above, or make the component tolerate its absence:

```python linenums="0"
try:
    connection = use_connection()
except RuntimeError:
    return html.p("(not connected yet)")
```

### `RuntimeError: No life cycle hook is active. Are you rendering in a layout?`

You called the hook outside a render — at module level, in a plain function the component calls before rendering, or directly in your test body. Hooks only work while a component is rendering inside a `Layout`.

### `connection.carrier` is `None` in my test

Correct — you passed `#!python None`, and nothing reads it. Only the executor's own plumbing touches the carrier.

### I need to send something to this specific client

There is no supported way to reach a single connection from a component. State changes re-render that client's own components; anything beyond that is outside the scope of these hooks.
