## Overview

<p class="intro" markdown>

ReactPy connects a Python process and a browser tab with one websocket. Everything crossing it is JSON, and nothing is pushed: the server sends rendered models, the client sends events, and a handler which wants to know something about the browser has to ask for it one property at a time. That constraint decides how every kind of data moves — values the server knows flow down as models, values the user produces flow up as events, and anything else needs a deliberate detour. This page is a map of those routes — what crosses, what cannot, and the honest workaround for each.

</p>

!!! summary "You will learn"

    -   Which channels actually exist, and the one direction that is not supported
    -   How to push a server-side value into a view without the client asking
    -   What an event actually gives your handler — including why file uploads do not work the way people expect
    -   How to get real file bytes across, and how to keep blocking code off the loop

## The channels that exist

| Direction | Mechanism | Your control |
| --- | --- | --- |
| server → client | the rendered model, sent as `#!python layout-update` patches | total — return it from the component |
| client → server | an event handler, receiving `#!python layout-event` | total — read `#!python event` |
| server → client, on demand | `#!python event-proxy-request` / `#!python event-proxy-response`, driven by `#!python await` on an event | indirect — you ask by awaiting, ReactPy frames the message |
| server → client, arbitrary message | **none** | not supported |
| shared mutable state | **none** | the two sides hold different objects |

The third row is new, and it is narrower than it looks: the request row exists because a handler *pulled*, on the back of an event the client chose to send. A read carries no application data and starts no conversation — see [Protocol Structure](../reference/protocol-structure.md#the-event-proxy-round-trip). Calling a method is the exception which proves the rule: `#!python await event.getCoalescedEvents()` ships your arguments down as JSON (`_event_proxy.py`, `_begin`), which is data travelling the direction the table says does not exist. Reads are the default; a call is a door you have to choose to open.

The server-to-client push row is the one people look for first, and its absence is a design choice, not an omission. A component's `#!python Connection` has no `#!python send`, no `#!python deliver`, no `#!python close` ([User Connection](../reference/use-connection.md)), and the backend is the only code allowed to write to the socket. That keeps the model the single source of truth: if a component could scribble on the wire, the client's tree and the server's model would drift apart with nothing to reconcile them.

!!! warning "A hand-written message is dropped by the client, silently"

    A custom backend *can* write anything to the socket, so it is tempting to invent a message type. Verified against a real browser: a `#!python {"type": "my-custom", ...}` frame arrives, and the client logs

    ```text linenums="0"
    [ReactPy] Received message without handler Object
    ```

    and discards it. The client dispatches on `#!python message.type` against a fixed registry — `#!python "layout-update"` is the only one registered by the mount path — and an unregistered type warns and returns. Nothing throws, the socket stays up, and the UI never changes. The page's only entry point is `mountReactPy`, and nothing in that path lets you register a handler of your own: `#!js onMessage` exists on the client classes, but a page built by `mountReactPy` never hands you the instance ([The client object](../reference/client-api.md#the-client-object)). Do not build on this path; use one of the routes below.

## Down: push a value the client never asked for

Anything you can `#!python await` on the server becomes a render, and a render reaches the client. An `#!python use_async_effect` that loops is the whole pattern:

=== "app.py"

    ```python
    {% include "../../examples/communicate_data_between_server_and_client/server_push/app.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```reactpy-run
    props: symbol="BTC"
    ```

Verified end to end: the first patch carried `#!python ["loading..."]`, and about a second later a second patch arrived with `#!python ["BTC: 42.10"]` — no client event in between. The client applied it like any other update.

Three things make or break this:

-   **Use `#!python use_async_effect`, not `#!python use_effect`.** An `#!python async def` passed to `#!python use_effect` raises `#!python TypeError: \`use_effect\` does not support async functions. Use \`use_async_effect\` instead.` Note where that error surfaces: `#!python use_effect` raises during the **render**, not inside the effect task, so you get a blank region — the model is `#!python {"tagName": "", "error": ""}` with debug off, and carries the `TypeError` text with `#!python REACTPY_DEBUG` on — and no `Error in effect` log line at all. That distinguishes it from a raising effect *body*, which is silent everywhere until unmount ([Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md#when-an-effect-fails-nothing-reports-it)).
-   **Loop and honour cancellation.** A long-lived effect is `#!python while True:` with `#!python except asyncio.CancelledError: break`. ReactPy cancels the task on unmount; `#!python shield=True` opts out if the work must finish.
-   **The dependency array is not React's.** Omitted means *inferred* from the closure's free variables, `#!python dependencies=[]` starts once, `#!python dependencies=None` restarts every render. Never omit the array expecting "run after every render". See [Use Async Effect](../reference/use-async-effect.md).

Polling is fine for a demo and wrong at scale. For real work, prefer a server-sent queue that the effect awaits — the effect suspends on `#!python await queue.get()` and the render happens the moment an item lands, with no timer at all.

## Up: read what the client sends

An event handler receives a live proxy onto the browser's event, not a copy of it. The client keeps the object and hands the server a handle; each `#!python await` on a property is a question asked of the page at that moment (`event-proxy.ts`, `serializeValue`). Nothing about the DOM event arrives unless you ask for it, which is the whole point: an `#!html <input>` used to arrive as the entire `#!python HTMLInputElement` — a measured `#!python onChange` payload carried roughly ninety keys, `#!python accept`, `#!python formAction`, `#!python validity`, and the rest — of which a handler reads `#!python value`.

What a read gives back is decided by the client. Plain data comes across as itself. A method comes back as a reference, so `await event.target.focus()` is a call the client makes rather than a function you receive. An object too deep, too large, or recursive comes back as a reference too, and you reach further with more `#!python await`s. Blocked members — `#!python window`, `#!python document`, `#!python parentNode`, `#!python eval`, `#!python setTimeout` — are refused outright, so a read cannot be used to walk out of the event and into the page.

**On `#!python submit`, the target is the form, and the thing you want is one level down.** `#!python HTMLFormControlsCollection` — what `#!python form.elements` holds — is iterable, and the client hands over anything iterable as a list (`serializeValue`), so `await event.target.elements` answers with one entry per control, named or not, each a plain dict of a hundred properties. The form itself is iterable too, so `await event.target` gives you the same controls; `#!python .elements` is just the name which says what you mean:

```python linenums="0"
async def handle_submit(event):
    event.preventDefault()
    controls = await event.target.elements  # list of control dicts
    payload = next(
        (c["value"] for c in controls if c.get("name") == "payload"), ""
    )
```

Note what makes that readable: the list arrives as data, so `c["value"]` is a plain subscript on the answer. The proxy itself is not subscriptable, but the JSON the client sent back is an ordinary `#!python list` of `#!python dict`s. The nested back-references inside each control (`#!python c["form"]`, which points at the form again) come through as references rather than copies. The full working example is in [Files](#files-what-actually-crosses-the-wire) below, and the wire format is in [Protocol Structure](../reference/protocol-structure.md).

Because each read is a round trip, how you write them costs time. Awaiting two properties one after another is two trips; `#!python await event.read("target.value", "key")` or an `#!python asyncio.gather` of them is one. A read you never make costs nothing at all.

## Files: what actually crosses the wire

A file input does not send file contents. It sends file **metadata**. Re-verified in Chrome against a real `#!html <input type="file">` — this is the entire `#!python files` entry that arrived for a 12-byte `#!python upload.txt`:

```python linenums="0"
[
    {
        "name": "upload.txt",
        "lastModified": 1792302335371,
        "lastModifiedDate": "2026-10-18T05:45:35.371Z",
        "webkitRelativePath": "",
        "size": 12,
        "type": "text/plain",
    }
]
```

No bytes. `#!python File` exposes its content through methods, and the client hands methods over as references rather than values, so there is nothing to read. There is no `#!python FormData` in the client and no chunked upload path. If you expected `#!python (await event.target.files)[0]["content"]`, it does not exist and never will from this mechanism.

### Reading real bytes

The route is: read the file **in the browser** with JavaScript, put the text into a normal form field, and let an ordinary submit carry it. This works — verified in Chrome, with a 12-character file arriving server-side as `#!python 'hello world\n'`:

=== "app.py"

    ```python
    {% include "../../examples/communicate_data_between_server_and_client/file_upload/app.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

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

    ```reactpy-run
    props: width=300
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

The mirror problem: something in the browser that Python cannot see. The proxy narrowed this considerably — anything reachable from the event object is now readable, so `#!python await event.target.scrollTop`, `#!python await event.target.className`, or a value a canvas put on its own element are ordinary awaits. What is still out of reach is anything the page will not hand over from that starting point: computed style of an element you never got an event from, `#!python localStorage`, geolocation, the clipboard. The client refuses the paths which would lead there anyway (`#!python window`, `#!python document`, `#!python localStorage`), so a handler cannot walk off the event and into the page — see [Protocol Structure](../reference/protocol-structure.md#the-event-proxy-round-trip).

Your options, in order of preference:

1.  **Move the computation server-side.** If the value depends only on data you already have, compute it in Python. Server-side rendering is the default for a reason.
2.  **Copy it into a form field and submit,** exactly as the file example does. Clunky, and it works.
3.  **Use the browser API in inline JavaScript** and let it act locally — copy to clipboard, request fullscreen, scroll. Keep it to one call, and never interpolate user input into the string.
4.  **Render the data yourself.** A chart is usually better as a server-built `#!html <svg>` or a generated image (`#!python reactpy.widgets.image`) than as JavaScript in the page.

There is no `#!python use_ref`-style handle to a DOM node, and `#!python {"ref": ...}` either vanishes or throws in the browser — see [Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md).

## Summary

-   Only two channels exist: the model down, events up. An arbitrary server→client message is logged as `#!python Received message without handler` and dropped.
-   Server push means `#!python use_async_effect` plus a state setter — loop, handle `#!python CancelledError`, and remember the dependency array infers by default.
-   Events are live proxies, not snapshots: each `#!python await` is a round trip to the browser, a read you never make costs nothing, and `#!python submit` hands back the form as a **list** of controls.
-   File inputs send metadata only, never bytes. Read the file in the browser, put the text in a named hidden input, and submit.
-   Use `#!python asyncio.to_thread` for blocking work. Calling a setter from a raw thread fails with `#!python no running event loop` and no visible symptom — marshal with `#!python call_soon_threadsafe`.
-   State never lives on the component function object; that is a leak across connections.

## Related

-   [Protocol Structure](../reference/protocol-structure.md) — the message types, `#!python target`, and `#!python seq`
-   [Use Async Effect](../reference/use-async-effect.md) and [Use Effect](../reference/use-effect.md) — the push mechanism, and its traps
-   [Creating VDOM Event Handlers](./creating-vdom-event-handlers.md) — payload shape, inline JavaScript, bytecode detection
-   [User Connection](../reference/use-connection.md) — the read-only connection view
-   [Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md) — client-only capabilities
-   [Creating Backends](./creating-backends.md) — where the socket actually lives
