## Overview

<p class="intro" markdown>

`use_reducer` is a ReactPy hook that holds state behind a function: you send an action, and a reducer turns the current state plus that action into the next state.

</p>

```python linenums="0"
state, dispatch = use_reducer(reducer, initial_value)
```

Reach for it when a component's updates are more than "set this to that" — several fields that change together, transitions that depend on what is already there, or update logic you want out of the component so it can be tested as a plain function.

---

## Reference

### `use_reducer(reducer, initial_value)` { #use-reducer }

Call `use_reducer` at the top level of your component.

```python linenums="0"
from reactpy import use_reducer
```

#### Parameters

-   **`reducer`**: `#!python (state, action) -> new_state`. A pure function: given the same two arguments it returns the same result, and it does not touch anything outside them. It must return a **new** object rather than modifying `#!python state` — see [the reducer must not mutate](#the-reducer-must-not-mutate).
-   **`initial_value`**: The state to start with. Pass a **function taking no arguments** to build it lazily; ReactPy calls it on the first render only. See [avoiding recreating the initial state](#avoiding-recreating-the-initial-state).

#### Returns

A two-item tuple, normally unpacked:

-   **`state`**: The current state, as of the start of this render.
-   **`dispatch`**: A function that takes an action and schedules the update. The **same object** on every render — verified, one dispatcher across four renders — so it is safe to pass into a child or a dependency list.

#### Caveats

-   **Define the reducer at module level.** ReactPy builds the dispatcher once, on the first render, and the dispatcher closes over the reducer you passed *then*. A reducer defined inside the component is a new function object each render and ReactPy keeps using the first one, so any value it closes over is frozen at its first-render value. Measured: four renders, four distinct reducer objects passed in, and the state kept reporting `#!python seen_n=0`. **This differs from React**, which re-reads the reducer every render. Anything the reducer needs must arrive in `#!python state` or `#!python action`. See [The reducer never changes](#the-reducer-never-changes).
-   **`use_reducer` is `use_state` underneath.** The dispatcher calls the state setter with `#!python lambda last_state: reducer(last_state, action)`, so every rule from [`use_state`](./use-state.md) applies here — replaced, never merged; equal values schedule no render; mutations vanish silently. See [The reducer must not mutate](#the-reducer-must-not-mutate).
-   **The reducer runs eagerly, inside `dispatch`** — not later during the render. Verified by ordering statements around the call. A reducer that raises is swallowed the same way any event-handler error is: logged on the server as `Failed to execute event handler`, with nothing in the browser console.
-   **Actions are yours; ReactPy never inspects them.** A `#!python dict` with a `#!python "type"` key is convention, not a requirement — you can dispatch a string, a number, or a tuple.
-   Like every hook, call it **only at the top level** — never in a loop, a conditional, or after an early `#!python return`. ReactPy does not check; a hook that runs on some renders but not others produces a scrambled component and a cryptic `IndexError`.

---

## Usage

### Managing complex state with a reducer

One reducer holds the whole shape, and each behaviour is a branch chosen by the action. Because it is an ordinary function of two arguments, you can test it without rendering anything.

Press **Add task** twice, **task 1**, then **Clear done**, and watch the reducer's branches run:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_reducer/todos/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Three things to notice in `#!python todos_reducer`. It is at module level, so the closure trap above never arises. Every branch builds a new dict with `#!python {**state, ...}` — none of them mutate. And the fallback `#!python return state` makes an unhandled action a deliberate no-op rather than a crash.

### The reducer must not mutate

This is the failure mode most likely to cost you an afternoon, and it is silent. A reducer that modifies `#!python state` and returns it hands back the very object ReactPy already holds; the comparison finds them equal and schedules nothing. No error, no warning, nothing in the console — the button just stops working while your data quietly changes underneath.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_reducer/replace_not_mutate/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Return `#!python {**state, "count": state["count"] + 1}`, not `#!python state["count"] += 1; return state`. The same applies one level down: `#!python {**state, "items": state["items"] + [new]}`, never `#!python state["items"].append(new)`. See [Updating Objects in State](../learn/updating-objects-in-state.md) and [Updating Arrays in State](../learn/updating-arrays-in-state.md).

### The reducer never changes

Because the first reducer is the only one that ever runs, a reducer that closes over component state reads a value frozen at the first render — permanently, with no warning.

Run this, press **Add step** twice, then **Bump step**, then **Add step** again:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_reducer/stale_reducer/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`#!python step` goes to 2 on screen, but the total keeps rising by 1. The reducer still holds the `#!python step` from the render that created it. Two ways out: keep the reducer at module level and put `#!python step` in the state, or send it in the action — `#!python dispatch({"type": "add", "amount": step})`.

### Avoiding recreating the initial state

Pass a function and ReactPy calls it once; pass a call and it runs on every render, with every result but the first discarded. Measured across four renders: 1 call versus 4. The counter on screen reports the total, and it stays at 1 no matter what you press.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_reducer/expensive_init/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

---

## `use_reducer` or `use_state`?

Prefer `#!python use_state`. It is shorter and there is no reducer-closure rule to remember. Switch when one of these is true:

-   Several pieces of state always change together, and updating them through separate setters lets the component render in between with an inconsistent mix.
-   The next state depends on the current one in a way you keep writing wrong.
-   The update logic has grown branches you want to name, or unit-test as a plain function.
-   Different parts of a tree need to trigger the same transitions — passing `#!python dispatch` around is tidier than passing several setters.

---

## Troubleshooting

### My dispatch does nothing

Check the reducer's return value first — this is almost always a mutation. `#!python return state` after modifying `#!python state` schedules nothing. Also check for a branch that returns the state unchanged: an action whose `#!python "type"` no branch matches falls through to your `#!python return state`, which is correctly a no-op.

### My reducer sees an old value of some state

You defined it inside the component, so ReactPy is running the first-render version with the first-render closure. Move it to module level and pass the value through `#!python state` or the action.

### The initial value seems to be rebuilt every render

You passed `#!python build_initial_state()` instead of `#!python build_initial_state`. ReactPy needs the function itself to know it may skip the work.

### My reducer raised and nothing said so

Expected. Reducer errors land in the server log as `Failed to execute event handler` and are otherwise swallowed; the state is left unassigned. Look at the server output, not the browser console.

### I want an updater function instead of an action

That is what `#!python use_state` gives you: `#!python set_value(lambda previous: ...)`. If that is all you need, `#!python use_reducer` is ceremony you do not owe yourself.
