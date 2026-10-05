## Overview

<p class="intro" markdown>

State can hold any kind of value, including dicts and lists. But you shouldn't change objects that you hold in ReactPy state directly. Instead, when you want to update an object, you need to create a new one (or make a copy of an existing one), and then set the state to use that copy.

</p>

!!! summary "You will learn"

    -   How to correctly update an object in ReactPy state
    -   How to update a nested object without mutating it
    -   What immutability is, and how not to break it
    -   Why a mutating update can be dropped without any error

## What's a mutation?

To _mutate_ something means to change it after it was created.

Objects and lists in Python are _mutable_: you can change their contents in place. The mutating operations are usually visible in the code you write — `#!python obj["key"] = value`, `#!python list.append(x)`, `#!python list.pop()`, `#!python del list[i]`, `#!python d.update(other)` — but there are more hiding behind method names that don't announce themselves (`#!python list.sort()`, `#!python list.extend()`, `#!python list.reverse()`, `#!python dict.setdefault()`).

In ReactPy, treat state as **read-only**. Every time your code renders, you work with the state that already exists, and you want to _cause changes_ over time based on user input. Leaving all mutation to the setter keeps your code easy to understand. This applies to state in general, not just object state.

!!! warning "Mutating state doesn't just risk a bug — it can silently do nothing"

    In React, mutating state is a "may render stale UI" hazard. In ReactPy it is sharper, because the setter compares the new value against the old one **by identity** before scheduling anything (`core/hooks.py`, `strictly_equal`).

    Measured behaviour, each case dispatched through `reactpy.core.layout.Layout`:

    | What the handler does | Result |
    | --- | --- |
    | Mutates a list in place, then `set_x(same_list)` | **no render at all** |
    | Mutates in place, calls no setter | no render |
    | `set_x([*old, item])` — a new object | renders |

    The failure is completely silent: no error, no warning, nothing in the browser console. Your handler ran, ReactPy agreed that nothing changed, and the UI never updates. This is why the read-only rule is not a style preference here.

## Treat state as read-only

Consider a form that lets the user change their profile. This handler reaches into the state object and assigns a field directly:

```python linenums="0"
def handle_first_name(event):
    person["firstName"] = event["target"]["value"]   # 🚩 Mutate!
    set_person(person)                                # same object -> ignored
```

`#!python person` is the very object ReactPy already holds, so the assignment changes it in place and then hands the same object back. ReactPy's identity check sees no change and skips the render — the field appears frozen while your dict quietly holds the new value.

The fix is to always create a **new** object for the next state:

```python linenums="0"
def handle_first_name(event):
    set_person({**person, "firstName": event["target"]["value"]})
```

That is the pattern for every state update in ReactPy: build a new value, pass it to the setter.

A pointer-tracking dot shows the same rule with no form in sight. The handler builds a brand-new position dict on every move:

=== "app.py"

    ```python
    {% include "../../examples/updating_objects_in_state/moving_dot/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The `#!python "onPointerMove"` handler is on the grey container, and the dot is positioned from the coordinates it receives. Move the pointer anywhere inside the box and the dot follows. `#!python event["clientX"]` and `#!python event["clientY"]` are part of what the client sends for pointer events — verified against a real browser, which reported `clientX`/`clientY` matching the synthesized pointer position — so React's pointer and drag demos port across unchanged.

!!! warning "There is no automatic merge"

    `#!python set_x(...)` **replaces** the state. It does not merge a partial object into what was there. Verified: setting `#!python {"a": 9}` over `#!python {"a": 1, "b": 2}` leaves `#!python {'a': 9}` — `#!python "b"` is simply gone.

    If you have read React tutorials, you may remember `setState` merging objects. That was the **class** API. React's own `useState` replaces, and so does ReactPy (`core/hooks.py`, `_CurrentState.dispatch` assigns `self.value = new`). Any ReactJS text saying "React merges the object into your current state" is describing an API that no longer applies — port those examples with an explicit `#!python {**old, ...}`.

!!! info "Local mutation is fine"

    Mutating a value you _just created_ inside the current render is safe, because nothing else has ever seen it. The same applies to the `#!python rows = []` plus `#!python rows.append(...)` loop you will write constantly when building children:

    ```python linenums="0"
    @component
    def list_of_parts(parts):
        # Built during this render, never handed out before.
        sorted_parts = sorted(parts, key=lambda p: p["importance"])
        return html.ul(
            [html.li({"key": p["id"]}, p["title"]) for p in sorted_parts]
        )
    ```

    What must not be mutated is state ReactPy gave you, and props you received. See [Local mutation: Your component's little secret](./keeping-components-pure.md#local-mutation-your-components-little-secret) for the rendering-side version of this rule.

## Copying objects with the spread syntax

To update an object, create a **new** one from the old one so you can change any of its properties. Python has no `#!js ...` spread operator, but `#!python {**obj, "key": value}` is the same operation on dicts, and `#!python [*items, x]` is its twin for lists.

Here the form keeps the other fields intact while replacing one:

=== "app.py"

    ```python
    {% include "../../examples/updating_objects_in_state/form_spread/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Type in any field and watch the heading update. Each handler spreads the current `#!python person` into a fresh dict and overrides exactly one key.

!!! warning "An unpacked dict is a shallow copy"

    `#!python {**person}` copies the top level only. Any nested dict or list inside it is still **shared** with the previous state — see [Updating a nested object](#updating-a-nested-object).

!!! info "The destructuring equivalents"

    Where React's docs reach for `#!js const { a, ...rest } = obj`, Python reads with indexing and writes with unpacking. For the "everything but one key" shape, the direct translation is a comprehension:

    ```python linenums="0"
    rest = {k: v for k, v in obj.items() if k != "drop"}
    ```

### Using a single event handler for multiple fields

Repeating a near-identical handler per field gets tedious. One handler can take the field name:

=== "app.py"

    ```python
    {% include "../../examples/updating_objects_in_state/form_single_handler/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Note how the field name is supplied by the `#!python lambda`. ReactPy invokes every event handler with the event as its **single** positional argument — verified, a handler declaring two required parameters fails with `TypeError: ... missing 1 required positional argument: 'event'`. There is no `#!js e.target.name` to read either, because the client does not send DOM attributes; any extra context has to be bound on the Python side.

!!! tip "Reach for `use_reducer` when handlers multiply"

    Several handlers that all edit one object is a sign the update logic wants its own home. See [Extracting State Logic into a Reducer](./extracting-state-logic-into-a-reducer.md).

## Updating a nested object

State often contains nested objects. To update a deeply nested value, copy the object all the way up from where the change happens.

=== "app.py"

    ```python
    {% include "../../examples/updating_objects_in_state/nested_object/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Two copies are required:

1. Copy `#!python person["shippingAddress"]` with the new `#!python "city"`.
2. Copy `#!python person`, replacing `#!python "shippingAddress"` with that new dict.

Writing `#!python person["shippingAddress"]["city"] = ...` would mutate the nested dict in place. Because that nested dict is the *same object* the previous state still refers to, the change is invisible to ReactPy's comparison and the update is dropped.

!!! info "Objects are not really nested"

    Python makes this point sharper than JavaScript does. Given:

    ```python linenums="0"
    person = {"name": "Jane", "theme": {"background": "white"}}
    copy = {**person}
    ```

    `#!python copy["theme"]` and `#!python person["theme"]` are the **same dict**. Python never deep-copies on assignment or on unpacking — copying is shallow for dicts, lists, and everything else. To get a genuinely independent copy you either copy each level explicitly, as the example does, or use `#!python copy.deepcopy`:

    ```python linenums="0"
    import copy

    set_people(copy.deepcopy(people))
    ```

    `#!python deepcopy` is the blunt instrument: correct, but slower, and it copies everything reachable, including objects you did not mean to duplicate. Prefer explicit copies for the paths you actually change, and keep state to plain dicts, lists, and primitives so `#!python deepcopy` remains a safe fallback.

    Shallow sharing is also why two components seeded from the same module-level fixture end up aliasing each other's data — see [Updating Arrays in State](./updating-arrays-in-state.md) for the list version of that bug.

### Writing concise update logic

React's docs reach for Immer here, which records your mutations through a proxy and turns them into copies. **ReactPy has no Immer and no equivalent.** There is no proxy layer, so nothing could observe your mutations, and there is no `#!python use_immer` to import.

What you have instead:

-   **Dict and list unpacking** — `#!python {**obj, "k": v}`, `#!python [*items, x]`. This covers the overwhelming majority of updates and is what every example above uses.
-   **`#!python copy.deepcopy`** — for the rare shape too deep to copy by hand.
-   **`use_reducer`** — does not shorten updates, but moves them out of the component so their verbosity costs you less. See [Extracting State Logic into a Reducer](./extracting-state-logic-into-a-reducer.md).

Resist building your own Immer. A proxy that logs mutations would have to run on the server, after a websocket round trip, which is not the problem Immer solves in the browser. If update logic feels genuinely painful, that usually means the state shape is wrong — see [Choosing the State Structure](./choosing-the-state-structure.md).

## Recap

-   Treat everything ReactPy hands you as state or props as read-only: never assign into it, never call a mutating method on it.
-   Build a **new** object with `#!python {**old, ...}` and pass that to the setter.
-   Mutating in place and passing the same object back is silently dropped — ReactPy compares by identity and schedules no render. Nothing in the browser will tell you.
-   Copying is shallow at every level; copy all the way up from the field that changed, or use `#!python copy.deepcopy`.
-   Mutating a value you created during this render is fine.
-   There is no Immer in ReactPy; use dict and list unpacking, or restructure the state.
