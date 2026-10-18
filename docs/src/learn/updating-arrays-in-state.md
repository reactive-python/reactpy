## Overview

<p class="intro" markdown>

Lists are mutable in Python, but you should treat them as immutable when you store them in state. Just like with objects, when you want to update a list stored in state, you need to create a new one (or make a copy of an existing one), and then set state to use the new list.

</p>

!!! summary "You will learn"

    -   How to add, remove, or change items in a list in ReactPy state
    -   How to update an object inside of a list
    -   Why a mutating update is dropped without any error

## Updating lists without mutation

In JavaScript you copy arrays with the spread syntax, and mutating methods like `#!js push()` and `#!js pop()` are easy to reach for by mistake. Python's equivalent methods — `#!python append()`, `#!python extend()`, `#!python insert()`, `#!python remove()`, `#!python pop()`, `#!python sort()`, `#!python reverse()` — are **in-place and return `#!python None`**, so the mistake looks different and fails harder:

```python linenums="0"
async def handle_add(event):
    items.append({"id": next_id, "text": text})   # mutates, returns None
    set_items(items)                              # same object -> ignored
```

Nothing happens. ReactPy compares the new value against the old one with `==` (`core/hooks.py`, `strictly_equal`), sees nothing changed, and schedules no render. There is no error, no warning, and nothing in the browser console. Verified directly: mutating then setting the same list produces no render at all. Nor does setting a *new* list that happens to compare equal — which is why `#!python set_rows([*rows, 4])` works while mutating `#!python rows` and passing it back does not.

So whenever you want to update a list, pass a **new** list to the setter. Python gives you two tools for that:

| Instead of (mutates) | Use (new list) |
| --- | --- |
| `#!python items.append(x)` | `#!python [*items, x]` |
| `#!python items.remove(x)` | `#!python [i for i in items if i is not x]` |
| `#!python items[i] = x` | `#!python [*items[:i], x, *items[i + 1:]]` |
| `#!python items.pop(i)` | `#!python [*items[:i], *items[i + 1:]]` |
| `#!python items.insert(i, x)` | `#!python [*items[:i], x, *items[i:]]` |
| `#!python items.reverse()` | `#!python list(reversed(items))` |
| `#!python items.sort(key=f)` | `#!python sorted(items, key=f)` |

!!! warning "Never store an iterator in state"

    This one has no JavaScript analogue and will bite you. Python's `#!python filter()` and `#!python map()` return **lazy, single-use iterators**, not lists:

    ```python linenums="0"
    set_items(filter(lambda i: i["id"] != id_to_delete, items))   # 🚩
    ```

    That renders correctly *once*, which is exactly what makes it so hard to diagnose. The iterator is consumed while ReactPy walks the children, so the next render of that same state sees an exhausted iterator and displays **nothing**. Verified: a list of three items filtered to `#!python "a,c"` on the first render, then an unrelated state change rendered an empty line.

    Always build a list — a comprehension is clearest, `#!python list(filter(...))` if you must:

    ```python linenums="0"
    set_items([i for i in items if i["id"] != id_to_delete])   # correct
    ```

### Adding to a list

The common case is adding an item. The handler creates a new list ending with the new item:

=== "app.py"

    ```python
    {% include "../../examples/updating_arrays_in_state/add_to_array/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Type a task and submit; it appends while the existing ones stay put. Note that the new id is computed from the existing items rather than from a module-level counter. A global counter is shared by every visitor to the server, so two users would collide on the same key — derive ids from the state you already have, or use `#!python uuid4()`.

### Removing from a list

The most common removal is filtering out one item:

=== "app.py"

    ```python
    {% include "../../examples/updating_arrays_in_state/remove_from_array/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`#!python [item for item in items if item["id"] != id_to_keep]` produces a brand-new list containing everything except the deleted item, and the original is left alone.

### Transforming every item

To apply a change to every item, build a new list by transforming each element:

=== "app.py"

    ```python
    {% include "../../examples/updating_arrays_in_state/transform_array/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Each item becomes a **new dict**, because mutating `#!python item["text"]` in place would leave the previous state pointing at the same mutated object.

!!! info "Comprehensions do not modify the original"

    React's docs point out that `#!js filter()` doesn't touch the original array, and a Python comprehension has the same property — it reads the old list and returns a fresh one. The catch, stated above, is that the *built-in* `#!python filter()` does not return a list at all.

### Replacing an item

Unlike most languages, Python has no `#!python setAt(i, x)` method, and the obvious `#!python items[i] = x` mutates. Build the list from slices instead:

=== "app.py"

    ```python
    {% include "../../examples/updating_arrays_in_state/replace_item/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`#!python [{"id": 0, "text": text}, *items[1:]]` replaces the first item and copies the rest. For an arbitrary index, `#!python [*items[:i], new_item, *items[i + 1:]]` is the general form.

### Inserting into a list

To insert an item somewhere other than the end, slice around the insertion point:

=== "app.py"

    ```python
    {% include "../../examples/updating_arrays_in_state/insert_at_index/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`#!python [*items[:1], new_item, *items[1:]]` puts the new item at index `#!python 1`. This is how React's "insert into an array" example translates; `#!python list.insert()` mutates and is unusable here.

### Making other changes to a list

The rule is uniform: **copy first, then operate on the copy**, or use a function that already returns a new list.

=== "app.py"

    ```python
    {% include "../../examples/updating_arrays_in_state/other_changes/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`#!python reversed()` returns an iterator, so wrap it in `#!python list(...)`; `#!python sorted()` already returns a new list; `#!python items[:2]` is a slice, which is already a new list.

!!! warning "`list.sort()` and `list.reverse()` return `None`"

    These two are the most expensive traps because the failure is invisible. `#!python items.sort()` sorts **in place** and returns `#!python None`, so `#!python set_items(items.sort())` stores `#!python None` in state. Use `#!python sorted(items)` and `#!python list(reversed(items))`.

## Updating objects inside lists

The examples above replaced whole dicts, which is the safe default. When an item is a dict whose fields you want to change one at a time, you need two copies: a new **list**, and a new **dict** for the item that changed.

=== "app.py"

    ```python
    {% include "../../examples/updating_arrays_in_state/objects_in_arrays/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Tick one checkbox and only that artwork's `#!python "seen"` flips — verified, the pair goes from `#!python [False, False]` to `#!python [True, False]`. The comprehension copies every item, and only the targeted one is rebuilt with the changed field.

!!! warning "A shallow copy of the list is not enough"

    It is tempting to write:

    ```python linenums="0"
    next_items = list(artworks)          # new list...
    next_items[0]["seen"] = True         # ...but the SAME dicts inside
    set_items(next_items)
    ```

    That is a new list containing the **same dict objects**. Two problems follow. The assignment mutates a dict the previous state still references, so the change is invisible to ReactPy's comparison. And anything else holding that dict — another component seeded from the same fixture, a cached render — sees it flip too.

    Copying is shallow at every level in Python; there is no deep copy on assignment or unpacking. Build the changed dict explicitly, as the example does. See [Updating a nested object](./updating-objects-in-state.md#updating-a-nested-object) for the object-side version of this.

!!! tip "Keep identity stable for unchanged items"

    Notice the `#!python else artwork` branch: unchanged items are passed through as the **same objects**, not rebuilt. That is both cheaper and useful — if you rebuild everything on each keystroke, nothing can be recognised as unchanged later.

### Writing concise update logic

React's docs finish this page with Immer, which lets you write `#!js draft.push(...)` behind a proxy. **ReactPy has no Immer and no equivalent.** There is no proxy layer to record your mutations, and no `#!python use_immer` to import.

What you have instead is what this page already used:

-   **List unpacking and comprehensions** — `#!python [*items, x]`, `#!python [f(i) for i in items]`, `#!python [*items[:i], x, *items[i:]]`. Verbose but explicit, and it fails loudly rather than silently.
-   **`#!python copy.deepcopy`** — for a structure too nested to copy by hand.
-   **`use_reducer`** — moves the update logic out of the component, which is where the verbosity actually starts to hurt. See [Extracting State Logic into a Reducer](./extracting-state-logic-into-a-reducer.md).

A homegrown Immer is worth avoiding specifically because it would paper over the failure mode this page is about: mutations are more dangerous here than in the browser, because ReactPy decides whether to render by comparing the old and new values on the server — so a mutation that hands back the same object, or an equal one, is dropped without a trace.

## Recap

-   Treat lists in state as read-only: never call `#!python append()`, `#!python sort()`, `#!python insert()`, `#!python remove()`, and friends on them.
-   Build a new list with `#!python [*items, x]` or a comprehension, and pass that to the setter.
-   Mutating and passing the same list back is silently dropped — no render, no error.
-   Never store `#!python filter()`/`#!python map()` results in state; they are single-use iterators and the second render will be empty.
-   To change an object inside a list, copy the list **and** copy the changed dict.
-   There is no Immer in ReactPy; use comprehensions, `#!python deepcopy`, or `#!python use_reducer`.
