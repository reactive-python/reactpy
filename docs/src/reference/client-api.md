## Overview

<p class="intro" markdown>

`mountReactPy` is the browser-side entry point: one exported function, one websocket, no build step. Everything else in the browser is the server's business.

</p>

```js linenums="0"
import { mountReactPy } from "/reactpy/static/index.js";

mountReactPy({
  mountElement: document.getElementById("app"),
  pathPrefix: "/reactpy/",
  componentPath: "main.counter/",
});
```

The executors emit this call for you — see [ReactPy](./reactpy.md) and [ReactPyMiddleware](./reactpy-middleware.md). You need to write it yourself only when you serve the document from your own route, or when the defaults do not fit.

---

## Reference

### `mountReactPy(options)`

```js linenums="0"
import { mountReactPy } from "{pathPrefix}static/index.js";
```

The bundle is served by ReactPy itself, under `{pathPrefix}static/`, alongside two chunks it imports by relative path. There is nothing to install and nothing to build: it is preact and the client, pre-bundled.

#### Parameters

A single object.

-   **`mountElement`**: The DOM node to render into. Not optional in effect — passing `#!js null`, which is what `#!js getElementById` returns for a missing id, dies with `TypeError: Cannot read properties of null (reading '__k')` before anything is logged.

-   **`pathPrefix`**: `#!js string`. Must start *and* end with `#!js /`. Concatenated verbatim with `#!js componentPath`, so a missing slash on either side produces a URL that is *wrong* rather than invalid — which is worse, because nothing rejects it. A value with no leading slash (`#!js "reactpy/"`) or no `#!js pathPrefix` at all may fail early with `TypeError: Failed to construct 'URL': Invalid URL`, but only when the page's host includes a port. See [The URL is built by concatenation](#the-url-is-built-by-concatenation).

-   **`componentPath`**: `#!js string`, optional. The dotted path of the root component, **with a trailing slash**: `#!js "main.counter/"`. `#!python ReactPyMiddleware` requires it. `#!python ReactPy` takes the opposite view and requires it be omitted — see [The executors route differently](#the-executors-route-differently).

-   **`reconnectInterval`**: `#!js number` of ms. `#!js 750`.

-   **`reconnectMaxInterval`**: `#!js number` of ms. `#!js 60000`.

-   **`reconnectMaxRetries`**: `#!js number`. `#!js 150`.

-   **`reconnectBackoffMultiplier`**: `#!js number`. `#!js 1.25`.

#### Returns

Nothing.

!!! warning "There is no `unmountReactPy`"

    The bundle exports exactly one name. Verified by importing it and listing the keys: `mountReactPy`, nothing else. `mountReactPy` returns nothing and takes no callback, so you get no handle to keep and no supported way to stop a component.

    Removing the mount element from the DOM does not stop it either. The subtree is **detached, not unmounted**: `mountReactPy` calls preact's `render(...)` into the node and never the matching unmount. Verified in a browser — after removing the node, a click dispatched into the detached subtree still reached the server and incremented its state, and the websocket stayed `OPEN` in both directions. The component keeps reconciling into an orphan nobody can see.

    The only clean teardown is to navigate or reload. If you are building a single-page app that swaps components on the client, the closest available tool is `#!js onMessage`'s return value, which unsubscribes a handler — that stops the client applying updates, but leaves the socket and the server's layout alive.

!!! warning "Reconnect options reject zero, not just wrong types"

    The defaults are applied with JavaScript's `||`, not `??`, so *any* falsy value is replaced by the default. Passing `#!js reconnectMaxRetries: 0` to mean "do not retry" gets you the default 150 instead, and `#!js reconnectInterval: 0` gets you 750 ms.

    To actually stop retrying, pass a **negative** `#!js reconnectMaxRetries`. The retry test is `retries >= maxRetries` and negatives survive `||`, so `#!js reconnectMaxRetries: -1` connects once and then gives up — measured at exactly one attempt, by running the client's own `createReconnectingWebSocket` against a stub socket.

    The retry counter is also not what it appears to be. It counts *consecutive* failures, because a successful open resets it to zero along with the backoff interval. Measured against a stub that accepts each connection and closes it 2 ms later, `#!js reconnectMaxRetries: 2` with a 1 ms interval produced **342** attempts in 1.5 s: every reconnect succeeds, so the counter never reaches the limit. Only attempts that fail to open at all accumulate.

    Which leads to the sharper edge: **a handshake that is refused is never retried at all.** If the socket never reaches `OPEN`, the close handler logs `Failed to connect!` and returns without scheduling anything. So `#!python ReactPyMiddleware` answering `403` — a wrong `#!js componentPath`, a wrong `#!js path_prefix` — gives you one attempt, one line in the console, and a permanently empty element. Nothing recovers without a reload. Retries exist only for connections that opened and then dropped.

---

## What `mountReactPy` does

`mountReactPy` does five things (`static/index.js`):

1.  Picks the websocket scheme from the page: `#!js wss:` under `#!js https:`, otherwise `#!js ws:`.
2.  Builds the URL as `#!js scheme // host + pathPrefix + componentPath`, then appends `#!js path=window.location.pathname` and, only if the page has a query string, `#!js qs=window.location.search`.
3.  Sets `#!js jsModulesPath` to `#!js origin + pathPrefix + "modules/"`, the base from which JavaScript modules named by an element's `#!json importSource` are imported.
4.  Constructs the client, which wires up a reconnecting websocket.
5.  Renders the layout into `#!js mountElement`.

Steps 2 and 3 are the only places the browser's own URL is read. Once the socket is open, the server's view of the URL is whatever those two parameters said — see [Use Location](./use-location.md).

### The URL is built by concatenation

Nothing inserts a slash for you, so both halves have to arrive correctly formed. The four ways to get it wrong, each verified from a page with the resulting socket URL (against `#!python ReactPyMiddleware` on a host with a port):

| `#!js pathPrefix` | `#!js componentPath` | Socket path | Result |
| --- | --- | --- | --- |
| `#!js "/reactpy/"` | `#!js "main.counter/"` | `#!js /reactpy/main.counter/` | Connects. |
| `#!js "/reactpy"` | `#!js "main.counter/"` | `#!js /reactpymain.counter/` | `403`, then `Failed to connect!` |
| `#!js "/reactpy/"` | `#!js "main.counter"` | `#!js /reactpy/main.counter` | `403`, then `Failed to connect!` |
| `#!js "/reactpy/"` | omitted | `#!js /reactpy/` | `403`, then `Failed to connect!` |

`ReactPyMiddleware` matches the websocket path against `#!python ^{path_prefix}(?P<dotted_path>[a-zA-Z0-9_.]+)/$`. Rows two through four fail that pattern, so they fall through to your own ASGI app, which answers `403`.

Read the browser's own error line, not ReactPy's. The client emits a bare `#!js Failed to connect!`; the URL that caused it is on the line above, in the browser's message, without the `#!js [ReactPy]` prefix.

!!! warning "The `||` defaults and the `URL` constructor make this host-dependent"

    Two of these fail *earlier* than the table suggests, and only sometimes. `new URL(...)` throws `TypeError: Failed to construct 'URL': Invalid URL` for a missing or slashless `#!js pathPrefix` — but only when the host carries a port, because `ws://example.comreactpy/main.counter/` parses happily as host `#!js example.comreactpy`. Verified with Node's `URL`, the same implementation Chrome uses:

    | Host | `#!js pathPrefix` | Outcome |
    | --- | --- | --- |
    | `#!js 127.0.0.1:8842` | `#!js ""` | `TypeError: Invalid URL` |
    | `#!js 127.0.0.1:8842` | `#!js "reactpy/"` | `TypeError: Invalid URL` |
    | `#!js example.com` | `#!js ""` | Connects to host `#!js example.commain.counter` |
    | `#!js example.com` | `#!js "reactpy/"` | Connects to host `#!js example.comreactpy` |

    So the mistake that fails loudly in development fails *silently* in production, sending the socket to a hostname that does not exist. Check the host, not just the path.

### The executors route differently

The last table row is not a universal truth, and this is where the two executors part company. `#!python ReactPy` — the standalone app — overrides the matcher:

```python linenums="0"
def match_dispatch_path(self, scope):
    """Method override to remove `dotted_path` from the dispatcher URL."""
    return str(scope["path"]) == self.dispatcher_path
```

So the two want opposite things:

| | `#!js componentPath` | Unmatched dotted path |
| --- | --- | --- |
| `#!python ReactPyMiddleware` | **required**, with trailing slash | Falls through to your app (with Starlette's websocket handler, a `403` handshake rejection) |
| `#!python ReactPy` | **must be omitted** — the bare `{pathPrefix}` is the route | socket error; the server logs `NotImplementedError` (see below) |

Verified against both executors on the same build: the middleware accepts `#!js /reactpy/main.counter/` and refuses `#!js /reactpy/`; the standalone app does exactly the reverse. A mount snippet copied from one executor to the other therefore produces a socket that never opens.

The standalone rejection does not read like a normal exception. `executors/asgi/standalone.py`, `ReactPyApp.__call__` builds `msg` as a **tuple** of a `%`-format template and its arguments and raises `NotImplementedError(msg)` without ever formatting it, so the server logs it verbatim — the placeholders survive and the path is appended:

```text linenums="0"
NotImplementedError: ("ReactPy app received unsupported request of type '%s' at path '%s'", 'websocket', '/reactpy//')
```

Do not search the log for `...type 'websocket'`; search for `unsupported request of type`. The same tuple is written by `_logger.warning` immediately before the raise.

### The socket does not open immediately

Constructing the client does not connect. The websocket waits on a `#!js ready` promise, and that promise is resolved by the *first* `#!js onMessage` registration — nothing else in the codebase resolves it. The layout registers its handler from an effect, so the client connects only after that effect runs, which is why `#!js [ReactPy] Starting client...` always precedes `#!js Connected!` and never follows it.

Because `onMessage` is the sole resolver, a run where the layout's effect never fires produces a fourth console state: no `#!js Starting client...`, no socket attempt, and no error. Treat that as "the bundle ran but the component never mounted" rather than a network problem — the other four messages below are all *post*-connect.

Two consequences of the gating:

-   Reconnection refreshes `#!js path` and `#!js qs` from the live page on every attempt, but never re-reads `#!js componentPath` — that was baked into the URL at mount time.
-   Messages sent before the socket reports `OPEN` are buffered rather than dropped, and flushed on the next `#!js open`. They survive a reconnect — but once retries are exhausted the buffer is never drained.

Note that `#!js path` and `#!js qs` are query parameters, not path segments. The full form is `#!js ws://127.0.0.1:8000/reactpy/main.counter/?path=%2F&qs=%3Ftab%3D1`, and the server reads them with `#!python strict_parsing=True`. When building a test client by hand, copy a real frame from the browser rather than assembling one from the tables on this page.

---

## The import map

For a server-rendered component, no import map is needed. The bundle imports its own two chunks by relative path and has preact inlined, so nothing it loads statically is a bare specifier. Verified: a page with no map at all mounted, connected, and the server never received a single request for `#!js preact.js`.

The map becomes load-bearing only when the model contains `#!json importSource` **and** the resolved module does not export its own `#!js bind`. Rendering such an element goes through `#!js loadImportSource`, which uses the module's `#!js bind` when it is a function and only otherwise calls `#!js infer_bind_from_environment()` — the function that runs `#!js await import("react")` and `#!js await import("react-dom/client")`. Those are *dynamic* imports, which are exactly what an import map resolves. If they succeed, real React renders the subtree; if they fail, the client falls back to its own preact bindings and says so:

```text linenums="0"
ReactPy will render JavaScript components using internal bindings for 'react'.
```

Note the level and the prefix: that line is `#!js console.debug` with no `#!js [ReactPy]` prefix, so it is invisible in a console filtered to warnings, and it is not caught by filtering on `[ReactPy]`.

The executors' bootstrap injects a map only if none is present — and the check is keyed on one specific id:

```js linenums="0"
if (!document.querySelector("#reactpy-importmap")) { /* inject ReactPy's map */ }
```

The **id is the trigger, not the content**. Verified across three pages, all served through the same executor bootstrap:

| Page | ReactPy injects | What you see |
| --- | --- | --- |
| No map | Yes, as `#!html <script type="importmap" id="reactpy-importmap">` | `ReactPy did not detect a suitable JavaScript import map. Falling back to ReactPy's internal framework (Preact).` |
| Your own map, any other id | Yes — a second map appears, alongside yours | The same `did not detect` line, plus the browser's own `An import map rule for specifier 'react' was removed, as it conflicted with an existing rule.` |
| Your own map with `id="reactpy-importmap"` | No | Nothing at all. |

The two messages have different authors, which matters when you search a minified bundle. The `#!js did not detect` line is written by the **Python** side of the bootstrap — `executors/utils.py`, `server_side_component_html` emits it inside the inline `#!html <script>` it generates, so it is in the served HTML, not in the bundle. The `#!js internal bindings for 'react'` line comes from the **client** — `#!js infer_bind_from_environment` in `bind.tsx`, reached from `loadImportSource` in `#!js vdom.tsx`. Both are unprefixed `#!js console.debug`, so neither shows up under a `[ReactPy]` filter.

To control resolution yourself, use that exact id. Two maps is worse than untidy: the browser keeps the **first** rule it sees for a specifier and discards the later one, so with two maps the winner is decided by document order — which is why the warning above names a rule being *removed*.

The map ReactPy writes maps all four React specifiers onto its own preact files under `{pathPrefix}static/`. Save the page and the app under those exact names — the dotted path in `#!js componentPath` is a Python module path, and `#!python main.counter` only resolves when this file is called `#!python main.py`:

=== "page.html"

    ```html
    {% include "../../examples/reference_client_api/import_map/page.html" %}
    ```

=== "main.py"

    ```python
    {% include "../../examples/reference_client_api/import_map/main.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Serve it with `#!bash uvicorn main:my_app`. Verified in a browser: the counter rendered and logged `#!js [ReactPy] Connected!`, and no request for `#!js preact.js` reached the server — confirming the client never consulted the map.

---

## The client object

`mountReactPy` builds on two classes from the `@reactpy/client` source package. Neither is reachable from a page — the shipped bundle exports `mountReactPy` and nothing else — but you meet them reading the bundle, and they are what a custom binding's `#!js sendMessage` and `#!js onMessage` come from.

`BaseReactPyClient` is the transport-independent half:

| Member | Purpose |
| --- | --- |
| `#!js onMessage(type, handler)` | Register a handler for a message `#!js type`. Returns an unsubscribe function. |
| `#!js handleIncoming(message)` | Dispatch to the handlers for `#!js message.type` — except live event reads, which it answers itself. |
| `#!js eventProxy` | The `#!js EventProxyRegistry` created with the client, which holds the live objects behind event handles. |
| `#!js ready` | Promise, resolved by the first `#!js onMessage` call. Gates the connection. |

One type never reaches a registered handler. `#!js handleIncoming` routes `#!js "event-proxy-request"` straight to the client's own `#!js eventProxy` registry (`client.ts`), which is why live event reads work even in a binding that registered no handler for them — and why `#!js Received message without handler` is never logged for one. Build a client that does not extend `#!js BaseReactPyClient` and you must answer those requests yourself, or every `#!python await` on an event ends in `#!python EventProxyTimeout` — see [Protocol Structure](protocol-structure.md#the-event-proxy-round-trip).

Messages with no `#!js type`, or with one nobody registered for, are logged and dropped — the connection is never closed over a bad message:

```text linenums="0"
Received message without type {…}
Received message without handler {…}
```

`ReactPyClient` adds the websocket, plus `#!js sendMessage(message)` and `#!js loadModule(name)`. They are not peers. `#!js sendMessage` is handed to a JavaScript binding as its way to talk back; `#!js loadModule` is called *for* the binding, by ReactPy, to pull in a web module named by an `#!json importSource` whose `#!python sourceType` is `#!python "NAME"` — it resolves against `#!js jsModulesPath`, which is what the server's web modules directory is mounted under.

---

## The console

Every message ReactPy writes is prefixed `#!js [ReactPy]`, so filtering the console by that string shows the whole story of a mount. The set is finite:

| Message | Meaning |
| --- | --- |
| `#!js Starting client...` | The layout registered its handler; a connection attempt is about to start. |
| `#!js Connected!` | The handshake completed. Resets the retry counter and the backoff interval. |
| `#!python Failed to connect!` | The socket closed **without ever having opened**. Usually a routing miss — see [The URL is built by concatenation](#the-url-is-built-by-concatenation). |
| `#!python Disconnected!` | The socket closed **after** at least one successful open. |
| `#!python Reconnecting in 0.7500 seconds...` | A retry is scheduled. The number is the current backoff interval. |
| `#!python Connection max retries exhausted!` | Giving up. The page needs a reload; nothing recovers after this. |
| `#!python did not detect a suitable JavaScript import map...` | `#!html <script type="importmap" id="reactpy-importmap">` was absent. Informational — see [The import map](#the-import-map). |

`#!python Failed to connect!` and `#!python Disconnected!` are distinguished by whether the socket ever opened, which makes them useful as a diagnosis: the first means the server never routed the request, the second means it did and then the link dropped. Both are logged at `#!python console.info` level, so a console set to warnings-only shows nothing at all — check the level before concluding the client is silent.

---

## A hand-written mount

Nothing is required beyond an element and the call. Both files below were run to produce the `#!python [ReactPy] Connected!` and the incremented counter quoted on this page.

=== "main.py"

    ```python
    {% include "../../examples/reference_client_api/hand_written_bootstrap/main.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The component is registered with `#!python root_components`, and the `#!js componentPath` in the page — `#!python "main.counter/"` — is that dotted path with a slash appended.

!!! warning "The 404 in the console is usually not yours"

    A page like this logs one `Failed to load resource: 404` on every load. It is `#!python /favicon.ico`, which no browser should be told about by a component framework. Verified: it appears with everything else working. Ignore it; a *second* 404 naming a `#!python /reactpy/...` path means the bundle could not be fetched, which does mean the mount will not happen.

---

## Failure modes

| Symptom | Cause |
| --- | --- |
| `#!python TypeError: Cannot read properties of null (reading '__k')` | `#!python mountElement` is `#!python None`. The id does not exist, or the script ran before the element was parsed. |
| `#!python TypeError: Failed to construct 'URL': Invalid URL` | `#!python pathPrefix` missing, or missing a leading or trailing slash. No request is ever made. |
| `#!js mountReactPy()` throws `Cannot read properties of undefined` | No options object at all. |
| `#!python Failed to connect!`, nothing rendered | The socket URL did not match the server's route. Read the URL in the browser's own error line. |
| `#!python [ReactPy] Connected!`, empty element, nothing in the browser console | The component path is unknown to the server. The failure is *server-side*: `RuntimeError: Attempting to use an unregistered root component <path>.` Check the server log, not the browser. |
| Renders once, never updates | Handlers are not firing — usually a snake_case event name such as `#!python on_click`. See [Responding to Events](../learn/responding-to-events.md). |
| Component vanishes when you remove it from the DOM, socket still open | Expected. There is no unmount that closes the socket. |
| Two import maps in the document, React warnings about a removed rule | Your map does not use `#!html id="reactpy-importmap"`. |

---

## Related

-   [Protocol Structure](./protocol-structure.md) — what travels over the socket this function opens.
-   [ReactPy](./reactpy.md) and [ReactPyMiddleware](./reactpy-middleware.md) — the executors that generate this call.
-   [Jinja](./jinja.md) — emitting mounts from templates, including `{% pyscript_component %}` for running Python in the page.
-   [Use Location](./use-location.md) — reading back the `#!js path` and `#!js qs` the client sends.
