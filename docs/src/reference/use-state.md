## Overview

<p class="intro" markdown>

`use_state` is a ReactPy hook that lets you add a [state variable](../learn/state-a-components-memory.md) to your component.

</p>

```python linenums="0"
value, set_value = use_state(initial_value)
```

---

## Reference

### `use_state(initial_value)`

Call `use_state` at the top level of your component to declare a [state variable](../learn/state-a-components-memory.md).

```python linenums="0"
from reactpy import use_state
```

#### Parameters

-   **`initial_value`**: The value you want the state to start with. It can be any Python value. Alternatively, pass a **function taking no arguments** and returning the initial value; ReactPy calls it on the first render only, which avoids rebuilding an expensive value on every render. See [avoiding recreating the initial state](#avoiding-recreating-the-initial-state).

#### Returns

`use_state` returns a `reactpy.types.State` — a named tuple of two items, which is normally unpacked:

-   **`value`**: The current state, as of the start of this render.
-   **`set_value`**: A function that updates the state and schedules a re-render. See [`set_value`](#set-value).

Because `State` is a named tuple you can also reach the halves explicitly (`state.value`, `state.set_value`), but unpacking is the convention.

#### Caveats

-   `use_state` is a hook, so call it **only at the top level** of your component or of your own hooks — never in a loop, a conditional, or after an early `return`. ReactPy does **not** check for this: changing which hooks run between renders produces a scrambled component and a cryptic `IndexError: list index out of range` rather than a helpful message. If you need conditional state, extract a component.
-   `initial_value` is used only on the first render. Later changes to the expression are ignored — see [resetting state with a key](#resetting-state-with-a-key).
-   **Do not pass a function you intend to store.** A callable `initial_value` is treated as an initializer and *called*. `use_state(lambda value: value * 2)` does not store the lambda; ReactPy calls it with no arguments and the component fails. To keep a function in state, wrap it (`use_state(lambda: my_function)`) or store it in a [`use_ref`](./use-ref.md).
-   Unlike React, ReactPy has **no Strict Mode**, so your initializer is called exactly once — verified: one call across four renders. Nothing will run it twice to expose impurity for you, so test purity yourself if it matters.

---

### `set_value(next_value)` { #set-value }

The `set_value` function returned by `use_state` updates the state and schedules a re-render.

#### Parameters

-   **`next_value`**: The value you want the state to become. Any Python value, **or** a function taking one argument and returning the next state. That function receives the current value, runs eagerly inside the setter, and must be [pure](../learn/keeping-components-pure.md). See [updating state based on the previous state](#updating-state-based-on-the-previous-state).

#### Returns

`None`.

#### Caveats

-   Setting state does **not** change the variable you already have in this render — it schedules a new one. See [State as a Snapshot](../learn/state-as-a-snapshot.md).
-   Setting state to a value equal to the current one **does not re-render**. The comparison is `core/hooks.py`, `strictly_equal` — and it is *not* an identity check: the two values must share a type, two locally-defined functions or lambdas are compared by their code, and everything else is compared with `==`, falling back to identity only if that raises. So a **brand-new object is dropped too** whenever it merely compares equal: setting `#!python [1, 2, 3]` while the state is an equal list renders nothing, and the same goes for any class whose `#!python __eq__` matches. Only values with identity-based `#!python __eq__` — plain class instances, say — re-render when you replace them.
-   `set_value` **replaces** the state; it never merges a partial object into it. Verified: setting `{"a": 9}` over `{"a": 1, "b": 2}` yields `{"a": 9}`. Update objects with `set_value({**value, "k": v})` — see [Updating Objects in State](../learn/updating-objects-in-state.md).
-   **Mutating the current value and passing it back does nothing.** The comparison finds the value equal to itself, so no render is scheduled — and there is no error, no warning, and nothing in the console. `set_value(items.append(x))` also stores `None`, because most mutating list methods return `None`.
-   If the updater function raises, the error is logged on the server as `Failed to execute event handler` and **swallowed**; the state is left unassigned and the UI simply stops updating. Check the server log, not the browser console.
-   `set_value` is a **stable object**: the same callable is returned on every render of that component. Verified across four renders. That makes it safe to put in a dependency list or pass to a child without causing extra renders.

---

## Usage

### Adding state to a component

Call `use_state` at the top level of your component, and use the returned value while rendering:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_state/counter/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Each state variable gets its own setter, so prefer several narrow variables over one crowded object:

```python linenums="0"
first_name, set_first_name = use_state("Ada")
last_name, set_last_name = use_state("Lovelace")
age, set_age = use_state(42)
```

#### Counter (number)

To update a number based on its current value, use a function:

```python linenums="0"
async def handle_add(event):
    set_step(lambda step: step + 1)
```

Or read the value from this render directly when you don't need the latest: `#!python set_step(step + 1)`.

#### Text field (string)

A controlled input reads its `#!python "value"` from state and writes back through `#!python "onChange"`:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_state/text_field/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Type into the field and the heading follows. Note the key names: `#!python "value"` and `#!python "onChange"` are DOM attribute names inside the attributes dictionary, while the Python names around them are `snake_case`.

Reading which field an event came from is possible — `#!python await event.target.name` asks the page for it — but it costs a round trip, so when the handler already knows which field it belongs to, bind that in Python instead: a named handler per field, a closure, or a `#!python functools.partial`. See [Responding to Events](../learn/responding-to-events.md).

#### Checkbox (boolean)

`#!python await event.target.checked` tells you whether the box is ticked:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_state/checkbox/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Tick the box and the status line flips. `#!python checked` is fetched from the live element when the handler awaits it, in the same message as any other property would be — nothing arrives up front, so a handler which never reads it never pays for it.

#### Form (two variables)

Two inputs, two state variables, no interference between them:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_state/form/app.py" start="# start" %}
    ```

=== ":material-play: Run"

### Updating state based on the previous state

A common case is updating state based on the value that came before. Pass a function instead of a value:

```python linenums="0"
set_count(lambda count: count + 1)
```

ReactPy calls your function with the current state and assigns the result.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_state/updater/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Click "+3" and the counter reaches `#!python 3`, because each updater sees what the previous one produced — verified. Had these been `#!python set_count(count + 1)` instead, all three would compute from the same render-time `#!python count` and the result would be `#!python 1`. See [Queueing a Series of State Updates](../learn/queueing-a-series-of-state-updates.md).

#### Is using an updater always preferred?

No. If you are setting state to a value that does not depend on previous state, pass the value. Updaters are for when the next value is derived from the last, or when several updates to the same variable must compose within one handler.

#### Passing the updater function

The function must be pure — it should only compute and return the next value. Do not send requests, mutate the argument, or set other state inside it.

```python linenums="0"
# Correct: pure, returns the next value
set_count(lambda count: count + 1)

# Wrong: mutates, and returns None
set_items(lambda items: items.append("new"))
```

#### Passing the next state directly

When the value comes from outside, pass it plainly:

```python linenums="0"
set_first_name("Ada")
```

### Updating objects and arrays in state

Pass a **new** object; there is no merge. For dicts use unpacking, for lists use a comprehension or slicing:

```python linenums="0"
async def handle_first_name(event):
    set_person({**person, "firstName": await event.target.value})


async def handle_add(event):
    set_items([*items, {"id": next_id, "text": text}])
```

Full treatment, including nested updates and the silent-drop failure mode, is on [Updating Objects in State](../learn/updating-objects-in-state.md) and [Updating Arrays in State](../learn/updating-arrays-in-state.md).

### Avoiding recreating the initial state

ReactPy ignores `initial_value` after the first render, but the *expression* still runs on every render. If building it is expensive, pass a function:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_state/initializer/app.py" start="# start" %}
    ```

=== ":material-play: Run"

`#!python create_expensive_state` is called once, on mount — verified (one call across four renders).

#### Passing the initializer function

```python linenums="0"
state, set_state = use_state(create_expensive_state)   # called once
```

#### Passing the initial state directly

```python linenums="0"
state, set_state = use_state(create_expensive_state())  # built every render
```

Correct, but wasteful. Note again that a bare function is interpreted *as* an initializer, which is why the second form calls it explicitly.

### Resetting state with a key

ReactPy normally preserves state between re-renders, matching children by position and `#!python key`. To force a component to start fresh, give its *call site* a different key:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_state/reset_by_key/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Switching accounts resets the counter to zero, because a changed key means a different component as far as ReactPy is concerned. Verified: a keyed child bumped to `#!python 2` came back at `#!python 0` after its key changed, while the identical child rendered *without* a key kept its count.

### Storing information from previous renders

To keep a history, read the previous list through an updater so it composes correctly, and capture this render's value:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_state/previous_render/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Clicking twice records `#!python Previous values: 0, 1` — verified. The `#!python history` name in the closure would still be the render-time value, which is exactly why the updater form matters here. For genuinely mutable, non-rendering values, use [`use_ref`](./use-ref.md) instead.
