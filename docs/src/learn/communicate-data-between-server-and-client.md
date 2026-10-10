## Overview

<p class="intro" markdown>

ReactPy connects a Python process and a browser tab with one websocket and one message type in each direction. That single constraint decides how every kind of data moves between the two: values the server knows flow down as rendered models, values the user produces flow up as event payloads, and anything else needs a deliberate detour. This page is a map of those routes — what crosses, what cannot, and the honest workaround for each.

</p>

!!! summary "You will learn"

    -   Which channels actually exist, and the one direction that is not supported
    -   How to push a server-side value into a view without the client asking
    -   What an event payload really contains — including why file uploads do not work the way people expect
    -   How to get real file bytes across, and how to keep blocking code off the loop

## The channels that exist

| Direction | Mechanism | Your control |
| --- | --- | --- |
| server → client | the rendered model, sent as `#!python layout-update` patches | total — return it from the component |
| client → server | an event handler, receiving `#!python layout-event` | total — read `#!python event` |
| server → client, arbitrary message | **none** | not supported |
| shared mutable state | **none** | the two sides hold different objects |

The server-to-client push row is the one people look for first, and its absence is a design choice, not an omission. A component's `#!python Connection` has no `#!python send`, no `#!python deliver`, no `#!python close` ([User Connection](../reference/use-connection.md)), and the backend is the only code allowed to write to the socket. That keeps the model the single source of truth: if a component could scribble on the wire, the client's tree and the server's model would drift apart with nothing to reconcile them.

!!! warning "A hand-written message is dropped by the client, silently"

    A custom backend *can* write anything to the socket, so it is tempting to invent a message type. Verified against a real browser: a `#!python {"type": "my-custom", ...}` frame arrives, and the client logs

    ```text linenums="0"
    [ReactPy] Received message without handler Object
    ```

    and discards it. The client dispatches on `#!python message.type` against a fixed registry — `#!python "layout-update"` is the only one registered by the mount path — and an unregistered type warns and returns. Nothing throws, the socket stays up, and the UI never changes. The client bundle exports exactly one function and offers no `#!js onMessage` hook to register against, so there is no supported way to add a handler. Do not build on this path; use one of the routes below.

## Down: push a value the client never asked for

Anything you can `#!python await` on the server becomes a render, and a render reaches the client. An `#!python use_async_effect` that loops is the whole pattern:

=== "app.py"

    ```python
    {% include "../../examples/communicate_data_between_server_and_client/server_push/app.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified end to end: the first patch carried `#!python ["loading..."]`, and about a second later a second patch arrived with `#!python ["BTC: 42.10"]` — no client event in between. The client applied it like any other update.

Three things make or break this:

-   **Use `#!python use_async_effect`, not `#!python use_effect`.** An `#!python async def` passed to `#!python use_effect` raises `#!python TypeError: \`use_effect\` does not support async functions. Use \`use_async_effect\` instead.` The effect takes **zero arguments** — the `#!python async def effect(stop)` shape from 1.x no longer works. Note where that error surfaces: `#!python use_effect` raises during the **render**, not inside the effect task, so you get a blank region — the model is `#!python {"tagName": "", "error": ""}` with debug off, and carries the `TypeError` text with `#!python REACTPY_DEBUG` on — and no `Error in effect` log line at all. That distinguishes it from a raising effect *body*, which is silent everywhere until unmount ([Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md#when-an-effect-fails-nothing-reports-it)).
-   **Loop and honour cancellation.** A long-lived effect is `#!python while True:` with `#!python except asyncio.CancelledError: break`. ReactPy cancels the task on unmount; `#!python shield=True` opts out if the work must finish.
-   **The dependency array is not React's.** Omitted means *inferred* from the closure's free variables, `#!python dependencies=[]` starts once, `#!python dependencies=None` restarts every render. Never omit the array expecting "run after every render". See [Use Async Effect](../reference/use-async-effect.md).

Polling is fine for a demo and wrong at scale. For real work, prefer a server-sent queue that the effect awaits — the effect suspends on `#!python await queue.get()` and the render happens the moment an item lands, with no timer at all.

## Up: read what the client sends

An event handler receives a `#!python dict`, not a live event — the browser serialized it and your code is now on the other side of a network boundary. The client walks the target and copies enumerable properties, plus `#!python value`, `#!python checked`, `#!python files`, `#!python type`, `#!python name` read off the element even though they are accessors, plus `#!python dataset`, plus — on `#!python submit` — the form's named controls. Functions, DOM nodes, and cycles are skipped rather than raising.

Two consequences to internalize:

**An `#!html <input>` arrives as the whole element.** A measured `#!python onChange` payload carried roughly ninety keys — `#!python accept`, `#!python formAction`, `#!python validity`, `#!python validationMessage`, and the rest of `#!python HTMLInputElement` — of which you read `#!python value`. Index what you need; do not count on a specific key surviving, and do not iterate the payload assuming it is small.

**On `#!python submit`, `#!python event["target"]` is a *list*, not a dict.** The named controls are serialized as list entries, so the read shape differs from every other event:

```python linenums="0"
def handle_submit(event):
    event.preventDefault()
    controls = event["target"]  # list of control dicts
    payload = next((c["value"] for c in controls if c.get("name") == "payload"), "")
```

This is verified: submitting a form with a hidden `#!python name="payload"` input produced `[{"name": "", "type": "file", ...}, {"name": "payload", "type": "hidden", "value": "hello world\n"}, {"name": "", "type": "submit", ...}]`. The full working example is in [Files](#files-what-actually-crosses-the-wire) below. The protocol behind this is documented in [Protocol Structure](../reference/protocol-structure.md).

## Files: what actually crosses the wire

A file input does not send file contents. It sends file **metadata**. Verified with a real file chooser against a real browser — this is the entire `#!python files` entry that arrived:

```python linenums="0"
{
    "name": "upload.txt",
    "lastModified": 1791523914968,
    "lastModifiedDate": {},
    "webkitRelativePath": "",
    "type": "text/plain",
}
```

No bytes. `#!python File` exposes its content through methods, which are functions, and functions are skipped by the walk. There is no `#!python FormData` in the client and no chunked upload path. If you expected `#!python event["target"]["files"][0]["content"]`, it does not exist and never will from this mechanism.

### Reading real bytes

The route is: read the file **in the browser** with JavaScript, put the text into a normal form field, and let an ordinary submit carry it. This works — verified in Chrome, with a 12-character file arriving server-side as `#!python 'hello world\n'`:

=== "app.py"

    ```python
    {% include "../../examples/communicate_data_between_server_and_client/file_upload/app.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The mechanics, each of which matters:

-   The `#!python onChange` value is a **string**, which routes it to `#!python inlineJavaScript` instead of `#!python eventHandlers` — that is what makes it run in the page ([Creating VDOM Event Handlers](./creating-vdom-event-handlers.md#inline-javascript)).
-   `#!python file.text()` returns a promise, so the assignment happens in a callback — which is why a **submit button** is required. Sending immediately from the change handler races the promise and ships an empty string.
-   The hidden input needs both `#!python id` (for the JavaScript to find it) and `#!python name` (for the form walk to include it).
-   `#!python event.preventDefault()` must appear **literally in the handler's body**. ReactPy detects it by bytecode inspection; calling a helper that calls it is not detected, and the page navigates away. See the bound-method caveat in [Creating VDOM Event Handlers](./creating-vdom-event-handlers.md#be-discovered-bytecode-inspection).

!!! danger "Untrusted content and `#!python eval`"

    The inline-JavaScript string is `#!python eval`'d. Build it from constants only — `#!python f"...{user_input}..."` is an injection point. And anything you read off a user's file is untrusted data: cap the size before you buffer it, and never render it back without escaping.

Binary uploads work the same way via `#!python file.arrayBuffer()` plus base64, but base64 costs a third of your bandwidth on top of a JSON string over a socket. For anything large, upload to a normal HTTP endpoint and pass the resulting id through state instead.

## Blocking code and other threads

Everything a component does runs on the connection's event loop. A synchronous, CPU-bound call inside a render or an effect freezes that connection — and the handlers on it. Move blocking work with `#!python asyncio.to_thread`:

=== "app.py"

    ```python
    {% include "../../examples/communicate_data_between_server_and_client/thread_bridge/app.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified: the first patch says `#!python rendering...`, the next says `#!python rendered 300px`, and the loop stayed responsive across the 0.4 s call. Note that the setter is called from inside the effect, which is already on the loop.

!!! warning "Calling a state setter from another thread loses the update"

    Handing `#!python set_value` to a raw `#!python threading.Thread` is the natural mistake, and it fails with no user-visible symptom. Verified — the setter raises on the worker thread, and no render ever arrives:

    ```text linenums="0"
    Failed to schedule render via <function _make_life_cycle_state.<locals>.<lambda> ...>
    RuntimeError: no running event loop
    RuntimeWarning: coroutine 'Layout._create_layout_update' was never awaited
    ```

    Nothing appears in the browser console; the component simply never updates. The fix is to capture the loop while you are on it and marshal back:

    ```python linenums="0"
    loop = asyncio.get_running_loop()  # inside the component, on the loop

    def deliver_from_thread(value):
        loop.call_soon_threadsafe(set_value, value)
    ```

    Verified working — the update arrived as a normal patch. Prefer `#!python asyncio.to_thread` when you can, since it removes the bookkeeping entirely.

!!! warning "Do not hang state on the component function"

    `#!python my_component.started = True` as a run-once guard looks harmless and is a cross-user leak: the function object is module-scope, so the first visitor flips it for everyone. Give the component a prop, key the child, or guard with `#!python use_ref`. The general version of this is in [VDOM Mutations](./vdom-mutations.md#case-2-the-mutation-escapes-to-other-users).

## Client-only data

The mirror problem: something in the browser that Python cannot see. Computed style, scroll position, canvas pixels, `#!python localStorage`, geolocation, the clipboard — none of it is in the payload, because the walk copies data properties and skips everything callable.

Your options, in order of preference:

1.  **Move the computation server-side.** If the value depends only on data you already have, compute it in Python. Server-side rendering is the default for a reason.
2.  **Copy it into a form field and submit,** exactly as the file example does. Clunky, and it works.
3.  **Use the browser API in inline JavaScript** and let it act locally — copy to clipboard, request fullscreen, scroll. Keep it to one call, and never interpolate user input into the string.
4.  **Render the data yourself.** A chart is usually better as a server-built `#!html <svg>` or a generated image (`#!python reactpy.widgets.image`) than as JavaScript in the page.

There is no `#!python use_ref`-style handle to a DOM node, and `#!python {"ref": ...}` either vanishes or throws in the browser — see [Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md).

## Summary

-   Only two channels exist: the model down, events up. An arbitrary server→client message is logged as `#!python Received message without handler` and dropped.
-   Server push means `#!python use_async_effect` plus a state setter — loop, handle `#!python CancelledError`, and remember the dependency array infers by default.
-   Event payloads are serialized snapshots: an input arrives as the whole `#!python HTMLInputElement`, and `#!python submit` gives you a **list** of named controls.
-   File inputs send metadata only, never bytes. Read the file in the browser, put the text in a named hidden input, and submit.
-   Use `#!python asyncio.to_thread` for blocking work. Calling a setter from a raw thread fails with `#!python no running event loop` and no visible symptom — marshal with `#!python call_soon_threadsafe`.
-   State never lives on the component function object; that is a leak across connections.

## Related

-   [Protocol Structure](../reference/protocol-structure.md) — both message types, `#!python target`, and `#!python seq`
-   [Use Async Effect](../reference/use-async-effect.md) and [Use Effect](../reference/use-effect.md) — the push mechanism, and its traps
-   [Creating VDOM Event Handlers](./creating-vdom-event-handlers.md) — payload shape, inline JavaScript, bytecode detection
-   [User Connection](../reference/use-connection.md) — the read-only connection view
-   [Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md) — client-only capabilities
-   [Creating Backends](./creating-backends.md) — where the socket actually lives
