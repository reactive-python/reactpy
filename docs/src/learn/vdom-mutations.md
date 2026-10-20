## Overview

<p class="intro" markdown>

A ReactPy element is a `#!python dict`, and Python lets you assign into it. That is the whole topic of this page: what is safe to change, what is merely pointless, and what quietly corrupts the model that the server is holding on behalf of every connected browser. The rule that decides all of it is that a model is **owned by exactly one render** — before it, yours to shape; after it, ReactPy's.

</p>

!!! summary "You will learn"

    -   Why mutation before a render is fine and after it is not
    -   Which parts of a built element are copies and which are shared
    -   The module-level element that leaks one user's change into everyone's page
    -   Safe shapes: build fresh, `#!python deepcopy`, and transform at build time

## The rule: a model belongs to its render

ReactPy serializes your element to JSON and sends it. Once that has happened, the dictionary is no longer purely yours — the layout keeps live references to the same objects so it can patch a subtree later (`core/layout.py`, `Layout._create_layout_update` reuses `model.current` rather than rebuilding it).

Split your code on that line:

-   **Before the element is returned** — mutate freely. Building a model incrementally out of helper functions is normal Python and nothing is watching.
-   **After it has been returned from a render** — treat it as frozen. Changes now affect a model the client has already received, and the server has no idea they happened.

Nothing in ReactPy enforces this. There is no freeze, no copy-on-render, no warning. That is why the failure modes below are worth memorizing.

## What is safe before the render

`#!python VdomDict` is a light `#!python dict` subclass, and it is strict about its top-level keys — exactly `#!python tagName`, `#!python children`, `#!python attributes`, `#!python eventHandlers`, `#!python inlineJavaScript`, `#!python importSource`:

```python linenums="0"
d = html.div({"id": "pre"}, "x")

d["tagName"] = "section"       # fine
d["attributes"]["id"] = "a"    # fine — but only because "attributes" exists
d["children"].append("tail")   # fine
d["key"] = 1                   # KeyError: 'Invalid key: key'
d["ref"] = object()            # KeyError: 'Invalid key: ref'
```

Note the first line passes an attributes dict. `#!python html.div("x")` omits the `#!python attributes` key entirely when there are none — verified, it returns `#!python {'children': ['x'], 'tagName': 'div'}` — so `#!python d["attributes"]["id"] = "a"` on such an element raises `#!python KeyError: 'attributes'` before any guard is reached. Use `#!python d.setdefault("attributes", {})["id"] = "a"` when the element may not have had one.

The guard only covers the six top-level names. `#!python d["attributes"]["anything"]` is unvalidated, and so is every nested value — the validation happens at serialization, and only in debug mode.

!!! warning "Keys and refs are not top-level keys"

    The React shapes `#!python {"key": ...}` and `#!python {"ref": ...}` raise, because a `#!python VdomDict` has no such slot. A `#!python key` goes **inside** `#!python attributes` for an element (`#!python html.li({"key": 1}, ...)`) or is passed as a keyword to a component (`#!python Item(x, key=1)`). A `#!python ref` does not exist at all — see [Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md).

### Shallow copy, deep sharing

The constructors copy the top level, so the containers you passed in are not aliased into the element — but the copy is shallow, and nested values still point at your objects:

=== "app.py"

    ```python
    {% include "../../examples/vdom_mutations/shallow_copy.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

The same applies to child elements: pass a model you built earlier and the parent stores *that object*, not a copy. Mutating the child later changes the parent. This is convenient for builders that assemble a tree in stages, and dangerous for anything that outlives the render — which is the subject of the next section.

## Mutating after the render

There are two ways this goes wrong, and they look nothing alike.

### Case 1: the mutation is never sent

Change a rendered element and ask for no re-render, and the browser never learns. This is the same class of bug as mutating state in place, and it shares the cause: ReactPy decides what to send from state changes, not from the shape of your dictionaries.

There is no error, no log line, and no console message. The element in the browser keeps its old text and you keep staring at the assignment that "obviously" should have worked.

!!! warning "A mutation you make while handling an event is invisible until something else renders"

    This is the version that costs an afternoon. In a real browser, against the [shared-element example](#case-2-the-mutation-escapes-to-other-users) below: click `#!python mutate` and the page does **not** change; click `#!python bump`, which changes unrelated state, and the mutation appears — as if it had been waiting. Because the re-render walks the model again, it re-reads the dictionary you edited and ships the change with the next patch. A user's action becomes visible on the *next* action, which is a bug that looks like a timing problem and is not one.

### Case 2: the mutation escapes to other users

The more damaging case, and the one unique to a server-side framework.

A model built at **module level** is one object shared by every connection to the server. Each connection gets its own `#!python Layout` and its own hook state, but they all render *the same dictionary*. One visitor's handler mutates the object that everyone else's next render reads:

=== "app.py"

    ```python
    {% include "../../examples/vdom_mutations/shared_element_leak.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

Verified in a real browser with two separate tabs and two separate websockets against one server: tab A clicks `#!python mutate`, then `#!python bump`; tab B, which never clicked anything, then clicks `#!python bump` and sees `#!python mutated by visitor 0` in **its own** page. Neither user can make it go away, because the mutated module-level dict is now the source of truth for every future render.

!!! danger "Module-level elements are shared across all connections"

    This has no browser-side analogue — in React, module scope is per-tab. Here module scope is per-*process*, and the process is shared. The rule follows directly: **build elements inside the component.** A function that returns `#!python html.p(...)` costs one dictionary construction and removes the whole class of bug:

    === "app.py"

        ```python
        {% include "../../examples/vdom_mutations/build_fresh.py" start="# start" end="# end" %}
        ```

    === ":material-play: Run"

    Module-level constants are still fine when they are genuinely inert — a style dict, a list of option labels, an `#!python html.head()` passed once to `#!python ReactPy(html_head=...)` — because nothing writes to them. The bug needs a write. If nothing in your program assigns into it, module scope is safe.

## The two mutation habits that also defeat state

These belong to [Updating Objects in State](./updating-objects-in-state.md) and [Updating Arrays in State](./updating-arrays-in-state.md), but they are VDOM mutation seen from the other side, so they are repeated here because the symptom — a control that stops responding with no error — is the one people hunt for longest.

`#!python use_state`'s setter compares the new value against the old with `#!python ==` (`core/hooks.py`, `strictly_equal`). So:

```python linenums="0"
rows.append(x)
set_rows(rows)          # same object -> compares equal -> no render, no error
```

And the corollary that surprises people: a **new** object that merely compares equal is dropped too, so `#!python set_rows([*rows])` when `#!python rows` is unchanged also renders nothing. Replace state with new, non-equal objects; never edit in place.

The same comparison is what makes `#!python use_memo` fail to recompute after a mutate-then-set — the dependency compares equal to itself.

## Safe ways to shape a model

Reach for these in order.

### Build it, do not edit it

The default. Compose with functions, keep elements as return values, and pass data in as arguments. Conditional structure is an expression, not a post-construction edit:

```python linenums="0"
def row(item):
    return html.li(
        {"key": item["id"], "className": "row" if item["done"] else "row pending"},
        item["text"],
    )
```

### `#!python deepcopy` for a genuine fork

When you must derive a variant from a model you do not own — typically something that came back from `#!python string_to_reactpy()` or a cached template — copy it first:

```python linenums="0"
from copy import deepcopy

TEMPLATE = html.div({"className": "card"}, html.p("placeholder"))


def card(body_text):
    model = deepcopy(TEMPLATE)
    model["children"][0]["children"] = [body_text]
    return model
```

`#!python deepcopy` preserves the `#!python VdomDict` class and its key guard, and leaves the original intact — verified. It is the right tool for a template you parse or build once at module level; it is not a licence to mutate a model that has already been rendered.

!!! note "Deep-copying a model with handlers duplicates the handler objects"

    `#!python deepcopy` succeeds on a model that has `#!python eventHandlers`. It builds a new `#!python EventHandler` but shares the wrapped function, so both copies still invoke the same Python code. That is fine for a fork you intend to render; it is not a way to hand two elements independent handlers — build those separately.

### Transform at parse time

For HTML that arrives as a string, pass `#!python *transforms` to `#!python string_to_reactpy()` and edit nodes before anyone has a reference to them — see [Convert Between VDOM and HTML](./convert-between-vdom-and-html.md#transforming-every-node-the-transforms-argument).

### Turn the check on while developing

`#!python REACTPY_CHECK_VDOM_SPEC` validates each rendered model against the JSON schema in `core/vdom.py` — but only catches structural damage (a child that is not a VDOM dict, a missing `#!python tagName`), and it is off unless `#!python REACTPY_DEBUG` is on:

```python linenums="0"
from reactpy import config

config.REACTPY_DEBUG.current = True   # parents REACTPY_CHECK_VDOM_SPEC on
```

It will not catch a `#!python className` you changed to the wrong string, or a text node you rewrote — those are valid VDOM. Treat it as a schema check, not a mutation detector.

## What you may still touch: the DOM, briefly

Nothing here applies to the browser's DOM, which ReactPy does not share with you. The one sanctioned route is an inline-JavaScript handler, and the same discipline applies there — do not mutate nodes ReactPy owns, since the next patch against a node you removed breaks the diff. That is covered in [Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md).

## Summary

-   A model is yours until it is returned from a render; after that the layout holds the same objects.
-   `#!python VdomDict` guards its six top-level keys — `#!python key` belongs inside `#!python attributes`, and there is no `#!python ref`.
-   Constructors copy the top level but share nested values, so a child element you built is the object the parent holds.
-   Mutating a rendered element sends nothing; the change surfaces on the next unrelated render, which makes it look like a timing bug.
-   A module-level element is shared by every connection, so one user's mutation appears in everyone's page. Build elements inside components.
-   Mutate-then-set-the-same-object is dropped by `#!python use_state`'s equality check, with no error.
-   Prefer building fresh; use `#!python deepcopy` for a real fork; use parse-time transforms for parsed HTML.

## Related

-   [Updating Objects in State](./updating-objects-in-state.md) and [Updating Arrays in State](./updating-arrays-in-state.md) — the state-side version of the same hazard
-   [Creating HTML Tags](./creating-html-tags.md) — what the constructors do to your arguments
-   [Convert Between VDOM and HTML](./convert-between-vdom-and-html.md) — where `#!python deepcopy`-and-edit is the natural pattern
-   [Preserving and Resetting State](./preserving-and-resetting-state.md) — how identity actually drives re-mounting
-   [Protocol Structure](../reference/protocol-structure.md) — why the server keeps holding on to those dictionaries
