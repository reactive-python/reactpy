## Overview

<p class="intro" markdown>

Structuring state well is the difference between a component that is pleasant to modify and one that is a constant source of bugs. ReactPy makes these guidelines matter more than they do in React, because it detects state changes with `==` rather than by identity, and because it re-renders every child of a component that re-renders. Each principle below comes with the failure it prevents, measured.

</p>

!!! summary "You will learn"

    -   When to group state into one object, and what that trade actually costs
    -   Why contradictions, redundancy, and duplication each buy you a bug
    -   How ReactPy's `==` comparison changes the "never mutate state" rule
    -   What a flat state shape does to the cost of an update

## Principles for structuring state

When you write a component that holds state, you choose how many state variables to use and what shape their data has. A poor shape still runs correctly; it just makes mistakes easier to make. Five principles point the other way:

1.  **Group related state.** If you always update two or more state variables together, merge them into one.
2.  **Avoid contradictions in state.** If two pieces of state can disagree, you have left room for a bug.
3.  **Avoid redundant state.** If you can calculate a value from props or existing state during render, do not put it in state.
4.  **Avoid duplication in state.** Data stored in two places must be kept in sync in two places.
5.  **Avoid deeply nested state.** To change one leaf you must rebuild every ancestor.

The goal is to make state easy to update without introducing mistakes — the same reason a database engineer normalizes a schema. To paraphrase Einstein: **make your state as simple as it can be, but no simpler.**

One fact about ReactPy changes how all five pay off, so it comes first.

### ReactPy compares state with `==`

`use_state` compares the value you set against the current one with `strictly_equal`, which falls through to `==`. If the two compare equal, **nothing re-renders**. Verified against a real `Layout`, one press each:

| You set | over | Renders |
| --- | --- | --- |
| `{"items": [1, 2]}` — a brand-new dict | `{"items": [1, 2]}` | **0** |
| `[1, 2, 3]` — a brand-new list | `[1, 2, 3]` | **0** |
| `[]` | `[]` | **0** |
| `{"a": {"b": 2}}` | `{"a": {"b": 1}}` | 1 |
| `[1, 2]` | `(1, 2)` | 1 |

The first three rows are the ones to internalise. In React, setting a fresh object always re-renders, because React compares by identity. In ReactPy, a new object that *reads* the same as the old one is discarded.

That makes the "never mutate state" rule stricter, not looser:

```python linenums="0"
rows["items"].append("x")
set_rows(rows)  # same object, and == equal -> no render at all
```

Verified: three presses of that handler leave the rendered count at `n=0` with the component body having run once. The mutation *did* happen — the list really grew — but nothing re-rendered to show it, so the screen and the data now disagree. Build a new object instead (`{**rows, "items": [*rows["items"], "x"]}`) and the update becomes visible.

It also means a tuple and a list are different states: `[1, 2]` over `(1, 2)` renders, because `strictly_equal` checks `type(x) is type(y)` before anything else. Pick one container type per field. See [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md) for the full comparison rules.

## Group related state

Should you use several state variables or one object?

Technically either works. But **if two state variables always change together, put them in one state variable**, so there is no second setter call to forget. Here the two coordinates are separate, and one handler forgets the second call:

=== "app.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/coordinates_separate/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Press **Move (forgot y)**: the dot travels horizontally and the readout confirms the split — `#!python x=44  y=20`. Every later move compounds it, because each handler builds on the state it already has.

With one object, the mistake has nowhere to live:

=== "app.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/coordinates_grouped/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Two presses of **Move diagonally** give `#!python x=68  y=68`. There is no second setter to omit: one `#!python set_position` call carries both axes, and the dict you build has to say something about each one.

The trade is worth naming, because it is not free. A single object means every update rebuilds the whole object, and `#!python position["x"]` is noisier than `#!python x`. ReactPy does not sweeten it with fewer renders: verified, two presses of "move both" cost two renders in the separate version and two in the grouped version, and moving only `#!python x` costs one render in both. Group related state to remove a class of bug, not to save work.

## Avoid contradictions in state

A feedback form tracks its send with two booleans:

=== "app.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/feedback_flags/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The code works — and it permits a state that should be impossible. Press **Send (buggy)**, which sets `#!python is_sent` without clearing `#!python is_sending`, and the readout reports:

```text linenums="0"
is_sending=True  is_sent=True
```

That is not hypothetical. Nothing in the data structure prevents those two flags being true together, so the only thing protecting you is remembering every setter in every handler. The readout exists so you can see the disagreement; in a real component you would instead see a spinner that never stops.

Since the flags can never both be true, replace them with one variable holding one of three values:

=== "app.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/feedback_status/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`#!python status` passes through `#!python "sending"` and ends at `#!python "sent"`, which swaps the form for a thank-you. There is no way to be in two states at once, because there is only one variable.

You can still write the readable names:

```python linenums="0"
is_sending = status == "sending"
is_sent = status == "sent"
```

Those are plain local variables computed during render, not state. They cannot drift, which is exactly why they should not be state.

## Avoid redundant state

A check-in form shows a full name built from two fields:

=== "app.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/full_name_stored/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

It has three state variables, and one is redundant — `#!python full_name` is derivable from the other two at any moment. That is not merely wasteful; it is a second place every writer must remember. Press **Rename first**: `#!python first_name` becomes `#!python "Grace"`, and the ticket still reads `#!python Ada Lovelace`.

Remove the state variable and calculate it:

=== "app.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/full_name_derived/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Now **Rename first** followed by **Rename last** gives `#!python Grace Hopper`. The same two buttons cannot go wrong, because there is only one copy of the name.

The difference is not the render count — both versions render once per press, verified. It is that the derived version has no code path that produces a stale ticket.

!!! abstract "Note"

    Deriving is the default, but not free when a calculation is genuinely expensive. The order is: derive first, then measure. If a render is too slow, cache the *value* with `#!python use_memo` rather than promoting it to state — a cache adds no render, a state variable does. See [You Might Not Need an Effect](./you-might-not-need-an-effect.md#caching-expensive-calculations).

## Avoid duplication in state

A snack menu lets you choose one item and edit the titles. This version stores the selected item as an object:

=== "app.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/snacks_duplicated/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Press **Choose** on `#!python pretzels`, then edit that input to `#!python chips`. The input updates; the line below it does not:

```text linenums="0"
You picked pretzels.
```

`#!python selected_item` is a second copy of data that also lives inside `#!python items`. `#!python set_items` updated one copy and nothing updated the other — the same bug as the stale full name, one level deeper.

Hold the *id* instead and look the item up during render:

=== "app.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/snacks_normalized/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Editing the selected row now updates the line below it, because `#!python selected_item` is a `#!python next(...)` over `#!python items`, re-evaluated on every render. The state went from:

-   `#!python items = [{"id": 0, "title": "pretzels"}, ...]`
-   `#!python selected_item = {"id": 0, "title": "pretzels"}`

to:

-   `#!python items = [{"id": 0, "title": "pretzels"}, ...]`
-   `#!python selected_id = 0`

Only the id is essential; the rest was a copy. The same reasoning turns a selected object into an id, a filter string into its own fields, and a sorted list into an unsorted list plus a sort.

!!! warning "Pitfall"

    "Store the id, derive the object" meets ReactPy's `==` comparison in one place worth knowing about. A derived object handed to `#!python use_effect` as a dependency compares equal every render, so the dependency holds and the effect never restarts — usually what you want. But that also means a dependency cannot detect a change that `==` cannot see. Verified with a plain class instance held as a dependency and mutated in place: across three presses the component re-rendered each time and the screen showed `#!python n=3`, while the effect ran once and kept reporting `#!python n=0`. Use dict and list, or an immutable `#!python @dataclass(frozen=True)`, for anything that appears in a dependency array. See [Removing Effect Dependencies](./removing-effect-dependencies.md).

## Avoid deeply nested state

A travel plan is planets, then continents, then countries. The tempting shape mirrors the picture. Two files make the example — `#!python app.py` renders it, `#!python data.py` holds the tree:

=== "app.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/places_nested/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/places_nested/data.py" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Marking one country visited calls `#!python mark_visited`, which copies the root, copies `#!python Earth`, copies the continent, and copies every sibling along the way — a new object for every node between the root and the leaf. Correct, and also easy to get wrong: miss one `#!python {**node, ...}` and you have mutated shared state, which in ReactPy means the update may compare equal and never render.

Flatten the tree into one dict keyed by id, with child lists of ids:

=== "app.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/places_flat/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/choosing_the_state_structure/places_flat/data.py" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The same update now adds one entry to one set, and finding a place is a dict lookup rather than a recursion. The rendering component still walks the tree by id, so the display is unchanged — only the update path got shorter.

A useful test for whether nesting has gone too far: **count the objects an update has to rebuild to change one field.** If the answer is "everything above it", flatten. If the hierarchy is genuinely part of the data and updates are rare, nesting is fine — the cost is in writes, not reads.

!!! info "Deep Dive"

    Flattening is what databases do, and ReactPy's `==` comparison gives you a concrete second reason. Because a state update is detected by comparing values, an update that rebuilds a large object makes ReactPy compare that whole object for equality — `#!python dict.__eq__` walks every key, and nested dicts compare recursively. A flat dict with one changed entry is a small comparison; a rebuilt tree is a comparison of everything you just rebuilt. For the shapes that matter, measure rather than guess: ReactPy ships no render profiler, so count renders with a `#!python use_ref` counter in the component body, as the examples on this page do.

## Recap

-   ReactPy's `use_state` compares with `==`: setting a new object that reads equal to the old one renders nothing. Copy objects rather than mutating them — verified, mutating leaves the screen and the data disagreeing.
-   `type(x) is not type(y)` makes `(1, 2)` and `[1, 2]` different states, so pick one container type per field.
-   Group state that always changes together. It removes the "forgot the second setter" bug; it does not reduce renders (verified: same count both ways).
-   Replace mutually exclusive booleans with one variable holding one of several values, so the impossible state is unrepresentable.
-   Derive anything you can calculate during render. Both versions of the name form render the same number of times; only one of them can show a stale ticket.
-   Store ids, not copies. Edit the selected row and the derived label follows while the stored one does not.
-   Count how many objects an update must rebuild. If nesting forces you to rebuild the path to every leaf, flatten and key by id.

## Related

-   [You Might Not Need an Effect](./you-might-not-need-an-effect.md) — the same derive-don't-store rule applied to Effects
-   [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md) — `strictly_equal` in full, and why dependency arrays use `==`
-   [Updating Objects in State](./updating-objects-in-state.md) and [Updating Arrays in State](./updating-arrays-in-state.md) — the copy idioms this page assumes
-   [Queueing a Series of State Updates](./queueing-a-series-of-state-updates.md) — functional updaters, for when two handlers race
-   [Extracting State Logic into a Reducer](./extracting-state-logic-into-a-reducer.md) — the next step once one component holds too many fields
-   [Use State](../reference/use-state.md) — parameter-level reference
