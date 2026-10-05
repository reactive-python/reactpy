## Overview

<p class="intro" markdown>

ReactPy renders on the server and paints in the browser. A single websocket carries two message types: the server sends `#!python "layout-update"` patches, the client sends `#!python "layout-event"` interactions.

</p>

```text linenums="0"
server --{"type": "layout-update", "path": ..., "model": ...}-->  client
server <--{"type": "layout-event", "target": ..., "data": [...]}--  client
```

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

The model is JSON, not a `#!python VdomDict`. Six key names are legal (`core/vdom.py`, `VDOM_JSON_SCHEMA`), and only `#!python tagName` is required:

| Key | Value | Notes |
| --- | --- | --- |
| `#!python "tagName"` | `#!python str` | The DOM tag, or `#!python ""` for a wrapper element. |
| `#!python "children"` | `#!python list` | Nested models or plain strings. |
| `#!python "attributes"` | `#!python dict` | Forwarded to the DOM verbatim. Includes `#!python key`. |
| `#!python "eventHandlers"` | `#!python dict` | Handler name to target spec, described below. |
| `#!python "inlineJavaScript"` | `#!python dict` | Handler name to JavaScript source string. |
| `#!python "importSource"` | `#!python dict` | Marks an element as coming from a JavaScript module. |

Any other key name is rejected while the element is being built:

```text linenums="0"
ValueError: Invalid keys: {'bogus'}.
```

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
| `#!python "data"` | `#!python list` | The arguments for the handler. Usually one event dict. |
| `#!python "seq"` | `#!python int` | Optional. A client-assigned counter, per element. |

A real click on the button above:

```json linenums="0"
{
  "type": "layout-event",
  "target": "/0/0/0/1:onClick",
  "data": [{"type": "click", "target": {"tagName": "BUTTON"}}],
  "seq": 1
}
```

### How `data` is built

The browser serializes the DOM event by walking it: enumerable properties, plus `#!python value`, `#!python checked`, `#!python files`, `#!python type` and `#!python name` read off the element even though they are accessors, plus `#!python dataset`, plus every named control of a form on `#!python submit`. Functions, DOM nodes, and anything else unserializable are skipped; a cycle or an object nested too deep is cut rather than raising.

That is why the handler receives a `#!python dict` and not a live event, and why it cannot call into the page. It also means the contents depend on what the walk happened to reach: an `#!html <input>` arrives as the whole element, hundreds of fields of which you read one. Index `#!python data` positionally rather than counting on a specific key surviving.

### Unpacking, and why the two handler forms differ

`Layout._process_event_queue` turns `#!python data` into arguments and calls the handler — but not the same way for both kinds of handler (`core/events.py`, `to_event_handler_function`):

```python linenums="0"
function(*data)   # a plain callable: the list is unpacked
function(data)    # an EventHandler: the list itself
```

So `#!python def f(event)` receives the event dict when passed directly, while `#!python def f(data)` must index into the list once wrapped in `#!python EventHandler`. Converting a working handler just to add `#!python prevent_default` breaks it in a way the traceback does not explain. [Common Props](./common-props.md#event-handlers) shows both shapes side by side.

### The `target` string

`#!python "/0/0/0/1:onClick"` is two parts joined by a colon:

-   Before the colon, the element's position: child index, then child index, walking down from the root. It indexes the same tree the patch `#!python path` does, so the two line up.
-   After the colon, the attribute name the handler was declared under. It is whatever key you used, which is why `#!python {"onMyThing": f}` produces a target ending in `#!python :onMyThing`.

Treat the whole thing as an opaque handle. It is generated per render and is not meant to be constructed by hand; two structurally identical elements get distinct targets because their index paths differ.

!!! warning "Events for unmounted elements are dropped, not queued"

    If the server has no handler for a target — because the element was removed since the client last rendered, or the target was mistyped — the event is discarded with an informational log and the socket stays open:

    ```text linenums="0"
    Ignored event - handler '/99/99:nope' does not exist or its component unmounted
    ```

    ReactPy retries the lookup three times at 10 ms intervals first, to cover a handler that is briefly absent mid-render. That window is a race guard, not a queue: nothing is replayed later. A click that happens while the socket is down is held in a client-side send buffer and flushed if the connection reopens — but once `#!python REACTPY_RECONNECT_MAX_RETRIES` is exhausted the client stops trying, and everything buffered stays unsent.

### `seq` and typed input

Typing needs a protocol answer that a plain request/response does not give. Each keystroke sends an event carrying a counter the client incremented for that element. The server records the highest number seen per target, and on the next render of an `#!html <input>`, `#!html <select>`, or `#!html <textarea>` stamps the largest one into the element's attributes under `_reactpy_ack_seq`:

```json linenums="0"
{
  "type": "layout-update",
  "path": "/children/0/children/0",
  "model": {
    "tagName": "",
    "children": [
      {
        "tagName": "input",
        "attributes": {"value": "hello world", "_reactpy_ack_seq": 1},
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

!!! note "Debounce and throttle never reach the wire"

    They change when events leave the browser, not what is in them. Both are applied client-side before the message is built, and an invalid value is dropped with a console warning rather than an error. See [Common Props](./common-props.md#reactpys-own-options).

---

## Watching it yourself

The protocol is plain JSON text frames, so an ordinary websocket client is a sufficient observer. Start this app:

=== "app.py"

    ```python
    {% include "../../examples/reference_protocol_structure/counter_app/app.py" start="# start" %}
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

Both were run against each other to produce every JSON block on this page. Nothing about the protocol is private to ReactPy's client — given a mount element and a correct `#!python target`, you can drive a server-rendered component from any language.

!!! danger "The server trusts the client completely"

    Nothing checks that `#!python target` names a real handler, that `#!python data` describes a real event, or that the sender is the page that mounted the component. Whatever your handler reads out of `#!python data`, it read because the browser asserted it. Treat it as user input: `#!python event["target"]["value"]` is a string an attacker chose, at any length. The one thing the client cannot forge is the ASGI scope, which is server-side — see [Use Connection](./use-connection.md).

---

## Failure modes

| Symptom | Cause |
| --- | --- |
| Handshake refused, `#!python [ReactPy] Failed to connect!` | Missing trailing slash in `#!python componentPath`, or a `#!python path_prefix` that differs between the bootstrap and the server. |
| Socket opens then closes; server logs `#!python RuntimeError: Attempting to use an unregistered root component <path>.` | The dotted path is not in `#!python root_components`. The socket is accepted *before* the component is resolved, so the failure is visible only in the server log. |
| Server log: `#!python Unknown message type: <type>` | Anything other than `#!python "layout-event"`. The server accepts that one type and drops the rest, leaving the connection open. |
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
