## Overview

<p class="intro" markdown>

ReactPy renders on the server and paints in the browser. A single websocket carries four message types: the server sends `#!python "layout-update"` patches, the client sends `#!python "layout-event"` interactions, and a handler which wants to read the browser goes back and forth over `#!python "event-proxy-request"` / `#!python "event-proxy-response"`.

</p>

```text linenums="0"
server --{"type": "layout-update", "path": ..., "model": ...}--------------->  client
server <--{"type": "layout-event", "target": ..., "data": [...]}------------  client
server --{"type": "event-proxy-request", "eventId": ..., "path": ...}------->  client
server <--{"type": "event-proxy-response", "requestId": ..., "value": ...}-  client
```

The last two are new, and they change what an event is. Nothing about the DOM event is serialized at all: the client keeps the live object in a registry of its own and sends the server a handle. What the server can do with that handle — and what happens when the browser never answers — is the subject of [The event proxy round trip](#the-event-proxy-round-trip).

---

## The connection

Every mounted component opens exactly one websocket. The client builds it from the `#!python pathPrefix` and `#!python componentPath` it was handed at mount time (`static/index.js`, `mountReactPy`):

```text linenums="0"
ws://<host><pathPrefix><componentPath>?path=<page path>&qs=<page query string>
```

With the default `#!python REACTPY_PATH_PREFIX` of `#!python "/reactpy/"` and a component registered as `#!python "main.counter/"`, mounting on `#!python /page?tab=1` opens:

```text linenums="0"
ws://127.0.0.1:8000/reactpy/main.counter/?path=%2Fpage&qs=%3Ftab%3D1
```

Two things about that URL are load-bearing:

-   **The trailing slash after the dotted path is required.** The server matches the websocket path against

    ```text linenums="0"
    ^{path_prefix}(?P<dotted_path>[a-zA-Z0-9_.]+)/$
    ```

    which ends in `#!python /$`. Without the slash the route never matches, the request falls through to your own ASGI app, and the handshake is refused. Verified from a page: `#!python ws://…/reactpy/main.counter/?path=/` opens, `#!python ws://…/reactpy/main.counter?path=/` fails with `Unexpected response code`, and the console logs `#!python [ReactPy] Failed to connect!`.

-   **`path` and `qs` are how the component learns its URL.** ReactPy runs on the server, where the browser's `#!python location` does not exist. The client copies `#!python window.location.pathname` into `#!python path` and `#!python window.location.search` into `#!python qs`; the server parses them back out (`executors/asgi/middleware.py`, `_location_from_websocket_query_string`) into the `#!python Location` that `#!python use_location()` returns. They are percent-encoded and carried in the websocket's own query string, so a server that normalises the handshake URL cannot silently rewrite them.

!!! warning "Reconnection does not re-read the mount"

    When the socket drops, the client waits and reconnects. Each attempt refreshes `#!python path` and `#!python qs` from the current page, but it never re-reads `#!python componentPath` or the connect options — those were captured when the element mounted. A client-side navigation that changes which component belongs on the page needs a fresh mount, not a reconnect.

The client retries with exponential backoff: `#!python REACTPY_RECONNECT_INTERVAL` (750 ms) times `#!python REACTPY_RECONNECT_BACKOFF_MULTIPLIER` (1.25) per attempt, capped at `#!python REACTPY_RECONNECT_MAX_INTERVAL` (60 s), for `#!python REACTPY_RECONNECT_MAX_RETRIES` (150) tries. Those are arguments to `#!python mountReactPy(...)`; see [ReactPyMiddleware](./reactpy-middleware.md) for the bootstrap that emits them.

---

## The server-to-client message

One message type goes down the wire. Its keys are fixed (`reactpy.types.LayoutUpdateMessage`):

| Key | Value | Meaning |
| --- | --- | --- |
| `#!python "type"` | `#!python "layout-update"` | Always this literal. |
| `#!python "path"` | `#!python str` | A JSON Pointer into the client's copy of the model. `#!python ""` means *replace everything*. |
| `#!python "model"` | `#!python dict` | The value to place at that pointer. |

The model is JSON, not a `#!python VdomDict`. Six key names are legal (`reactpy/types.py`, `ALLOWED_VDOM_KEYS`), and only `#!python tagName` is required:

| Key | Value | Notes |
| --- | --- | --- |
| `#!python "tagName"` | `#!python str` | The DOM tag, or `#!python ""` for a wrapper element. |
| `#!python "children"` | `#!python list` | Nested models or plain strings. |
| `#!python "attributes"` | `#!python dict` | Sent to the client as written, and written to the DOM essentially verbatim. Two ReactPy-specific exceptions: `#!python key` is read for reconciliation and consumed, never becoming an attribute, and `#!python _reactpy_ack_seq` is deleted by the client before render. |
| `#!python "eventHandlers"` | `#!python dict` | Handler name to target spec, described below. |
| `#!python "inlineJavaScript"` | `#!python dict` | Handler name to JavaScript source string. |
| `#!python "importSource"` | `#!python dict` | Marks an element as coming from a JavaScript module. |

Any other key name is rejected by `#!python VdomDict` while the element is being built (`reactpy/types.py`):

```text linenums="0"
ValueError: Invalid keys: {'bogus'}.
```

The wire schema in `core/vdom.py`, `VDOM_JSON_SCHEMA` is a looser thing: it lists these six plus `#!python "error"` (which the layout injects when a component raises), and it is only consulted when `#!python REACTPY_CHECK_VDOM_SPEC` or `#!python REACTPY_DEBUG` is on.

Here is a real mount message for a counter, captured off the wire:

```json linenums="0"
{
  "type": "layout-update",
  "path": "",
  "model": {
    "tagName": "",
    "children": [
      {
        "tagName": "",
        "children": [
          {
            "tagName": "",
            "children": [
              {
                "tagName": "div",
                "children": [
                  {"tagName": "h1", "children": ["count is 0"]},
                  {
                    "tagName": "button",
                    "eventHandlers": {
                      "onClick": {
                        "target": "/0/0/0/1:onClick",
                        "preventDefault": false,
                        "stopPropagation": false
                      }
                    },
                    "children": ["Add"]
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### Wrapper elements

Read from the top, that model is *three* elements with `#!python "tagName": ""` before the `#!python div` appears. ReactPy needs somewhere to put a component's output that is not itself a DOM node, and it does not reuse your tag for the purpose.

Do not depend on how many there are. The count is an implementation detail that shifts with structure: the same component produced one wrapper rendered bare through `Layout`, and three behind the ASGI executor's context provider. Never index the tree by position, and never assume the root has a tag name. The client renders a wrapper as a fragment, so it costs you nothing on screen.

### Patches, not re-renders

The server does not resend the tree. When only an inner component's state changes, it sends the subtree rooted where that component renders:

```json linenums="0"
{
  "type": "layout-update",
  "path": "/children/0/children/0",
  "model": {
    "tagName": "",
    "children": [
      {
        "tagName": "div",
        "children": [
          {"tagName": "h1", "children": ["count is 1"]},
          {
            "tagName": "button",
            "eventHandlers": {
              "onClick": {
                "target": "/0/0/0/1:onClick",
                "preventDefault": false,
                "stopPropagation": false
              }
            },
            "children": ["Add"]
          }
        ]
      }
    ]
  }
}
```

That is the whole reply to a click: one-third the depth of the mount, and the only text that changed is inside it. The pointer indexes the *model*, and `#!python path: ""` replaces the root — which is what a state change in the topmost component produces.

A patch **replaces** rather than merges, so whatever subtree it carries is complete: keys you would expect to be sticky, `#!python eventHandlers` among them, are resent inside it. Nothing is deleted by a patch; a smaller subtree simply arrives with fewer children.

### Errors arrive as a model

A component that raises during render does not kill the socket. The layout sends an element whose `#!python tagName` is empty and whose `#!python error` is the message, which the client prints in a `#!html <pre>` in place of the component:

```json linenums="0"
{
  "type": "layout-update",
  "path": "",
  "model": {
    "tagName": "",
    "error": "ValueError: Expected a VDOM element dict, not {'noTag': True}"
  }
}
```

The schema ties the two together: when `#!python error` is present, `#!python tagName` must be empty. Without `#!python REACTPY_DEBUG=1` the same element carries `#!python "error": ""` — an empty string, which the client renders as nothing, so the component silently disappears instead of showing a blank box.

---

## The client-to-server message

One message type goes up (`reactpy.types.LayoutEventMessage`):

| Key | Value | Meaning |
| --- | --- | --- |
| `#!python "type"` | `#!python "layout-event"` | Always this literal. |
| `#!python "target"` | `#!python str` | The handler's `#!python target`, copied from the model. |
| `#!python "data"` | `#!python list` | The arguments for the handler. Usually one event handle. |
| `#!python "seq"` | `#!python int` | Optional. A client-assigned counter, per element. |

A real click on the button above:

```json linenums="0"
{
  "type": "layout-event",
  "target": "/0/0/0/1:onClick",
  "data": [{"__reactpy_event__": {"id": "lzk4q1-0"}, "type": "click"}],
  "seq": 1
}
```

### How `data` is built

The client does not serialize the DOM event. It stores the live object in a registry and sends a handle — `#!python {"__reactpy_event__": {"id": ...}}` — plus `#!python "type"`, the one plain value the client attaches because the server needs it to name the event and it is too cheap to be worth a round trip (`vdom.tsx`). Anything else the handler wants is fetched, per property, over the proxy messages described below.

That replaced the old `#!js event-to-object` package, which walked the event and its target: enumerable properties, plus `#!python value`, `#!python checked`, `#!python files`, `#!python type` and `#!python name` read off the element even though they are accessors, plus `#!python dataset`, plus every named control of a form on `#!python submit`. A single `#!html <input>` used to put the whole element on the wire — around ninety keys, of which a handler reads one. What goes over the wire for an event now is a handle and a type: on the order of a hundred and fifty bytes.

The consequence for you: the second element of `#!python data` is whatever the event was dispatched with, and the first is the handle — a dict of the marker and nothing but the id, never a copy of the event. Handlers are still free to take more than one argument — `#!js vdom.tsx` builds the list from the event plus any extra values the dispatch supplied — so index `#!python data` positionally rather than counting on a specific key surviving.

### Unpacking, and why the two handler forms differ

`Layout._process_event_queue` turns `#!python data` into arguments and calls the handler — but not the same way for both kinds of handler (`core/events.py`, `to_event_handler_function`):

```python linenums="0"
function(*data)   # a plain coroutine: the list is unpacked
function(data)    # an EventHandler: the list itself
```

So `#!python async def f(event)` receives the event when passed directly, while `#!python async def f(data)` must index into the list once wrapped in `#!python EventHandler`. Converting a working handler just to add `#!python prevent_default` breaks it in a way the traceback does not explain. Both forms are coroutines: `#!python EventHandler.__init__` and `#!python to_event_handler_function` each run the value through `check_is_async_handler`, so a sync function or a `#!python lambda` raises at element-build time. [Common Props](./common-props.md#event-handlers) shows both shapes side by side.

### The event proxy round trip

A handler which reads `#!python await event.target.value` makes the server ask the browser. `Layout.set_event_proxy_sender` wires the backend to the connection, and the request that goes down is one per property (`_event_proxy.py`):

```json linenums="0"
{
  "type": "event-proxy-request",
  "requestId": "f5a9b645f0a145e984b7c2d8e19f753c",
  "eventId": "lzk4q1-0",
  "path": ["target", "value"],
  "call": false,
  "args": [],
  "reply": true,
  "maxDepth": 10
}
```

The two ids come from different sides and mean different things. `#!python "requestId"` is a fresh `#!python uuid4().hex` per request, minted by the server so it can match the answer to whoever asked. `#!python "eventId"` is the client's own registry key for the object behind the handle — an opaque string such as `#!python "lzk4q1-0"` from `#!js EventProxyRegistry.register`, never a handler `#!python target` — so build it from the handle you were given and do not try to guess one.

The client answers with the value, or with a failure it can name:

```json linenums="0"
{
  "type": "event-proxy-response",
  "requestId": "f5a9b645f0a145e984b7c2d8e19f753c",
  "ok": true,
  "value": "typed text",
  "error": null,
  "code": null
}
```

Two requests raised in the same synchronous stretch — a batch via `#!python await event.read(...)`, or an `#!python asyncio.gather` of reads — are flushed together as `#!python {"type": "event-proxy-request", "requests": [ ... ]}` and answered the same way with a `#!python "responses"` array. Requests which genuinely depend on each other (`#!python await` one, then the next) cost one round trip each.

A client that never answers does not hang the handler. After `#!python REACTPY_EVENT_PROXY_TIMEOUT` seconds the read raises `EventProxyTimeout`. Strikes are counted by the connection's `#!python EventProxyBackend` — one backend per layout, so one per connection — and one unanswered message costs one strike however many properties it was asking for; after `#!python REACTPY_EVENT_PROXY_MAX_TIMEOUTS` consecutive unanswered round trips, live access is switched off for that connection and every later read raises `EventProxyUnavailable` at once rather than stalling. Binding a new sender — a reconnect — clears the strikes and gives the client another chance. `#!python REACTPY_EVENT_PROXY_MAX_DEPTH` bounds how deep a returned object is expanded. See [Configuring ReactPy](./reactpy.md#configuration).

The client is the one that decides what may be read. It refuses the members that would let a server reach outside the event — `#!python window`, `#!python document`, `#!python parentNode`, `#!python eval`, `#!python setTimeout`, and friends (`BLOCKED_MEMBERS` in `event-proxy.ts`) — and it also refuses `#!python __reactpy_event__`, `#!python __reactpy_ref__`, and anything matching `#!js /^on[a-z]/i`, so a handler cannot read the handle back off its own event or fish for another one. A refusal is an error on the response, not a value.

The client also decides how long an event stays readable, and it enforces that two different ways. An event which the server never once asked about is forgotten after `#!js LIVE_OBJECT_TTL_MS` (60 s); one the server *has* read is exempt, because the handler may simply be slow. What bounds the page overall is `#!js MAX_LIVE_OBJECTS` (512): past that, the event the server has gone longest without reading is dropped. Either way the id keeps working as an address and keeps explaining why it failed — `#!python "not-found"` for one that aged out unread, `#!python "evicted"` for one dropped to make room while this side was still reading it — which is the difference between `EventProxyNotFound` and `EventProxyEvicted`. An `#!python "evicted"` points at the page rather than at your handler.

Build a non-Python client from this page and you must implement both proxy message types as well, or every `#!python await` on an event raises. The stock client does, which is why a handler written against it works.

### The `target` string

`#!python "/0/0/0/1:onClick"` is two parts joined by a colon:

-   Before the colon, the element's **key path**: one segment per level, where each segment is that child's `#!python key` if it has one and its index otherwise (`core/layout.py`, `_get_children_info` and `_make_element_model_state`). Patch `#!python path`\ s, by contrast, are always positional (`.../children/<index>`). The two line up only while nobody sets a key — give a child `#!python {"key": "row-3"}` and its target segment becomes `#!python row-3` while its patch path stays `#!python children/2`.
-   After the colon, the attribute name the handler was declared under. It is whatever key you used, which is why `#!python {"onMyThing": f}` produces a target ending in `#!python :onMyThing`.

Treat the whole thing as an opaque handle. It is generated per render and is not meant to be constructed by hand; two structurally identical elements get distinct targets because their index paths differ.

!!! warning "Events for unmounted elements are dropped, not queued"

    If the server has no handler for a target — because the element was removed since the client last rendered, or the target was mistyped — the event is discarded with an informational log and the socket stays open:

    ```text linenums="0"
    Ignored event - handler '/99/99:nope' does not exist or its component unmounted
    ```

    ReactPy retries the lookup three times at 10 ms intervals first, to cover a handler that is briefly absent mid-render. That window is a race guard, not a queue: nothing is replayed later. A click that happens while the socket is down is held in a client-side send buffer and flushed if the connection reopens — but once `#!python REACTPY_RECONNECT_MAX_RETRIES` is exhausted the client stops trying, and everything buffered stays unsent.

### `seq` and typed input

Typing needs a protocol answer that a plain request/response does not give. Each keystroke sends an event carrying a counter the client incremented for that element. The server records the highest number it has finished handling, **per event name** for that target, and on the next render of an `#!html <input>`, `#!html <select>`, or `#!html <textarea>` stamps that whole mapping into the element's attributes under `_reactpy_ack_seq` — not one number for the element, because a single counter would let one event's progress stand in for another's (`core/layout.py`, `_inject_event_ack_seq`):

```json linenums="0"
{
  "type": "layout-update",
  "path": "/children/0/children/0",
  "model": {
    "tagName": "",
    "children": [
      {
        "tagName": "input",
        "attributes": {"value": "hello world", "_reactpy_ack_seq": {"onInput": 1}},
        "eventHandlers": {
          "onInput": {
            "target": "/0/0/0:onInput",
            "preventDefault": false,
            "stopPropagation": false
          }
        }
      }
    ]
  }
}
```

The client compares that number against its own counter to decide whether the server has caught up with the latest keystrokes. If the server is still behind, the client keeps what the user typed instead of overwriting the box with a stale `#!python value`. Without it, a slow handler erases text mid-word — the classic complaint about server-rendered inputs.

The value lives in a dedicated attribute rather than among your own so it cannot collide with, or leak into, a real DOM attribute. It is added only to those three tags, and only once at least one event has arrived for the element.

!!! note "Debounce and throttle do travel on the wire"

    They change *when* events leave the browser, not what is in them — but the layout still has to tell the client about them. `core/layout.py`, `_serialize_event_handler` copies both into the handler's model entry whenever they are not `#!python None`, and `#!js vdom.tsx` reads them back off that entry. `#!python @event(handler, debounce=250, throttle=500)` arrives as:

    ```json linenums="0"
    {
      "onClick": {
        "target": "/0:onClick",
        "preventDefault": false,
        "stopPropagation": false,
        "debounce": 250,
        "throttle": 500
      }
    }
    ```

    Both are omitted entirely when `#!python None`, which is what keeps the common case minimal. On arrival the client validates each with `#!js isValidDebounce` — finite, non-negative integer — and an invalid one is dropped with a `#!js console.warn` naming the handler rather than an error, leaving the handler live but un-debounced. Build a non-Python client from this page and you must carry these two fields; skipping them silently loses the throttling. See [Common Props](./common-props.md#reactpys-own-options).

    One further key may appear in that entry, and it is new with this release: `#!js "stopImmediatePropagation"`. It is a boolean like its two neighbours, but unlike `#!python preventDefault` and `#!python stopPropagation` — which are always sent — it is **omitted rather than sent as `#!python false`**: `_serialize_event_handler` in `core/layout.py` adds the key only when the handler asked for it, so read its absence as `#!python false`. `#!python @event(stop_immediate_propagation=True)`, or a detected `#!python event.stopImmediatePropagation()` in the handler's body, is what puts it there. The client then calls `#!js stopImmediatePropagation()` on the event before running the handler, so the other listeners on that same element are skipped too (`#!js vdom.tsx`).

---

## Watching it yourself

The protocol is plain JSON text frames, so an ordinary websocket client is a sufficient observer. Start this app:

=== "main.py"

    ```python
    {% include "../../examples/reference_protocol_structure/counter_app/main.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Then read the mount message, send a click, and read the patch:

=== "client.py"

    ```python
    {% include "../../examples/reference_protocol_structure/observe_protocol/client.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Both were run against each other, which is where the mount message, the `#!python target`, and the patch above come from. The counter's handler only calls a setter, so it never reads a property and the proxy messages never appear — the observer answers them, and gets nothing to answer, which is the "a read you never make costs nothing" rule from [Responding to Events](../learn/responding-to-events.md#the-event-object) showing up on the wire. The two proxy frames further up the page were captured from a handler which does read, against the same middleware. Nothing about the protocol is private to ReactPy's client — given a mount element and a correct `#!python target`, you can drive a server-rendered component from any language.

!!! danger "The server trusts the client completely"

    Nothing checks that `#!python target` names a real handler, that `#!python data` describes a real event, or that the sender is the page that mounted the component. Whatever your handler reads out of `#!python data`, it read because the browser asserted it. Treat it as user input: `#!python await event.target.value` is a string an attacker chose, at any length. The one thing which does not travel in the message at all is the ASGI scope: the server built that itself when the socket was accepted, which is why [Use Connection](./use-connection.md) and [User Scope](./use-scope.md) are the trusted side of the picture — even there, remember that the headers and peer address it reports are what the client chose to send.

    The proxy did not weaken this; it moved the trust question rather than answering it. `EventProxyBackend._route` takes `#!python "value"` from a response verbatim — no schema, no type check — so a crafted client can make any read return anything, including a `#!python list` where a `#!python str` was expected. And a `#!js call: true` request runs a method **in the page**, which is why the client, not the server, holds the veto: `BLOCKED_MEMBERS` and the `#!js /^on[a-z]/i` rule are the page's defence against a hostile *server*. Read that as what it is — the two sides do not trust each other, and only the page defends the page. Anything the client volunteers without being asked (`#!python "type"`) is the same kind of assertion as the rest of `#!python data`.

---

## Failure modes

| Symptom | Cause |
| --- | --- |
| Handshake refused, `#!python [ReactPy] Failed to connect!` | Missing trailing slash in `#!python componentPath`, or a `#!python path_prefix` that differs between the bootstrap and the server. |
| Socket opens then closes; server logs `#!python RuntimeError: Attempting to use an unregistered root component <path>.` | The dotted path is not in `#!python root_components`. The socket is accepted *before* the component is resolved, so the failure is visible only in the server log. |
| Server log: `#!python Unknown message type: <type>` | Anything other than `#!python "layout-event"` or `#!python "event-proxy-response"`. The server accepts those two and drops the rest, leaving the connection open. |
| Server log: `#!python Ignored event - handler ... does not exist or its component unmounted` | Stale or wrong `#!python target`. |
| Console: `#!python Received message without type` or `#!python Received message without handler` | A frame the client has no handler for. Ignored; the connection stays up. |
| A `#!html <pre>` with an exception message appears in the page | The component raised. See [Errors arrive as a model](#errors-arrive-as-a-model). |
| Component renders once and never updates | The handler never fires — usually a snake_case event name such as `#!python on_click`, so no event is ever sent. |
| `#!python [ReactPy] Disconnected!` then `#!python Reconnecting in …` | The socket dropped and backoff is in effect. If `#!python Connection max retries exhausted!` follows, the page needs a reload. |

---

## Related

-   [Common Props](./common-props.md) — the attribute names that become `#!python eventHandlers` and `#!python inlineJavaScript`.
-   [Usage](./usage.md) — writing the model by hand as a plain `#!python dict`.
-   [ReactPyMiddleware](./reactpy-middleware.md) — the paths the server claims, and the bootstrap that opens the socket.
-   [Use Connection](./use-connection.md) and [Use Location](./use-location.md) — the server-side view of the two query parameters.
