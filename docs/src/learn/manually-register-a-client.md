## Overview

<p class="intro" markdown>

"Registering a client" in ReactPy means telling the browser three things: which component to mount, where the socket lives, and which JavaScript modules it may import. The executors do all three for you. This page is for the cases where they cannot — a page you render yourself, several components on one document, or a component written in JavaScript that the server has to describe but cannot run.

</p>

!!! summary "You will learn"

    -   What `#!js mountReactPy` needs, and how to write the call by hand
    -   How to mount several components in one document, and what breaks if you mount twice into the same node
    -   How an author-supplied import map suppresses ReactPy's own
    -   How to register a JavaScript component so ReactPy can render it

## The three registrations

| What | Where it lives | Who normally writes it |
| --- | --- | --- |
| The root component to mount | `#!js componentPath` in `#!js mountReactPy`, and the backend's component registry | the executor's HTML template |
| The socket address | `#!js pathPrefix` + `#!js componentPath`, concatenated | the executor's HTML template |
| Bare-specifier resolution (`#!js "react"`, `#!js "react-dom"`) | `#!html <script type="importmap">` | injected only if no `#!html <script type="importmap" id="reactpy-importmap">` exists |

The full reference for the JavaScript side, including every option and its quirks, is [Client API](../reference/client-api.md). This page covers the parts the executors normally hide.

## Mounting by hand

The minimal call needs only an element and a path:

```html linenums="0"
<div id="app"></div>
<script type="module">
    import { mountReactPy } from "/reactpy/static/index.js";

    mountReactPy({
        mountElement: document.getElementById("app"),
        pathPrefix: "/reactpy/",
        componentPath: "main.counter/",
    });
</script>
```

Three details are load-bearing, all verified in a real browser:

-   **`#!js pathPrefix` must start and end with `#!js /`.** The client builds the socket URL by string concatenation, so `#!js "reactpy/"` on a host with a port throws `#!python TypeError: Failed to construct 'URL': Invalid URL` — and on a host *without* a port silently connects to a hostname like `#!js example.comreactpy`. The failure mode changes with deployment, which is what makes it nasty.
-   **`#!js componentPath` carries a trailing slash** and must name a component the server knows. `#!js "main.counter/"`, not `#!js "main.counter"`.
-   **The import must be `#!html <script type="module">`.** The bundle statically imports two sibling chunks; a classic script fails with `#!python SyntaxError: Cannot use import statement outside a module` before anything ReactPy-related runs.

The component itself lives in a Python module the backend can import. Under `#!python ReactPyMiddleware`, `#!python componentPath` is the dotted path you listed in `#!python root_components` plus a slash — the middleware matches `#!python ^{path_prefix}(?P<dotted_path>[a-zA-Z0-9_.]+)/$`. Under `#!python ReactPy` there is one root and `#!python componentPath` must be **omitted**: the client builds the URL as `#!js pathPrefix + componentPath` (`static/index.js`) and `ReactPy.match_dispatch_path` compares the result against `#!python dispatcher_path` exactly, so a stray `#!js "/"` produces `#!python /reactpy//`, matches nothing, and is rejected with `#!python NotImplementedError: ReactPy app received unsupported request of type 'websocket'`. See [The executors route differently](../reference/client-api.md#the-executors-route-differently).

!!! warning "Nothing stops you from mounting twice into the same element"

    `#!js mountReactPy` returns nothing and keeps no registry, so a second call into the same node is not rejected. Verified in Chrome with two mounts pointing at one `#!html <div>`: the **second** component's markup wins the visible tree, and the first keeps a fully live websocket — its socket stays `OPEN`, its server-side layout stays alive, and events it registered can still reach the server. You get one visible component and one invisible one consuming a connection and a layout each.

    The client does **not** unmount the first subtree; it renders over it. Nothing you can do from JavaScript will stop it — there is no `#!js unmountReactPy`. The only clean teardown is navigation or reload. If you are building a client-side router that swaps components, mount into a **fresh** element each time and remove the old one, accepting that the orphaned layout lives until the page does.

## Several components in one document

Each `#!js mountReactPy` call opens its own websocket and gets its own `#!python Layout`, which means separate hook state and no shared memory between them. Verified with two counters on one page: incrementing one left the other at zero, and the console logged two independent `#!python [ReactPy] Connected!` lines.

```html linenums="0"
<div id="header"></div>
<div id="cart"></div>
<script type="module">
    import { mountReactPy } from "/reactpy/static/index.js";

    mountReactPy({
        mountElement: document.getElementById("header"),
        pathPrefix: "/reactpy/",
        componentPath: "shop.header/",
    });
    mountReactPy({
        mountElement: document.getElementById("cart"),
        pathPrefix: "/reactpy/",
        componentPath: "shop.cart/",
    });
</script>
```

Under `#!python ReactPyMiddleware`, register both:

```python linenums="0"
from reactpy.executors.asgi import ReactPyMiddleware

app = ReactPyMiddleware(
    starlette_app,
    root_components=["shop.header", "shop.cart"],
)
```

!!! note "Separate roots do not share state"

    Two components on one page are two layouts. They cannot `#!python use_state` their way to agreement, and there is no event bus between them. If they must agree, either make them one component tree, or pass the shared value in as props from a single root — see [Sharing State Between Components](./sharing-state-between-components.md) and [Passing Data Deeply with Context](./passing-data-deeply-with-context.md).

You can also mount later, from a click handler or after a fetch — the call is ordinary JavaScript and nothing about it is privileged.

## Import maps

An import map is only needed when your model contains an `#!python importSource`, which is what JavaScript components produce. Bare specifiers like `#!js "react"` and `#!js "react-dom"` are resolved by the map; without one, the client falls back to its bundled preact and says so on `#!js console.debug`, at a level most consoles filter out.

The executors inject a map **only when one with a specific id is absent**:

```js linenums="0"
if (!document.querySelector("#reactpy-importmap")) { /* inject ReactPy's map */ }
```

The trigger is the **id, not the content**. Write your own map and give it that id, or ReactPy adds a second one alongside yours and the browser reports a conflict on the `#!js "react"` rule. See [The import map](../reference/client-api.md#the-import-map) for the three-case table.

ReactPy ships a helper that produces exactly that element, so you can decide the framework per page:

```python linenums="0"
from reactpy.executors.asgi import ReactPy
from reactpy.reactjs import import_reactjs

app = ReactPy(
    counter,
    html_head=html.head(import_reactjs("react", version="19")),
)
```

`#!python import_reactjs(framework=None, version=None, use_local=False)` returns a `#!python html.script` already carrying `#!json {"type": "importmap", "id": "reactpy-importmap"}`, so putting it in `#!python html_head` suppresses the automatic injection. `#!python "preact"` (the default) maps the four `#!js react*` specifiers onto `#!js esm.sh/v135/preact@10/compat`; `#!python "react"` uses real React at the version you pass (`#!python "19"` if you omit it); `#!python use_local=True` maps them to ReactPy's own bundled chunks, which is what the default injection does anyway.

!!! warning "`#!python use_local` rejects companions"

    `#!python import_reactjs(use_local=True, framework="react")` raises `#!python ValueError: use_local cannot be used with framework or version`. Choose one source or the other.

## Registering a JavaScript component

Python describes; the browser runs. A JavaScript component is any ES module that exports the names you ask for, and the module needs one extra export — a `#!python bind` function that tells the client how to create, render, and unmount nodes in a container the client owns:

=== "badge.js"

    ```js
    {% include "../../examples/manually_register_a_client/badge_module/badge.js" %}
    ```

=== "main.py"

    ```python
    {% include "../../examples/manually_register_a_client/badge_module/main.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The registration call gives you a normal constructor:

```python linenums="0"
from pathlib import Path

from reactpy.reactjs import component_from_file

Badge = component_from_file(Path("badge.js"), "Badge", name="badge")

Badge({"label": "alpha", "tone": "warn"}, "hello")
```

which produces the element the client executes:

```json linenums="0"
{
    "tagName": "Badge",
    "attributes": {"label": "alpha", "tone": "warn"},
    "children": ["hello"],
    "importSource": {
        "source": "badge.js",
        "sourceType": "NAME",
        "fallback": null,
        "unmountBeforeUpdate": false
    }
}
```

`#!python importSource` is the whole mechanism: `#!json sourceType` is `#!json "NAME"` or `#!json "URL"`, and the client resolves them differently — `#!json "NAME"` becomes `#!js await import("/<prefix>modules/" + source)` and `#!json "URL"` becomes `#!js await import(source)` directly.

Verified in Chrome: the badge rendered as `#!html <span class="warn">alpha: hello</span>`, with the `#!html <span>` coming from JavaScript and the wrapper from Python.

### The four registration functions

All in `#!python reactpy.reactjs`, all returning a `#!python VdomConstructor` (or a list, if you pass a list of names):

| Function | Source | Typical use |
| --- | --- | --- |
| `#!python component_from_url(url, import_names, ...)` | a URL the browser can reach | a CDN build, a dev server |
| `#!python component_from_npm(package, import_names, version="latest", cdn="https://esm.sh/v135", bundle=...)` | an NPM package, rewritten to a CDN URL | third-party React components |
| `#!python component_from_file(file, import_names, name="", symlink=False, ...)` | a file on disk, copied into the web-modules dir | a component you ship in your package |
| `#!python component_from_string(content, import_names, name="", ...)` | a string of JavaScript | tiny inline modules, tests |

`#!python reactpy.web.module_from_url` / `#!python module_from_file` / `#!python module_from_string` / `#!python export` do the same thing and are all deprecated — they `#!python warn(DeprecationWarning)` telling you to use the `#!python component_from_*` form.

### Serving the module

A `#!json "NAME"` module is copied into `#!python config.REACTPY_WEB_MODULES_DIR` and fetched from `{path_prefix}modules/` — which is why a custom backend must serve that directory, and why the built-in ones do:

```python linenums="0"
from reactpy.config import REACTPY_WEB_MODULES_DIR

modules_app = ServeStaticASGI(not_found, root=REACTPY_WEB_MODULES_DIR.current, prefix="/reactpy/modules/")
```

!!! warning "The default web-modules directory is a temporary directory"

    `#!python REACTPY_WEB_MODULES_DIR` defaults to a fresh `#!python TemporaryDirectory` created at import (`config.py`). It is **per process**: read it in one process and you get a path that does not exist in the next. Two consequences:

    -   Under a multi-worker server, workers get different directories and a module registered by one is 404 for another. Pin it — pass `#!python web_modules_dir=Path(...)` to the executor or set the `#!python REACTPY_WEB_MODULES_DIR` environment variable to one shared path.
    -   The upstream config docstring says the directory must be treated as a black box. Do not read from it yourself; register modules and let the client fetch them.

A `#!json "URL"` module needs no serving at all — the browser goes to the URL. That makes CDN registration the simpler path when you have a network, and a self-hosted directory the right one for offline or air-gapped use.

### Options worth knowing

-   **`#!python fallback`** — what to show while the module loads. Pass an element (`#!python html.p("loading...")`). Without it there is nothing, and a slow module reads as a broken page.
-   **`#!python allow_children`** — set `#!python False` for a component that takes props only. Passing a child then raises `#!python TypeError: 'Badge' nodes cannot have children.` at the call site rather than silently dropping it.
-   **`#!python unmount_before_update`** — unmount and rebuild on every update. Only for packages that fail to re-render on prop change; it costs a full DOM rebuild each time.
-   **`#!python resolve_imports`** — parse the module to learn its export names, so a typo fails in Python at registration instead of in the browser at render. Off by default for `#!python component_from_file`/`#!python component_from_string`; it walks imports to `#!python resolve_imports_depth` (default 5).

!!! warning "A wrong export name fails at different times depending on a flag"

    With `#!python resolve_imports=True`, `#!python component_from_file("badge.js", "Nope")` raises immediately:

    ```text linenums="0"
    ValueError: 'badge.js' does not contain 'Nope'
    ```

    With it off — the default — you get no Python error, and instead the browser logs, verbatim including the typo:

    ```text linenums="0"
    Module from source {"source": "badge.js", "sourceType": "NAME"} does not export Nope
    ```

    and nothing renders. Turn the flag on during development; it turns a console hunt into a stack trace.

!!! warning "A bad `bind` is a console error, not an exception"

    If your module's `#!python bind` does not return an object with `#!python create`, `#!python render`, and `#!python unmount`, the client logs `#!python <source> returned an impropper binding` — misspelling in the upstream string — and renders nothing. Python stays happy. The message goes to `#!python console.error`, so it is easy to miss when the component simply is not there.

## Summary

-   Registering a client means the component path, the socket prefix, and an import map — the executors write all three for you.
-   `#!js pathPrefix` needs both slashes, `#!js componentPath` needs its trailing slash, and the import must be a module script.
-   Mount each component into its own element. Mounting twice into one node leaves a live, invisible websocket you cannot close.
-   Multiple mounts on a page are multiple layouts with no shared state; pass shared values as props instead.
-   ReactPy injects an import map only if no element with `#!json id="reactpy-importmap"` exists — the id, not the content, is the trigger. `#!python import_reactjs()` produces that element.
-   JavaScript components are ordinary ES modules with a `#!python bind` export, registered with `#!python component_from_url`/`#!python _npm`/`#!python _file`/`#!python _string`, and served from `#!python {prefix}modules/` unless they are URL-sourced.
-   The default web-modules directory is a per-process temporary directory; pin it under any multi-worker deployment.

## Related

-   [Client API](../reference/client-api.md) — the full `#!js mountReactPy` reference and failure-mode table
-   [Creating Backends](./creating-backends.md) — serving `#!python static/` and `#!python modules/` yourself
-   [Protocol Structure](../reference/protocol-structure.md) — what travels over the socket the mount opens
-   [Common Props](../reference/common-props.md#importsource) — the `#!python importSource` model shape
-   [ReactPyMiddleware](../reference/reactpy-middleware.md) — mounting components into pages you already own
