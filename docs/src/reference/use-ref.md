## Overview

<p class="intro" markdown>

`use_ref` is a ReactPy hook that gives you a mutable box which survives re-renders. Writing to it never causes a render.

</p>

```python linenums="0"
value_box = use_ref(initial_value)
```

A ref is for values your component *uses* but never *renders*. It is a plain Python object holding one field, so reading and writing it is just attribute access — no setter, no scheduling, no re-render.

!!! warning "There is no DOM ref in ReactPy"
    React's `useRef` is often used to grab a DOM node — `inputRef.current.focus()`, `videoRef.current.play()`, `myDiv.current.scrollIntoView()`. That use **does not exist in ReactPy.** Your components run on the server, where there is no DOM, and ReactPy has no mechanism for handing a browser node to Python. There is no `ref_current` attribute, no callback ref, nothing to attach a node to. Anything you write as a `#!python "ref_..."` attribute is an unknown attribute the client silently ignores.

    Express browser behavior through state and ordinary attributes instead: `#!python {"autoFocus": True}`, `#!python {"value": text}`, `#!python {"disabled": not ready}`. If you need genuinely imperative browser code, that belongs in a [client-side app](./reactpy-csr.md), where your Python runs in the browser.

---

## Reference

### `use_ref(initial_value)` { #use-ref }

Call `use_ref` at the top level of your component to declare a value box.

```python linenums="0"
from reactpy import use_ref
```

#### Parameters

-   **`initial_value`**: The value the box starts with. It can be any Python value, including a mutable one.

#### Returns

A `reactpy.utils.Ref` object — the **same object** on every render of that component. It has two members:

-   **`current`**: The value. Read and write it directly: `#!python value_box.current = new_value`. Reading it does not schedule a render.
-   **`set_current(new_value)`**: Assigns `#!python current` and *returns the value it replaced*. Because it is a call rather than an assignment, it fits where a statement cannot go — inside a comprehension, or as part of a larger expression.

#### Caveats

-   **`initial_value` is evaluated on every render.** `#!python use_ref(build_something_expensive())` calls `build_something_expensive()` each time the component renders, then throws all but the first result away. Verified: four renders, four calls. To build something once, start empty and fill it in:

    ```python linenums="0"
    index = use_ref(None)
    if index.current is None:
        index.current = build_something_expensive()
    ```

-   **Writing to a ref never triggers a render.** That is the point, and also the trap: if the value is something the screen shows, it will not update. See [Ref versus state](#ref-versus-state).
-   **Mutating a ref does not invalidate anything.** Dependency comparison treats the box as unchanged no matter what you write into it, because it compares equal to itself. Listing a ref in a `dependencies` list is therefore useless — the effect or memo will never re-run because of it. Verified: an effect with `#!python dependencies=[box]` ran once while its `#!python box.current` was written to three times.
-   **A ref is unhashable.** `#!python hash(use_ref(0))` raises `TypeError`, so it cannot be a `#!python dict` key or a set member. Its `#!python ==` compares contents: two separate `#!python Ref(0)` boxes are equal.
-   **Render `#!python value_box.current`, not the box.** `#!python html.p(my_ref)` does not raise; it renders the repr, so the reader sees `#!python Ref(0)` on the page. Passing a ref as an attribute value fails at serialization instead.
-   Like every hook, call it **only at the top level** — never in a loop, a conditional, or after an early `#!python return`. ReactPy does not check: shuffling which hooks run between renders yields a scrambled component and a cryptic `IndexError`, not a helpful message.
-   ReactPy has **no Strict Mode**, so nothing runs your component twice to catch impure code. A ref written to *during rendering* is exactly as unsafe here as in React, and nothing will warn you. See [Keeping Components Pure](../learn/keeping-components-pure.md).

---

## Usage

### Ref versus state

The question is not "which is cheaper" but **who needs to know**. If changing the value must update the screen, it is state. If only the code needs it, it is a ref.

The two counters below start together and then drift apart, because only one of them causes a render. The ref counter's new value sits in the box unseen until something *else* renders the component.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_ref/no_rerender/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The usual split:

| You need...                                                | Use                                   |
| ---------------------------------------------------------- | ------------------------------------- |
| A value the UI renders                                     | `use_state`                           |
| A value only handlers or effects read                       | `use_ref`                             |
| A value that drives the UI *and* is written by a long-lived loop | Both: state for the UI, ref for the loop |
| Something built once, then read-only                        | `use_ref`, with the guard             |
| A mutable value the UI renders                              | `use_state` — replace the object instead of mutating it; see [Updating Objects in State](../learn/updating-objects-in-state.md) |

### Remembering a value built once

Because the box is the same object across renders, it is the natural place for something expensive to construct and cheap to read: a parsed file, an index, a client object. Start it empty so the expensive call is not repeated on every render.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_ref/expensive_object/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

If the value should be rebuilt when some input changes, a ref is the wrong tool — that is what a `dependencies` list is for. See `use_memo`.

### Sharing a value with a long-lived effect

An `use_async_effect` loop keeps running across renders, so it closes over the state values from the render that started it. A ref sidesteps this: it is the same object every render, so the loop reads whatever the handlers wrote *after* it started.

The stopwatch below keeps the start timestamp in a ref. The ticking effect reads it and the buttons write it, none of which needs a render of its own. The value the screen shows, `#!python elapsed`, is state.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_ref/stopwatch/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

### Writing where an expression is required

`#!python box.current = value` is an assignment, which is a statement, so it cannot appear where an expression is required — inside a comprehension, or as a value. `set_current` is the call-shaped form of the same write, and it hands back what you replaced.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_ref/set_current/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`pick` is a factory: it returns a fresh coroutine per button, so each button gets its own handler and the theme it belongs to is bound by the closure. `swap_back` is where `set_current` earns its place — `#!python set_theme(previous.set_current(theme))` exchanges the two in one expression, which an assignment could not do because an assignment is not a value. The re-render still comes from `set_theme`, not from the write to the ref.

---

## Troubleshooting

### My ref value is stale

Check which of these you did:

-   **You rendered the box, not its contents.** `#!python html.p(my_ref)` prints `#!python Ref(...)`. Use `#!python my_ref.current`.
-   **You expected the write to re-render.** A ref never schedules a render. If the screen must change, that value is state.
-   **You listed the ref as a dependency.** Mutating `#!python current` does not invalidate effects or memos — the box always compares equal to itself. Put the *value* in the dependency list, or use state.
-   **You read a ref through an old closure.** Inside a long-lived effect, re-read `#!python box.current` on each pass instead of binding it to a local once.

### My expensive setup runs on every render

You passed it as the argument: `#!python use_ref(build())` calls `build()` every render. Move it behind a guard:

```python linenums="0"
box = use_ref(None)
if box.current is None:
    box.current = build()
```

### I need to focus an input, or scroll to an element

There is no way to do this from a ReactPy server component, and no `#!python "ref_current"` attribute will add one. Use the declarative attributes the browser already understands — `#!python "autoFocus"`, `#!python "checked"`, `#!python "value"`, `#!python "disabled"` — and reach for a [client-side app](./reactpy-csr.md) if you truly need imperative browser access.
