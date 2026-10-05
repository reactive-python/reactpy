## Overview

<p class="intro" markdown>

`use_location` is a ReactPy hook that returns the URL the browser is currently showing.

</p>

```python linenums="0"
location = use_location()
```

Your components run on the server and know nothing about the browser unless you ask. `use_location` is how you ask: it reports the page the visitor is looking at, so navigation, breadcrumbs, and query-driven views can be built from it.

---

## Reference

### `use_location()` { #use-location }

Call it at the top level of a component. It takes no arguments.

```python linenums="0"
from reactpy import use_location
```

#### Returns

A `reactpy.types.Location` — a plain dataclass with two fields, both required:

-   **`path`**: The URL path, mirroring `window.location.pathname`. For example `#!python "/reports/2024/q1"`.
-   **`query_string`**: The query string, mirroring `window.location.search` — **including the leading `#!python "?"`**. For example `#!python "?tab=2&user=ada"`, or `#!python ""` when there is no query.

It is mutable and compares by value. Import the type with `#!python from reactpy.types import Location`; it is not exported from the `#!python reactpy` namespace.

#### Caveats

-   **The `#!python "?"` is part of the value.** `#!python parse_qs(location.query_string)` mis-parses the first parameter, producing a key `#!python "?tab"` instead of `#!python "tab"`. Strip it: `#!python parse_qs(location.query_string.lstrip("?"))`. See the example below.
-   **It is not the ASGI scope's path.** `use_scope()["path"]` is the ReactPy websocket endpoint — `#!python "/reactpy/"` — for every component on every page. `use_location().path` is the page the visitor is on. Verified in Chrome: visiting `#!python /some/deep/page?tab=2&user=ada` gives `#!python Location(path='/some/deep/page', query_string='?tab=2&user=ada')` while the scope still says `#!python "/reactpy/"`.
-   **The browser reports it, so it is untrusted.** The value arrives as parameters on the websocket URL and ReactPy does not validate it against your routes. Treat it as input: match it, never interpolate it into a `#!python "href"` or a filesystem path without checking.
-   **It needs a live connection.** Called in a test's plain `Layout` render, it raises `#!python RuntimeError: No backend established a connection.`. See [working without a connection](#working-without-a-connection).
-   **It does not exist under client-side rendering.** With `#!python ReactPyCsr`, Python runs in the browser but no ReactPy connection object is established, so the hook raises the same `RuntimeError`. Verified in Chrome against a CSR app. Read `window.location` through JavaScript there instead.
-   Like every hook, call it **only at the top level** — never in a loop, a conditional, or after an early `#!python return`.

---

## Usage

### Reading query parameters

`query_string` arrives exactly as the browser shows it, which means the leading `#!python "?"` is attached to the first parameter's name. That is the one detail that trips people up.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_location/query_params/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

With `#!python ?tab=sales&sort=price` this renders "Products — sales", sorted by price. With no query string at all it falls back to the defaults.

### Building navigation from the current path

Splitting the path gives you the trail from the site root to wherever the visitor is.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_location/breadcrumb/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

On `#!python /reports/2024/q1` this produces links to `#!python /reports`, `#!python /reports/2024`, and `#!python /reports/2024/q1`. Build the URLs yourself rather than pasting path segments in raw if they can contain anything you did not choose.

### Working without a connection

A component that reads the location should say what it shows when there is none — a unit test, a `#!python reactpy_to_string` call, or a CSR page all take this path.

```python linenums="0"
@component
def page_title():
    try:
        location = use_location()
    except RuntimeError:
        return html.h1("(no browser yet)")
    return html.h1(f"at {location.path}")
```

Verified both ways through `Layout`: with no provider it renders the fallback; with one it renders the path.

---

## Troubleshooting

### My query parameters never match

The leading `#!python "?"`. `#!python parse_qs("?tab=2")` gives `#!python {"?tab": ["2"]}`. Strip it before parsing.

### It says `/reactpy/`

You are reading `use_scope()["path"]`, which is the websocket endpoint. Use `use_location().path` for the page.

### It raises in my tests

Expected: a bare `Layout` render has no connection. Either wrap the call as shown above, or inject one — see [`use_connection`](./use-connection.md).

### It raises inside a `ReactPyCsr` app

Client-side rendering establishes no connection, so there is nothing to report. Read the URL from JavaScript instead, or move that component server-side.
