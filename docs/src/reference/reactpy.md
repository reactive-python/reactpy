## Overview

<p class="intro" markdown>

`ReactPy` is ReactPy's standalone ASGI application. It serves the HTML document, the client bundle, and the websocket through which components render.

</p>

```python linenums="0"
from reactpy.executors.asgi import ReactPy

my_app = ReactPy(root_component)
```

---

## Reference

### `ReactPy(root_component, **settings)`

Instantiate `ReactPy` once, at module level, and hand the instance to any ASGI server:

```bash linenums="0"
uvicorn main:my_app
```

ReactPy serves the page at every route that is not claimed by its own static or websocket paths.

```python linenums="0"
from reactpy.executors.asgi import ReactPy
```

#### Parameters

-   **`root_component`**: The component to mount. A component *constructor* — the `#!python @component` function itself, not a call to it. This app is a single-page application: there is exactly one root.

-   **`html_head`** *(optional)*: Extra content for the document's `#!html <head>`.

    !!! warning "Must be built with `html.head`"

        Pass `#!python html.head(...)` — not a bare `#!python html.title(...)` or a `#!python html.div(...)`. Anything else raises at request time:

        ```text linenums="0"
        ValueError: Head element must be constructed with `html.head`.
        ```

        Verified: this surfaces as a `500` on the index route, not at import time, so a typo here only shows up once the server is running.

-   **`prepend_body`** *(optional)*: Content rendered at the start of the `#!html <body>`, **before** the mount point. Accepts a `#!python VdomDict` built with `#!python html.*`, or `#!python None` to omit. Defaults to `#!python html.noscript("Enable JavaScript to view this site.")`.

    This is the one part of the tree that is genuinely server-rendered. See [what `ReactPy` does and does not render](#what-reactpy-does-and-does-not-render).

-   **`html_lang`** *(optional)*: Value for the document's `#!python lang` attribute. Defaults to `#!python "en"`.

-   **`http_headers`** *(optional)*: Extra response headers for the index document — a plain `#!python dict[str, str]`. Use it for CSP, `X-Frame-Options`, caching, and similar.

-   **`pyscript_setup`** *(optional)*: Load [PyScript](https://pyscript.net/) into the document head, for running component code in the browser. Defaults to `#!python False`. `#!python ReactPyCsr` sets this for you.

-   **`pyscript_options`** *(optional)*: A `#!python PyScriptOptions` configuring that behaviour.

-   **`**settings`**: Any key from `#!python ReactPyConfig`. Despite appearances these are **not** scoped to this app instance — each one is written to the matching global in `#!python reactpy.config`, so the last executor constructed wins process-wide. See [Configuration](#configuration).

#### Returns

An ASGI application.

---

## Usage

### A standalone app

=== "app.py"

    ```python
    {% include "../../examples/reference_reactpy/standalone/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Serve it with `#!python uvicorn main:my_app`. The name you assign matters, because it is what `#!python uvicorn module:name` refers to.

### Page metadata and headers

=== "app.py"

    ```python
    {% include "../../examples/reference_reactpy/head_and_lang/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified against a running server: `#!python lang="fr"`, the custom `#!html <title>`, the custom response header, and the `#!python prepend_body` markup all appear in the initial HTML.

### Configuration

Settings are ordinary keyword arguments, and they reach the browser-side client:

=== "app.py"

    ```python
    {% include "../../examples/reference_reactpy/config/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

| Setting | Default | Meaning |
| --- | --- | --- |
| `path_prefix` | `/reactpy/` | Base path ReactPy serves its own static assets and websocket from. |
| `web_modules_dir` | temp dir | Where built web modules are cached. |
| `reconnect_interval` | `750` | Milliseconds before the first reconnect attempt. |
| `reconnect_max_interval` | `60000` | Ceiling on the reconnect backoff. |
| `reconnect_max_retries` | `150` | Attempts before giving up. |
| `reconnect_backoff_multiplier` | `1.25` | Growth factor between attempts. |
| `async_rendering` | `True` | Allow renders to overlap. |
| `debug` | `False` | Server-side checks and richer error text — see the note below. |
| `max_queue_size` | `1000` | Bound on the pending events of each handler target — the layout keeps a queue per target (`core/layout.py`, `_event_queues`), not one per connection. |
| `event_proxy_timeout` | `5.0` | Seconds to wait for the browser to answer one live event read before `EventProxyTimeout`. |
| `event_proxy_max_depth` | `10` | How deep one resolution may expand nested objects before they come back as references. |
| `event_proxy_max_timeouts` | `3` | Consecutive unanswered round trips tolerated before live access is switched off for the connection. |
| `tests_default_timeout` | `15.0` | Default timeout for `reactpy.testing`. **Not settable this way** — see the note below. |

Verified: setting `#!python path_prefix="/apps/reactpy/"` moves asset serving to that prefix, and the reconnect values appear in the generated mount call. The three `#!python event_proxy_*` settings were verified by constructing an executor with them and reading the matching `#!python reactpy.config` options back.

They belong to a handler which reads the browser rather than to the client bootstrap: they bound the round trips behind `#!python await event.target.value`. Reach for them only when a handler is timing out or a deeply nested read comes back as references — see [Protocol Structure](protocol-structure.md#the-event-proxy-round-trip).

!!! warning "These keywords are process-wide, not per-app"

    `executors/utils.py`, `process_settings` walks the keywords and calls `set_current()` on the matching `#!python reactpy.config` `Option` object. Those objects are module-level globals, so the *last constructor to run wins for the whole process* — including for any app built before it. Verified: two `#!python ReactPy` instances created with `#!python reconnect_interval=111` and `#!python reconnect_interval=999` leave `#!python REACTPY_RECONNECT_INTERVAL.current` at `#!python 999` for both. There is no per-app configuration layer; do not host two apps that need different values.

    `#!python tests_default_timeout` is worse than ineffective. Its `Option` is declared `#!python mutable=False` in `reactpy/config.py`, and `#!python _option.py`, `set_current` raises `TypeError` on an immutable option — so passing it raises `Option(REACTPY_TESTS_DEFAULT_TIMEOUT=15.0) cannot be modified after initial load` out of the constructor. Set it via the `#!bash REACTPY_TESTS_DEFAULT_TIMEOUT` environment variable before import, or not at all.

    `#!python debug` is not a client switch. `#!python REACTPY_DEBUG` turns on server-side VDOM and JSON-attribute validation, populates the model's `#!python error` text (without it, a failed component ships `#!python "error": ""` and renders as nothing), and changes a few asset URLs to their `#!js ?dev` forms. See [Common Props](common-props.md#invalid-dictionaries).

Each setting also has an environment-variable twin in `#!python reactpy.config` — `#!python REACTPY_PATH_PREFIX`, `#!python REACTPY_RECONNECT_INTERVAL`, and so on. Since the keyword already writes to that same global option, the two differ only in timing: the environment variable is read when the module is first imported, the keyword whenever an executor is constructed.

---

## What `ReactPy` does and does not render

This is the distinction that trips people up, because the executor has historically been described as "SSR".

The initial HTML document contains an **empty** mount point:

```html linenums="0"
<body>
  <noscript>Enable JavaScript to view this site.</noscript>
  <div id="app" class=""></div>
  <script type="module" crossorigin="anonymous">
    import { mountReactPy } from "/reactpy/static/index.js";
    mountReactPy({ mountElement: document.getElementById("app"), ... });
  </script>
</body>
```

Verified by fetching the index route: your root component's markup is **not** in the response. The browser connects over the websocket and ReactPy renders and streams from there.

What *is* server-rendered into the first response:

-   `#!python prepend_body`, converted with `#!python reactpy_to_string`.
-   `#!python html_head`.
-   The document shell: `#!python lang`, static asset paths, the mount script.

Practical consequences:

-   **Search engines and `curl` see an empty app.** For content that must exist without JavaScript, render it yourself — `#!python reactpy_to_string` turns a component into an HTML string, which you can place in `#!python prepend_body` or emit from your own route. It renders the component's *first* render directly, without a layout, so the component **cannot use any hook**: `use_state`, `use_ref`, `use_effect`, `use_location` and the rest all raise `RuntimeError: No life cycle hook is active. Are you rendering in a layout?`. Pass plain `#!python html.*` elements, or a component that calls none of them.
-   **There is no first-paint flash to optimise away**, because there is no first paint to replace.
-   A component that fails on the server fails *after* the page loads, leaving a blank `#!html <div id="app">`. When the page loads but shows nothing, check the server log before the browser console.

!!! info "Not the same as `ReactPyCsr`"
    `#!python ReactPyCsr` is the one that runs component code in the browser via [PyScript](https://pyscript.net/). `#!python ReactPy` runs components on the server and sends VDOM over a websocket. Both need a server; they differ in where your Python executes. See [ReactPyMiddleware](./reactpy-middleware.md) for mounting into an existing ASGI app.

## Related

-   [Creating a Standalone React App](../learn/creating-a-react-app.md) — the tutorial version of this page.
-   [ReactPyMiddleware](./reactpy-middleware.md) — mount components inside an existing ASGI application.
-   [ReactPyCsr](./reactpy-csr.md) — run component code in the browser.
