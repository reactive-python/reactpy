## Overview

<p class="intro" markdown>

`ReactPyMiddleware` adds ReactPy routes to an ASGI application you already have. Requests ReactPy does not recognise fall through to your app.

</p>

```python linenums="0"
from reactpy.executors.asgi import ReactPyMiddleware

my_app = ReactPyMiddleware(existing_asgi_app, root_components=["main.component"])
```

---

## Reference

### `ReactPyMiddleware(app, root_components, **settings)`

```python linenums="0"
from reactpy.executors.asgi import ReactPyMiddleware
```

#### Parameters

-   **`app`**: The ASGI application to serve when a request does **not** match a ReactPy route. Any ASGI app works — Starlette, FastAPI, or hand-written.

-   **`root_components`**: A list, set, or tuple of **dotted paths** to root components, e.g. `#!python ["main.counter"]`. The path must be importable by Python's import system: module path, dot, attribute name. Resolution is `module.rsplit(".", 1)` followed by `#!python getattr`, so it must name a module that is importable from the server's working directory.

-   **`**settings`**: Any key from `#!python ReactPyConfig`. See [Configuration](./reactpy.md#configuration). `#!python path_prefix` is validated at construction and raises `#!python ValueError` if malformed.

#### Returns

An ASGI application.

---

## Usage

### Wrapping an existing app

=== "main.py"

    ```python
    {% include "../../examples/reference_reactpy_middleware/wrapper/main.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The wrapped app is untouched. Verified with Starlette: a plain `#!python /healthz` route still returned its text response through the middleware.

### What the middleware actually claims

`ReactPyMiddleware.__call__` handles exactly three kinds of request and forwards everything else:

| Path | Handled by |
| --- | --- |
| websocket matching `{path_prefix}{dotted_path}/` | ReactPy render stream |
| `{path_prefix}static/...` | ReactPy client bundle |
| `{path_prefix}modules/...` | built web modules |
| **anything else** | **your app** |

There is no fourth row. `ReactPyMiddleware.match_extra_paths` is a hook that returns `#!python None` — its own comment says custom routes are "unused by default to encourage users to handle routing within your ASGI framework of choice". The `#!python @my_app.route(...)` registry people expect belongs to the standalone `#!python ReactPy` executor, which overrides that method to match `#!python extra_http_routes` / `#!python extra_ws_routes`. Under the middleware, every route is your app's.

!!! warning "The middleware never serves your HTML"

    This is the part that surprises people. Registering a dotted path does **not** create a page. Requesting `#!python "/"` falls through to your app, and there is no `{path_prefix}{dotted_path}/` HTTP route either — that pattern is matched only when the ASGI scope type is `#!python "websocket"`. Verified: requesting `#!python /reactpy/main.counter/` over HTTP returns `404`, while the websocket on the same path streams the model.

    You produce the document yourself, by emitting an empty mount element and the client bootstrap that points at one registered component.

### Serving a component from your own route

=== "main.py"

    ```python
    {% include "../../examples/reference_reactpy_middleware/mount_snippet/main.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`#!python server_side_component_html` emits the `#!html <div id="app">`, the import map fallback, and the `#!python mountReactPy(...)` call. Verified in a real browser: the counter rendered into `#!html <div id="app">` with `#!python [ReactPy] Connected!` in the console.

!!! warning "The trailing slash in `component_path` is required"

    Pass `#!python "main.counter/"`, not `#!python "main.counter"`. The client opens `#!python ws://host/reactpy/<component_path>?path=/`, and the server matches the websocket path against

    ```text linenums="0"
    ^{path_prefix}(?P<dotted_path>[a-zA-Z0-9_.]+)/$
    ```

    which **requires** the trailing slash. Verified both ways: without it the handshake fails with `Unexpected response code` and the console logs `#!python [ReactPy] Failed to connect!`, leaving an empty div; with it, the component renders.

### Multiple components

Register several and choose per page. Each page mounts exactly one:

```python linenums="0"
my_app = ReactPyMiddleware(
    starlette_app,
    root_components=["main.counter", "main.settings", "main.profile"],
)
```

Then emit a different `#!python component_path` from each of your routes.

!!! info "Unregistered paths are rejected"

    `#!python "Attempting to use an unregistered root component <path>."` is raised when a websocket asks for a dotted path you never listed. Register every component you intend to mount.

### Import errors

A dotted path that cannot be imported fails at construction, with a message naming the part that failed:

```text linenums="0"
ImportError: ReactPy failed to import "main"
AttributeError: ReactPy failed to import "counter" from "main"
```

The first means the module was not found; the second means the module loaded but has no such attribute. `#!python ValueError` is raised earlier still if the path has no dot at all.

## Choosing an executor

| Goal | Use |
| --- | --- |
| Whole app is ReactPy, no existing server code | [`ReactPy`](./reactpy.md) |
| Add components to an existing ASGI app | `ReactPyMiddleware` |
| Run component code in the browser via PyScript | [`ReactPyCsr`](./reactpy-csr.md) |

`#!python ReactPy` is itself a subclass of `#!python ReactPyMiddleware` that registers a single root and serves its own index document, which is why the standalone executor can do the HTML the middleware leaves to you.

## Related

-   [Adding ReactPy to an Existing Project](../learn/add-react-to-an-existing-project.md)
-   [ReactPy](./reactpy.md) — the standalone executor.
