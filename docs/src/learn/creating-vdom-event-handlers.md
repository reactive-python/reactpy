## Overview

<p class="intro" markdown>

An event handler in ReactPy is any callable you put in an element's attribute dict. ReactPy inspects the value, not the name, decides what it is, and files it under one of three keys in the model. Most of the surprises on this page come from that one decision point: what counts as a handler, what counts as JavaScript, and what happens to the options you thought you set.

</p>

!!! summary "You will learn"

    -   The three buckets an attribute value lands in, and the rule that sorts them
    -   Why `#!python preventDefault()` sometimes reaches the browser and sometimes does not
    -   The difference in arguments between a plain callable and an `#!python EventHandler`
    -   How to set `#!python debounce` and `#!python throttle`, and what values are rejected

## The three buckets

When you call `#!python html.button({...}, ...)`, ReactPy walks the attribute dict once and routes every value by kind — `#!python callable` first, then string-under-`#!python onXxx`, then everything else (`core/vdom.py`, `separate_attributes_handlers_and_inline_javascript`):

=== "app.py"

    ```python
    {% include "../../examples/creating_vdom_event_handlers/three_buckets.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The rules, exactly:

| Value | Lands in | Note |
| --- | --- | --- |
| Anything `#!python callable` | `#!python eventHandlers` | **under any key name** |
| A `#!python BaseEventHandler` | `#!python eventHandlers` | stored as-is, untouched |
| A `#!python str` under a key matching `#!python ^on[A-Z]\w+` | `#!python inlineJavaScript` | `#!python eval`'d in the page |
| A `#!python reactpy.types.InlineJavaScript` string | `#!python inlineJavaScript` | under any key |
| Everything else | `#!python attributes` | forwarded verbatim |

Three of those rows have consequences worth spelling out.

**`#!python callable` wins over the key name.** `#!python {"notAnHandler": my_function}` registers a real listener whose target ends in `#!python :notAnHandler`. It will never fire, because no DOM event is named that, but it is registered. Conversely `#!python {"onClick": True}` is *not* a handler — a `#!python bool` is not callable, so it becomes an attribute and no listener exists. Neither mistake produces an error.

**`#!python None` is not a handler.** The classic `#!python {"onClick": handle_click()}` — calling instead of passing — yields `#!python {"attributes": {"onClick": None}}`. The button renders, looks dead, and logs nothing on either side. If a control "does nothing", check that you passed the function.

**A `#!python dict` is never a handler.** The React-style `#!python {"function": fn, "preventDefault": True}` becomes an ordinary attribute; no listener is attached. With `#!python REACTPY_DEBUG` on it fails loudly instead — `#!python TypeError: Object of type function is not JSON serializable` — which is the better outcome. Build handlers with `#!python @event` or `#!python EventHandler`, never with a dict.

## Plain callables, the shape you want most of the time

Pass a function and ReactPy wraps it. The browser sends a *list* of arguments; a plain callable receives it **unpacked positionally** (`core/events.py`, `to_event_handler_function`), which for a DOM event means one argument:

```python linenums="0"
def handle_click(event):
    print(event["target"]["value"])


html.button({"onClick": handle_click}, "Click me")
```

Sync functions, coroutine functions, and lambdas all work. Name the parameter whatever you like — the value is positional, and its type is `#!python reactpy.types.Event`, a `#!python dict` subclass with attribute access into nested dicts, so `#!python event["target"]["value"]` and `#!python event.target.value` are the same read. See [Responding to Events](./responding-to-events.md) for the payload surface and [Protocol Structure](../reference/protocol-structure.md) for what the client actually serializes.

!!! warning "Declare exactly one parameter"

    The list is unpacked onto your signature, so a handler declaring two required parameters fails at the moment of the click with `#!python TypeError: ... missing 1 required positional argument`, logged **server-side only** — the browser stays silent and the button just stops working. Extra context has to be bound in Python, usually with a `#!python lambda`:

    ```python linenums="0"
    html.button({"onClick": lambda event: delete(item.id)}, "Delete")
    ```

## `EventHandler`: the pre-built form, and its different argument

`#!python EventHandler` is what the `#!python @event` decorator returns, and you can construct it directly. Two things change when you do.

First, ReactPy stores an `#!python EventHandler` **as-is** rather than wrapping it, so the same object can serve every element that uses it. It does **not** follow that they share a `#!python target`. The target is derived per element: unless the handler carries an explicit `#!python target`, `core/layout.py` builds `#!python target = f"{key_path}:{event}"`, and `#!python @event` leaves `#!python target` as `#!python None`. Verified with one `#!python @event` handler on two buttons: the targets came out `#!python /0/0:onClick` and `#!python /0/1:onClick` — one function object, two targets.

Do not try to force the sharing by setting `#!python target=` yourself. Two elements registered under the same explicit target overwrite each other in the layout's handler table, and the unmount path then tries to `#!python del` that one key twice — verified, the second deletion raises `#!python KeyError` from `Layout._unmount_model_states`.

Second, and this is the trap: an `#!python EventHandler` receives the **list itself**, not the unpacked arguments.

=== "app.py"

    ```python
    {% include "../../examples/creating_vdom_event_handlers/argument_shape.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The failure when you get it backwards is `#!python TypeError: list indices must be integers or slices, not str` inside the handler — and the layout swallows it into a server-side `#!python Failed to execute event handler` line. Nothing appears in the browser console, so the UI merely stops responding. Prefer the plain-callable form unless you specifically need to hand-build a handler; `#!python @event` gives you the same options with the friendlier argument shape.

## Setting the four options

Four behaviours run in the browser *before* an event is sent. They are properties on the handler object, never attributes on the element:

| Option | Type | Effect |
| --- | --- | --- |
| `#!python prevent_default` | `#!python bool` | calls `#!python preventDefault()` in the page |
| `#!python stop_propagation` | `#!python bool` | calls `#!python stopPropagation()` in the page |
| `#!python debounce` | `#!python int` ms | rate-limits **server→client** `#!python value` updates on input elements |
| `#!python throttle` | `#!python int` ms | rate-limits **client→server** outgoing events |

There are two ways to set them, and the difference matters.

### Say it: `#!python @event`

```python linenums="0"
from reactpy import event


@event(prevent_default=True, stop_propagation=True, debounce=250, throttle=100)
async def handle_key_down(event_data): ...


html.input({"onKeyDown": handle_key_down})
```

This is explicit and it always works. Reach for it by default.

### Be discovered: bytecode inspection

ReactPy also reads your function's bytecode looking for three specific statements, so you can write them inline instead (`core/_event_inspect.py`, `inspect_event_handler`):

=== "app.py"

    ```python
    {% include "../../examples/creating_vdom_event_handlers/bytecode_detection.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

This is a source-parsing hack, not a runtime mechanism, and it has limits you should know before relying on it. Detection requires all of the following:

-   The call is written **literally in the handler's own body.** `#!python event.preventDefault()` inside a helper the handler calls is invisible to the inspector — it does not follow calls.
-   The **first parameter** is the event. The inspector reads `#!python co_varnames[0]` and matches against it.
-   For `#!python debounce`, the assigned value must be resolvable at inspect time: an integer literal, a compile-time-folded expression like `#!python 100 * 5`, a numeric **default** on a parameter (`#!python def h(event, ms=350)`), or a numeric closure cell. It cannot resolve a parameter with no default, a module-level global, or an arbitrary expression — all three inspect to `#!python None`. And it stops scanning at the **first** assignment it can settle — resolved or not — so with two assignments to `#!python event.debounce` the result depends on which one the bytecode reaches first. Verified: `#!python if event: event.debounce = 200 / else: event.debounce = len(x)` inspects to `#!python 200`, while the same branches written in the other order inspect to `#!python None`. Write one assignment and the question does not arise; with more than one, check the value you get.

The second rule produces the sharpest bug, so it deserves its own call-out:

!!! warning "Bound methods are not inspected correctly"

    For `#!python def on_submit(self, event)`, the first parameter is `#!python self`, so the inspector never matches the event variable and reports `#!python prevent_default=False`. The handler still *fires* — it is a perfectly good callable — but your `#!python event.preventDefault()` call is silently discarded:

    === "app.py"

        ```python
        {% include "../../examples/creating_vdom_event_handlers/bound_method_trap.py" start="# start" end="# end" %}
        ```

    === ":material-play: Run"

        ```python
        # TODO
        ```

    Attach a plain function defined inside the component instead, or pass `#!python @event(prevent_default=True)` explicitly over the method. `#!python functools.partial` is fine — the inspector unwraps `#!python .func` — and so is a `#!python functools.wraps` decorator, via `#!python __wrapped__`.

!!! warning "An inline-JavaScript handler cannot be inspected at all"

    Detection runs on Python bytecode. `#!python {"onClick": "this.innerText = 'x'"}` has none, so there is no `#!python preventDefault` equivalent in the string form. Call it yourself in the JavaScript: `#!python "event.preventDefault(); doThing()"`.

## Inline JavaScript

A `#!python str` under an `#!python onXxx` key is stored under `#!python inlineJavaScript` and `#!python eval`'d in the page; if it evaluates to a function, that function is called with the event:

```python linenums="0"
html.button({"onClick": '(event) => (event.target.innerText = "Thank you!")'}, "Click")
html.button({"onClick": "this.innerText = 'Thank you!'"}, "Click")
```

This is the way to touch the DOM from ReactPy, and the reason it exists is that the server has no node to hold ([Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md)). Keep each snippet to a single call, and never interpolate anything you did not write:

!!! danger "Trusted strings only"

    The string runs with your application's privileges, in the page. `#!python f"this.innerText = '{user_input}'"` is an injection point. Build strings from constants, or use a Python handler and pass data through state.

Note also that the pattern is `#!python ^on[A-Z]\w+` — a lowercase `#!python {"onclick": "..."}` matches nothing and becomes a plain attribute that never fires.

## Merging handlers

`#!python reactpy.core.events.merge_event_handlers` combines several handlers into one that runs them concurrently in a task group. It is public API but nothing in the installed package calls it — verified by grepping the whole `reactpy` package, which finds only its own definition — so you will rarely have a reason to call it. Its failure mode is still worth knowing, because it is a `#!python ValueError` at build time:

```python linenums="0"
merge_event_handlers([a, b])
# ValueError: Cannot merge handlers - 'stop_propagation', 'prevent_default',
# 'debounce', 'throttle' or 'target' mismatch.
```

Handlers merge only if every option matches. An empty list raises `#!python ValueError: No event handlers to merge`.

## What to check when a control does nothing

Every failure mode on this page is silent in the browser, so work through them in this order:

1.  **Did you pass the function or call it?** `#!python {"onClick": handler()}` gives `#!python None`, which becomes an inert attribute.
2.  **Is the key a real DOM event name in camelCase?** `#!python on_click` and `#!python onclick` never fire.
3.  **Does the handler take exactly one parameter?** Two required parameters means a server-side `#!python TypeError` and a dead button.
4.  **Is it a bound method?** Then `#!python preventDefault`/`#!python stopPropagation`/`#!python debounce` are not detected — use `#!python @event`.
5.  **Read the server log.** `#!python Failed to execute event handler` is where swallowed handler errors go; the browser console will show nothing.

## Summary

-   Values are sorted by kind, not name: `#!python callable` → `#!python eventHandlers`, string under `#!python onXxx` → `#!python inlineJavaScript`, everything else → `#!python attributes`.
-   `#!python None`, `#!python True`, and `#!python dict` handlers all fail silently as attributes.
-   A plain callable receives the argument list **unpacked** (so, the event dict); an `#!python EventHandler` receives the **list**.
-   Set options with `#!python @event(prevent_default=..., stop_propagation=..., debounce=..., throttle=...)`; the bytecode detector is a convenience with real limits, notably bound methods.
-   `#!python debounce` limits server→client value updates; `#!python throttle` limits client→server events. Invalid values are dropped with a console warning, not an error.
-   Handler errors surface in the server log only.

## Related

-   [Responding to Events](./responding-to-events.md) — the tutorial treatment, propagation, and the event object
-   [Common Props](../reference/common-props.md#event-handlers) — the same surface from the reference side, including ReactPy's own options
-   [Protocol Structure](../reference/protocol-structure.md) — the wire format, `#!python target`, and how `#!python data` is built
-   [Creating HTML Tags](./creating-html-tags.md) — how the model these handlers live in is built
-   [Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md) — the inline-JavaScript escape hatch
