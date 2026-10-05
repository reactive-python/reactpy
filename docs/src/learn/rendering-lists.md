## Overview

<p class="intro" markdown>

You will often want to display multiple similar components from a collection of data. You can use Python's [list comprehensions](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions) to manipulate a list of data. On this page, you'll use comprehensions with ReactPy to filter and transform your data into lists of components.

</p>

!!! summary "You will learn"

    -   How to render components from a list using a comprehension
    -   How to render only specific components using a filtering condition
    -   When and why to use ReactPy keys

## Rendering data from lists

Say that you have a list of content.

```python linenums="0"
html.ul(
    html.li("Creola Katherine Johnson: mathematician"),
    html.li("Mario José Molina-Pasquel Henríquez: chemist"),
    html.li("Mohammad Abdus Salam: physicist"),
    html.li("Percy Lavon Julian: chemist"),
    html.li("Subrahmanyan Chandrasekhar: astrophysicist"),
)
```

The only difference among those list items is their contents, their data. You will often need to show several instances of the same component using different data when building interfaces: from lists of comments to galleries of profile images. In these situations, you can store that data in Python dictionaries and lists and use comprehensions to render lists of components from them.

Here's a short example of how to generate a list of items from a list:

1. **Move** the data into a list:

```python linenums="0"
people = [
    "Creola Katherine Johnson: mathematician",
    "Mario José Molina-Pasquel Henríquez: chemist",
    "Mohammad Abdus Salam: physicist",
    "Percy Lavon Julian: chemist",
    "Subrahmanyan Chandrasekhar: astrophysicist",
]
```

2. **Build** a new list of VDOM nodes from `#!python people`:

```python linenums="0"
list_items = [html.li(person) for person in people]
```

3. **Return** `#!python list_items` from your component wrapped in a `#!html <ul>`:

```python linenums="0"
return html.ul(list_items)
```

Here is the result:

=== "app.py"

    ```python
    {% include "../../examples/rendering_lists/from_array/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/rendering_lists/from_array/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

If you run this with `#!bash REACTPY_DEBUG=1`, ReactPy prints a warning for each child:

```text linenums="0"
Key not specified for child in list row(7f2c11ac75e0, person={...})
```

You'll learn how to fix this warning later on this page. Before we get to that, let's add some structure to your data.

## Filtering lists of items

This data can be structured even more. Rather than strings, each person becomes a dictionary:

```python linenums="0"
people = [
    {
        "id": 0,
        "name": "Creola Katherine Johnson",
        "profession": "mathematician",
        "accomplishment": "spaceflight calculations",
        "image_id": "MK3eW3A",
    },
    # ...
]
```

Say you want to display only the chemists. In JavaScript React you would chain `#!js filter()` and `#!js map()`; in Python a single comprehension with an `#!python if` clause does both:

```python linenums="0"
chemists = [person for person in people if person["profession"] == "chemist"]
list_items = [html.li(person["name"]) for person in chemists]
```

=== "app.py"

    ```python
    {% include "../../examples/rendering_lists/filtering/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/rendering_lists/filtering/data.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/rendering_lists/filtering/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

!!! warning "A helper that forgets `#!python return` renders nothing"

    The JavaScript "`=>` with a block body needs a `#!js return`" trap has a direct Python twin that is *worse*, because Python fails silently. If a helper used inside a comprehension forgets its `#!python return`, it evaluates to `#!python None` — and ReactPy skips `#!python None` children instead of raising:

    ```python linenums="0"
    def render_person(person):  # WRONG: no return
        html.li(person["name"])


    list_items = [render_person(person) for person in people]
    ```

    `#!python list_items` becomes a list of `#!python None` values and the `#!html <ul>` renders empty, with no error. Use a comprehension directly when the expression is simple, and add a `#!python -> VdomDict` return annotation to helpers so type checkers catch the omission.

## Keeping list items in order with `key`

When you render children from a list, ReactPy needs a way to tell which child is which. Give each item a `#!python key` — a string or a number that uniquely identifies it among the other items in that list. Unlike React, where `key` is a special JSX attribute, in ReactPy it lives in the **attributes dictionary** like any other attribute:

```python linenums="0"
html.li({"key": person["id"]}, ...)
```

!!! info "Children built from a list always need keys"

    Any child that comes out of a comprehension — or any other list — should carry a `#!python key`. ReactPy does not warn about this by default; the check is part of its debug mode, so run your app with `#!bash REACTPY_DEBUG=1` (or set `#!python reactpy.config.REACTPY_DEBUG.current = True`) while developing to surface them.

Keys tell ReactPy which list item each component corresponds to, so that it can match them up later. This becomes important if your list items can move (e.g. due to sorting), get inserted, or get deleted. A well-chosen `#!python key` helps ReactPy infer what exactly has happened, and make the correct updates to the DOM tree.

Rather than generating keys on the fly, you should include them in your data:

=== "app.py"

    ```python
    {% include "../../examples/rendering_lists/keyed/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/rendering_lists/keyed/data.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/rendering_lists/keyed/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

### Displaying several DOM nodes for each list item

What do you do when each item needs to render not one, but several DOM nodes?

A plain `#!python html(...)` fragment takes no positional attributes, but it does accept an attributes dictionary — so pass the key there:

```python linenums="0"
[
    html(
        {"key": person["id"]},
        html.h1(person["name"]),
        html.p(person["profession"]),
    )
    for person in people
]
```

=== "app.py"

    ```python
    {% include "../../examples/rendering_lists/fragments/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/rendering_lists/fragments/data.py" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Fragments disappear from the DOM, so this produces a flat list of `#!html <h1>`, `#!html <p>`, `#!html <h1>`, `#!html <p>`, and so on.

### Where to get your `key`

Different sources of data provide different sources of keys:

-   **Data from a database:** If your data is coming from a database, you can use the database keys/IDs, which are unique by nature.
-   **Locally generated data:** If your data is generated and persisted locally (e.g. notes in a note-taking app), use an incrementing counter from [`itertools.count`](https://docs.python.org/3/library/itertools.html#itertools.count) or a UUID from [`uuid.uuid4`](https://docs.python.org/3/library/uuid.html#uuid.uuid4) when *creating* the item — never while rendering.

### Rules of keys

-   **Keys must be unique among siblings.** However, it's okay to use the same keys for nodes in _different_ lists.
-   **Keys must not change** or that defeats their purpose! Don't generate them while rendering.

!!! warning "Duplicate keys are a hard error in ReactPy"

    React logs a warning for duplicate keys and carries on. ReactPy raises instead:

    ```text linenums="0"
    ValueError: Duplicate keys [1] at '/children/0'
    ```

    The whole component fails to render, so a data set with repeated IDs takes down the section rather than degrading it. If your data can legitimately repeat — for example, two rows that render the same underlying record — make the key unique among siblings by combining the fields that distinguish them.

### Why does ReactPy need keys?

Imagine that files on your desktop didn't have names. Instead, you'd refer to them by their order — the first file, the second file, and so on. You could get used to it, but once you delete a file, it would get confusing. The second file would become the first file, the third file would be the second file, and so on.

File names in a folder and keys in a list serve a similar purpose. They let us uniquely identify an item between its siblings. A well-chosen key provides more information than the position within the list. Even if the _position_ changes due to reordering, the `#!python key` lets ReactPy identify the item throughout its lifetime.

This is observable. Give each row its own `#!python use_state` seeded from the person it renders, then reverse the list. With keys, every row's state travels with its person. Without keys, the state stays behind in the old slot:

```text linenums="0"
keyed=True
   before: shown=ada   state=ada#0
   after : shown=alan  state=alan#2

keyed=False
   before: shown=ada   state=ada#0
   after : shown=alan  state=ada#0    # the row for "alan" inherited ada's state
```

!!! warning "Index-based keys are a trap"

    You might be tempted to use an item's index in the list as its key. In fact, that's effectively what ReactPy uses if you don't specify a `#!python key` at all. But the order in which you render items will change over time if an item is inserted, deleted, or if the list gets reordered, and — as the output above shows — state then attaches to the wrong item.

    Similarly, do not generate keys on the fly, e.g. with `#!python key=uuid.uuid4()` or `#!python key=id(person)` inside the render. Keys that differ on every render never match up, so every component and DOM node is recreated each time. Not only is this slow, it will also lose any user input inside the list items. Instead, use a stable ID that comes from the data.

    Note that your component never receives `#!python key` as a prop — ReactPy reserves it. Declaring a `#!python key` parameter raises immediately:

    ```text linenums="0"
    TypeError: Component render function <function row ...> uses reserved parameter 'key'
    ```

    If your component needs an ID, pass it as a separate prop: `#!python profile(id=id, key=id)`.

!!! info "Pass a list, not a generator"

    `#!python html.ul(html.li(person) for person in people)` renders, but a generator has no length, so ReactPy cannot verify key integrity and warns about it in debug mode. Bracket the comprehension so the children are a real list: `#!python html.ul([html.li(person) for person in people])`.

## Recap

On this page you learned:

-   How to move data out of components and into data structures like lists and dictionaries.
-   How to generate sets of similar components with a list comprehension.
-   How to create filtered lists with an `#!python if` clause in a comprehension.
-   Why and how to set `#!python key` on each component in a collection so ReactPy can keep track of each of them even if their position or data changes.
-   That ReactPy checks keys only in debug mode, treats duplicate keys as an error, and reserves `#!python key` so components can never receive it as a prop.
