## Overview

<p class="intro" markdown>

Setting a state variable will queue another render. But sometimes you might want to perform multiple operations on the value before queueing the next render. To do this, it helps to understand how ReactPy batches state updates.

</p>

!!! summary "You will learn"

    -   How ReactPy batches state updates
    -   Updating the same state multiple times before the next render
    -   What happens when you mix values and updater functions

## ReactPy batches state updates

You might expect that clicking the "+3" button will increment the counter three times, because it calls `#!python set_number(number + 1)` three times:

=== "app.py"

    ```python
    {% include "../../examples/queueing_a_series_of_state_updates/batched/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/queueing_a_series_of_state_updates/batched/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

It lands on `#!python 1`, not `#!python 3`. Two things combine to produce that.

First, as you may recall from [State as a Snapshot](./state-as-a-snapshot.md#rendering-takes-a-snapshot-in-time), each render's state values are fixed. Inside this render's event handler `#!python number` is always `#!python 0`, no matter how many times you call the setter, so all three lines evaluate to the same call:

```python linenums="0"
set_number(0 + 1)
set_number(0 + 1)
set_number(0 + 1)
```

Second, **ReactPy waits until _all_ code in a synchronous event handler has run before rendering.** The re-render happens only _after_ the handler returns, so the three assignments collapse into one render showing `#!python 1`.

This lets you update several state variables — even across several components — without triggering a render for each. It also avoids "half-finished" renders in which only some variables have been updated.

!!! warning "Batching stops at an `await`"

    The batching above is a side effect of a *synchronous* handler, and it is narrower than React's. ReactPy's setter applies its value to the hook's state immediately and merely flags the component for re-render (`core/hooks.py`, `_CurrentState.dispatch`), so an `#!python await` gives the scheduler a chance to render what has been set *so far*.

    Measured in a real browser, watching every value the counter takes after a single click:

    | Handler | Observed sequence |
    | --- | --- |
    | three `set_number(n => n + 1)` in a `def` | `0 → 3` (one render) |
    | the same, with `await asyncio.sleep(0.3)` between the calls | `0 → 1 → 2 → 3` (three renders) |

    React 18+ would batch both into a single render. In ReactPy, an `#!python async def` handler that awaits between updates renders — and repaints — in between. If that flicker matters, do the awaits first and set state once at the end, or collect the results and make a single setter call.

**ReactPy does not batch across _multiple_ intentional events like clicks** — each click is handled separately. This ensures that, for example, if the first click disables a form, the second click cannot submit it again.

## Updating the same state multiple times before the next render

It is an uncommon use case, but if you would like to update the same state variable multiple times before the next render, pass a _function_ that computes the next value from the previous one instead of the value itself: `#!python set_number(lambda n: n + 1)`. This is a way of saying "do something with the current state" rather than "replace the state".

=== "app.py"

    ```python
    {% include "../../examples/queueing_a_series_of_state_updates/updaters/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/queueing_a_series_of_state_updates/updaters/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

This time the counter reaches `#!python 3`, because each updater receives whatever the previous one produced.

### What happens if you update state after replacing it

What does this handler produce?

=== "app.py"

    ```python
    {% include "../../examples/queueing_a_series_of_state_updates/replace_then_update/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Step by step, starting from `#!python number == 0`:

1. `#!python set_number(number + 5)` — `#!python number` is `#!python 0`, so this is `#!python set_number(5)`. The state becomes `#!python 5`.
2. `#!python set_number(lambda n: n + 1)` — an updater, so it runs against the current value: `#!python 5 + 1`.

The next render shows `#!python 6`, confirmed by rendering the example.

!!! info "`set_number(5)` behaves like `set_number(lambda n: 5)`"

    A plain value ignores the argument entirely — it just replaces. That equivalence is what makes the next case surprising.

### What happens if you replace state after updating it

One more:

=== "app.py"

    ```python
    {% include "../../examples/queueing_a_series_of_state_updates/update_then_replace/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

1. `#!python set_number(number + 5)` — `#!python number` is `#!python 0`, so state becomes `#!python 5`.
2. `#!python set_number(lambda n: n + 1)` — updater, so `#!python 5 + 1 = 6`.
3. `#!python set_number(42)` — a plain value, so state becomes `#!python 42`.

The result is `#!python 42`. The two updaters still ran, and their work was then overwritten — which is the same answer React's queue produces, arrived at by a different route.

To summarize what you can pass to a state setter:

-   **An updater function** (e.g. `#!python lambda n: n + 1`) is applied to the current value.
-   **Any other value** (e.g. `#!python 5`) replaces the state outright, discarding whatever the updaters produced.

Updater functions run while your handler runs, so — like components — they must be **pure**. Don't set state from inside one or perform side effects there. Because they can run at any point, an updater that reads a variable from the enclosing render may see a stale value; take everything you need from the `#!python n` argument.

!!! warning "An updater that raises fails silently"

    Updaters run *eagerly*, inside the setter call itself (`core/hooks.py`, `_CurrentState.dispatch` calls `new(self.value)` before scheduling anything) — not later during rendering. Verified: an updater's side effect lands before the line after its `set_number(...)`.

    That has a nasty consequence. If an updater raises, the state is never assigned and no render is scheduled; ReactPy logs `Failed to execute event handler` on the server and **swallows** the error. The browser shows nothing, the console stays quiet, and the component simply stops responding to that button. Reproduced: a `lambda x: 1 / 0` updater produced a server-side traceback and then an indefinite absence of any render.

    Two habits follow: keep updaters to one pure expression, and when a counter "stops working" with no error in the browser, check the *server* log for `Failed to execute event handler`.

### Naming conventions

Name the updater's argument after the state variable it updates. Python has no single-letter convention as strong as JavaScript's, but the intent is the same — the argument is the *previous* value:

```python linenums="0"
set_enabled(lambda enabled: not enabled)
set_last_name(lambda last_name: last_name[::-1])
set_friend_count(lambda friend_count: friend_count * 2)
```

For clarity, prefer a descriptive name over `#!python n`: `#!python lambda previous: previous + 1` reads better in a handler that also does other work.

## Recap

-   Setting state does not change the variable in the existing render; it requests a new render.
-   ReactPy processes state updates after a synchronous event handler has finished. That is batching.
-   Batching does **not** survive an `#!python await` inside an `#!python async def` handler — each await can flush a render with partial updates.
-   To update the same state several times in one handler, use updater functions: `#!python set_number(lambda n: n + 1)`.
-   A plain value replaces the state and discards earlier updater results; an updater is applied to the current value.
-   Updater functions must be pure, and ReactPy will not check them for you.
