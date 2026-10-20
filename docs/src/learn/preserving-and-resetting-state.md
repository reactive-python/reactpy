## Overview

<p class="intro" markdown>

State is isolated between components. ReactPy keeps track of which state belongs to which component based on their place in the UI tree. You can control when to preserve state and when to reset it between re-renders.

</p>

!!! summary "You will learn"

    -   How state is tied to a position in the tree
    -   When state is preserved, and when it resets
    -   How to reset a component's state on purpose, with position or with `#!python key`
    -   Why defining a component inside another one loses state

## State is tied to a position in the tree

When you give a component state, you might think the state "lives" inside the component. It doesn't. ReactPy holds the state, and associates each piece of it with a component by *where that component sits in the tree*.

Here `#!python counter()` is rendered at two different positions:

=== "app.py"

    ```python
    {% include "../../examples/preserving_and_resetting_state/two_positions/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/preserving_and_resetting_state/two_positions/styles.css" %}
    ```

=== ":material-play: Run"

Click both counters and notice they don't affect each other. Each position gets its own state, so `#!python counter()` is really two separate components here.

It makes no difference whether you build the child once and reuse it, or call it twice:

```python linenums="0"
one_counter = counter()
html.div(one_counter, one_counter)  # same as: html.div(counter(), counter())
```

Both render `#!python counter()` at two positions, and both get independent state.

## Same component at the same position preserves state

In this example a checkbox flips a prop on the counter, but there is always exactly one `#!python counter()` at that position:

=== "app.py"

    ```python
    {% include "../../examples/preserving_and_resetting_state/same_position/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/preserving_and_resetting_state/same_position/styles.css" %}
    ```

=== ":material-play: Run"

Raise the score, then toggle "Use fancy styling". **The score survives**, because the same component stayed at the same position — only its `#!python is_fancy` prop changed.

This is the default, and usually what you want.

## Different components at the same position reset state

Now switch the child to something else entirely:

=== "app.py"

    ```python
    {% include "../../examples/preserving_and_resetting_state/different_components/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/preserving_and_resetting_state/different_components/styles.css" %}
    ```

=== ":material-play: Run"

Raise the score, tick "Take a break", then untick it. The counter comes back at **zero**. Replacing the child with an `#!python html.p()` destroyed the old state, and the returning `#!python counter()` is a brand new one.

The rule so far: same component at the same position keeps state; anything else at that position does not.

## Resetting state at the same position

Suppose a scoreboard shows one player's score at a time, and "Next player" swaps Taylor for Sarah:

```python linenums="0"
counter("Taylor") if is_player_a else counter("Sarah")
```

Both branches call `#!python counter()` at the same position, so ReactPy sees one component whose `#!python person` prop changed — and the score follows the player over. That's wrong here: Taylor's score and Sarah's score are different things.

There are two ways to get them treated as separate components.

### Option 1: render them at different positions

Give each player a container that always exists:

=== "app.py"

    ```python
    {% include "../../examples/preserving_and_resetting_state/different_positions/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/preserving_and_resetting_state/different_positions/styles.css" %}
    ```

=== ":material-play: Run"

-   At first the first `#!python html.div()` holds Taylor's counter and the second is empty.
-   After "Next player!" the first is empty and the second holds Sarah's.

Each counter is destroyed when its container empties, so every switch starts from zero. This works nicely when there are only a couple of alternatives to lay out side by side.

!!! warning "An empty list expansion is not a placeholder"

    The tempting Python spelling of "or nothing" collapses the whole mechanism:

    ```python linenums="0"
    *([] if not is_player_a else [counter("Taylor")]),  # wrong: no child at all
    ```

    An empty expansion contributes **no children**, so the two counters land at position `#!python 0` and ReactPy treats them as one component — no reset, and Sarah inherits Taylor's score. It is the two `#!python html.div()` containers above that create the positions. (React avoids this because `#!js false` still occupies a JSX slot.)

### Option 2: reset state with a key

You have seen `#!python "key"` when [rendering lists.](./rendering-lists.md#keeping-list-items-in-order-with-key) Keys are not only for lists. By default ReactPy identifies a child by its index within its parent — "the first counter", "the second counter" — and a key lets you say *this is not the first counter, it is Taylor's counter*.

=== "app.py"

    ```python
    {% include "../../examples/preserving_and_resetting_state/reset_with_key/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/preserving_and_resetting_state/reset_with_key/styles.css" %}
    ```

=== ":material-play: Run"

The two counters no longer share state, even though they appear in the same place. Give `#!python "key"` a value that identifies *what* the component is — the contact id, the player name — not where it sits.

!!! info "Keys are only unique within their parent"

    Two components with the same key under **different** parents are fine: keys are not globally unique, they only identify a position within one parent.

    Note also that an unkeyed child is identified by its **index**, which shares a namespace with explicit keys. `#!python html.div(contact_list(...), chat(to, key=0))` raises `ValueError: Duplicate keys [0]`, because the unkeyed `#!python contact_list()` already occupies position `#!python 0`. Prefix your keys (`#!python key=f"chat-{to['id']}"`) or key all the siblings.

### Resetting a form with a key

Keying is most useful for forms. In this chat app, `#!python chat()` holds the half-written message:

=== "app.py"

    ```python
    {% include "../../examples/preserving_and_resetting_state/messenger/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/preserving_and_resetting_state/messenger/data.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/preserving_and_resetting_state/messenger/styles.css" %}
    ```

=== ":material-play: Run"

Type a draft, then pick another contact. Without the key the draft would follow you over, because `#!python chat()` never left its position. With `#!python key=f"chat-{to['id']}"` the draft belongs to the conversation rather than the slot.

### Keeping state for a component that is no longer rendered

Resetting is often *not* what you want — a real chat app should restore the draft when you go back to Alice. Keying does not do that: an unmounted component loses its state, so returning to Taylor starts at zero. Options:

-   Render **all** the chats and hide the inactive ones with CSS. Nothing is unmounted, so state survives. Great for small UIs, wasteful when the hidden trees are large.
-   [Lift the state up](./sharing-state-between-components.md) and keep each recipient's draft in the parent, in a dict keyed by recipient. Children coming and going stops mattering. This is the most common answer.
-   Keep it outside ReactPy entirely — a database, or `#!python localStorage` in the browser — which you want anyway if a draft should survive a page reload.

Whichever you choose, a chat *with Alice* is conceptually different from a chat *with Bob*, so it still deserves a distinct key.

## Nested component definitions reset state accidentally

This one bites quietly:

```python linenums="0"
@component
def outer():
    @component
    def nested():
        value, set_value = use_state(...)
        ...

    return html.div(nested())
```

Every render of `#!python outer()` creates a **new function object** for `#!python nested()`. A new function is a new component, so ReactPy discards the old state and mounts a fresh one on every render — your state resets itself, with no warning. Measured: a nested child's mount counter climbs by one on each parent render, while a module-level child mounted once.

Define components at module level, or pass data through props.

## Recap

-   ReactPy keeps state for as long as the same component is rendered at the same position.
-   State is not stored in the call that produced the VDOM; it belongs to the tree position you put it in.
-   Force a subtree to reset by rendering it at a different position, or by giving it a different `#!python "key"`.
-   Unkeyed siblings are identified by index, in the same key namespace as explicit keys — prefix your keys to avoid `ValueError: Duplicate keys`.
-   Don't define a component inside another component, or you'll reset state by accident.
