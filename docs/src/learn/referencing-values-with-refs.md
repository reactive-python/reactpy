## Overview

<p class="intro" markdown>

When you want a component to "remember" some information, but you don't want that information to [trigger new renders](./render-and-commit.md), you can use a _ref_.

</p>

!!! summary "You will learn"

    -   How to add a ref to your component
    -   How to update a ref's value
    -   How refs are different from state
    -   How to use refs safely

## Adding a ref to your component

You can add a ref to your component by importing the `use_ref` hook from ReactPy:

```python linenums="0"
from reactpy import use_ref
```

Inside your component, call the `use_ref` hook and pass the initial value that you want to reference as the only argument. For example, here is a ref to the value `#!python 0`:

```python linenums="0"
clicks = use_ref(0)
```

`use_ref` returns a `#!python Ref` object holding that value:

```python linenums="0"
Ref(0)  # holds the value you passed to use_ref
```

You can access the current value of that ref through the `#!python clicks.current` attribute. This value is intentionally mutable, meaning you can both read and write to it. It's like a secret pocket of your component that ReactPy doesn't track. (This is what makes it an "escape hatch" from ReactPy's one-way data flow — more on that below!)

Here, a button will increment `#!python clicks.current` on every click:

=== "app.py"

    ```python
    {% include "../../examples/referencing_values_with_refs/counter/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The ref points to a number, but, like [state](./state-a-components-memory.md), you could point to anything: a string, an object, or even a function. Unlike state, a ref is a plain Python object with a `#!python current` attribute that you can read and modify.

Note that **the component doesn't re-render with every increment.** Like state, refs are retained by ReactPy between re-renders. However, setting state re-renders a component. Changing a ref does not! Watch the server console: each click prints a new count, yet the page never redraws.

!!! tip "Pass the initial value"

    Unlike `#!python useRef()` in React, `#!python use_ref()` has no no-argument form — `#!python initial_value` is required, so `#!python use_ref()` fails outright with `#!python TypeError: use_ref() missing 1 required positional argument: 'initial_value'`. Pass `#!python None` explicitly when you have no better starting value: `#!python tick_task = use_ref(None)`.

    The lower-level `#!python reactpy.utils.Ref()` is the one that accepts no arguments, and there `#!python current` starts **unset** rather than at `#!python None`, so the first read raises `#!python AttributeError: 'Ref' object has no attribute 'current'`. Components should call `#!python use_ref` rather than construct a `#!python Ref` directly.

## Example: building a stopwatch

You can combine refs and state in a single component. For example, let's make a stopwatch that the user can start or stop by pressing a button. In order to display how much time has passed since the user pressed "Start", you will need to keep track of when the Start button was pressed and what the current time is. **This information is used for rendering, so you'll keep it in state:**

```python linenums="0"
elapsed, set_elapsed = use_state(0.0)
running, set_running = use_state(False)
```

When the user presses "Start", you'll update the elapsed time about ten times a second. ReactPy has no `setInterval`, but it runs on `asyncio`, so the equivalent is a coroutine that sleeps and sets state, started with [`use_async_effect`](../reference/use-async-effect.md).

Now the awkward part. That coroutine runs for a long time, and it needs to know *when* the user pressed Start in order to compute `time.monotonic() - <start>`. It cannot read it from a local variable, because the render that created the coroutine is long gone by the time the coroutine wakes up. **Since the start time is not used for rendering directly, you can keep it in a ref:**

=== "app.py"

    ```python
    {% include "../../examples/reference_use_ref/stopwatch/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Press Start and the counter climbs; press Stop and it freezes at the exact final value. The `#!python started_at` ref is the same object on every render, so the button handlers and the long-lived ticking coroutine all see whatever the others wrote into it.

Note what the ref is *not* doing here: it is not holding the `#!python asyncio.Task`. The ticking coroutine is owned by `#!python use_async_effect`, which cancels it when `#!python running` flips to `#!python False` and when the component unmounts. Storing a manually created task in a ref is tempting — `#!python tick_task.current = asyncio.create_task(keep_ticking())` — but nothing ever cancels it. Measure it by unmounting the component while it runs and the loop keeps rendering forever. Reach for an effect to own background work, and use the ref for the plain values the handlers need to share.

When a piece of information is used for rendering, keep it in state. When a piece of information is only needed by event handlers and changing it doesn't require a re-render, using a ref may be more efficient.

## Differences between refs and state

Perhaps you're thinking refs seem less "strict" than state — you can mutate them instead of always having to use a state setting function, for instance. But in most cases, you'll want to use state. Refs are an "escape hatch" you won't need often. Here's how state and refs compare:

| refs                                                                                       | state                                                                                                                    |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| `#!python use_ref(initial_value)` returns `#!python Ref(current=initial_value)`            | `#!python use_state(initial_value)` returns the current value of a state variable and a state setter function          |
| Doesn't trigger re-render when you change it.                                              | Triggers re-render when you change it.                                                                                   |
| Mutable — you can modify and update `#!python current` outside of the rendering process.   | "Immutable" — you must use the state setting function to modify state variables to queue a re-render.                   |
| You shouldn't read (or write) `#!python current` during rendering.                         | You can read state at any time. However, each render has its own [snapshot](./state-as-a-snapshot.md) of state which does not change. |

Here is a counter button that's implemented with state:

=== "app.py"

    ```python
    {% include "../../examples/referencing_values_with_refs/state_counter/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Because the `#!python count` value is displayed, it makes sense to use a state value for it. When the counter's value is set with `#!python set_count()`, ReactPy re-renders the component and the screen updates to reflect the new count.

If you tried to implement this with a ref, ReactPy would never re-render the component, so you'd never see the count change! See how clicking this button **does not update its text**:

=== "app.py"

    ```python
    {% include "../../examples/referencing_values_with_refs/ref_counter/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

This is why reading `#!python ref.current` during render leads to unreliable code. If you need that, use state instead.

### How does `use_ref` work inside?

Although both `use_state` and `use_ref` are provided by ReactPy, `use_ref` really is implemented _on top of_ `use_state`. In `reactpy/core/hooks.py`:

```python linenums="0"
def use_ref(initial_value):
    return _use_const(lambda: Ref(initial_value))


def _use_const(function):
    return HOOK_STACK.current_hook().use_state(function)
```

During the first render, `use_ref` stores a `#!python Ref` object as if it were state. That object is retained by ReactPy, so every later render gets the very same object back. There is no setter in the picture because `use_ref` always needs to return the same object — which is exactly why it can reuse state machinery without re-rendering.

If you're familiar with object-oriented programming, refs might remind you of instance fields — but instead of `#!python self.something` you write `#!python something.current`.

## When to use refs

Typically, you will use a ref when your component needs to "step outside" ReactPy and communicate with external APIs — often an API that won't impact the appearance of the component. Here are a few of these rare situations:

-   Storing [`asyncio` tasks](https://docs.python.org/3/library/asyncio-task.html#creating-tasks) or timer handles, as in the stopwatch above
-   Storing other objects that aren't needed to calculate the VDOM — a client, a cache, a handle from an external library

If your component needs to store some value, but it doesn't impact the rendering logic, choose refs.

!!! warning "A ref cannot hold a DOM node"

    React's docs list "accessing a DOM element" among the top reasons to reach for a ref. That one does not carry over: `reactpy.utils.Ref` is a plain Python box that lives on the server, and there is no attribute that hands a browser node to Python. What you do instead — give the element an `#!python "id"` and reach it from inline JavaScript — uses no ref at all. See [Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md) for why the name is a misnomer and what replaces each React example.

## Best practices for refs

Following these principles will make your components more predictable:

-   **Treat refs as an escape hatch.** Refs are useful when you work with external systems. If much of your application logic and data flow relies on refs, you might want to rethink your approach.
-   **Don't read or write `#!python ref.current` during rendering.** If some information is needed during rendering, use [state](./state-a-components-memory.md) instead. Since ReactPy doesn't know when `#!python ref.current` changes, even reading it while rendering makes your component's behavior difficult to predict. (The only exception to this is code like `#!python if not ref.current: ref.current = Thing()`, which only sets the ref once during the first render.)

Limitations of ReactPy state don't apply to refs. For example, state acts like a [snapshot for every render](./state-as-a-snapshot.md) and [doesn't update synchronously.](./queueing-a-series-of-state-updates.md) But when you mutate the current value of a ref, it changes immediately:

```python linenums="0"
clicks.current = 5
print(clicks.current)  # 5
```

This is because **the ref itself is a regular Python object,** and so it behaves like one.

You also don't need to worry about [avoiding mutation](./updating-objects-in-state.md) when you work with a ref. As long as the object you're mutating isn't used for rendering, ReactPy doesn't care what you do with the ref or its contents.

## Refs and the DOM

You can point a ref to any value — but not to a DOM element. ReactPy has no `#!python ref` attribute to pass to a tag, and no server-side handle on a browser node: `use_ref` lives in the Python process, the node lives in the page. The React idiom `#!python input_ref.current.focus()` therefore has no Python spelling at all. What replaces it is to give the element an `#!python "id"` and reach it from **inline JavaScript**, which runs in the page — and which uses no ref. The trap to avoid is reaching for it from an effect: effects run on the server too, where `#!python document` does not exist. [Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md) walks through focus, scrolling, and play/pause.

## Summary

-   A ref is a value that lets a component "remember" something without triggering a re-render.
-   Call `#!python use_ref(initial_value)` and read or write `#!python ref.current`.
-   Setting state re-renders; changing a ref does not, which makes refs suitable for values only event handlers need.
-   Don't read or write `#!python ref.current` during rendering — use state for anything that affects what's on screen.
