## Overview

<p class="intro" markdown>

`reactpy.html` is how you write markup in ReactPy. It is an object whose attributes are tag constructors: `#!python html.div(...)` builds a `#!python <div>`, and there is no template language, no JSX, and no parser involved.

</p>

```python linenums="0"
from reactpy import html

html.div({"class": "card"}, html.h2("Title"), html.p("Body"))
```

That call produces a plain `#!python dict`:

```python linenums="0"
{
    "children": [
        {"children": ["Title"], "tagName": "h2"},
        {"children": ["Body"], "tagName": "p"},
    ],
    "attributes": {"class": "card"},
    "tagName": "div",
}
```

`reactpy.h` is the same object under a shorter name — `#!python h is html` is `#!python True` — so use whichever reads better in a given file. Importing both and mixing them in one module buys nothing.

---

## Reference

### `html.<tag_name>(attributes, *children)` { #html-tag }

Every attribute of `#!python html` is a tag constructor. The common tags are declared for autocomplete, but **any** name works — see [Any name is a tag](#any-name-is-a-tag).

-   **First argument**: the attributes — but only when it is a **plain** `#!python dict`. A `#!python VdomDict`, or any dict subclass, is treated as a child instead. This single rule is the most common source of confusion, and it is worth internalizing:

    ```python linenums="0"
    html.div({"class": "card"}, html.p("Body"))  # dict -> attributes
    html.div(html.p("Body"))  # no dict -> no attributes
    html.div(None, html.p("Body"))  # None -> an explicit "no attributes"
    ```

    Leading `#!python None` is the conventional way to say "no attributes" and keep the arguments in a predictable shape. It renders nothing.

    !!! warning "A `#!python VdomDict` as the first argument is a child"
        `#!python VdomDict` is a `#!python dict` *subclass*, and the check is for the exact plain `#!python dict` type. So a `#!python VdomDict` is never mistaken for attributes — even when you meant it that way:

        ```python linenums="0"
        from reactpy.types import VdomDict

        html.div(VdomDict(tagName="span"))  # -> a <span> *child* of the div
        ```

-   **Remaining arguments**: children, of any type [Common Props](common-props.md#children) accepts — strings, numbers, `#!python None`, lists, dicts, components. Lists are flattened.

-   **Returns**: a `#!python VdomDict`. Tag constructors are cached, so `#!python html.div is html.div` — the same object every time. Nothing is rendered until a component returns it.

#### Caveats

-   **A plain `#!python dict` that is *meant* as an element can be read as attributes.** `#!python html.div({"children": ["x"]})` produces a div with an attribute literally named `#!python children`, not a child — because the first argument was a plain dict. When in doubt, pass the element as the second argument after `#!python None`.
-   **Void tags reject children.** `#!python html.br("x")` raises `#!python TypeError: 'br' nodes cannot have children.` See [Common Props](common-props.md#void-elements).
-   **Tags do not validate their own attributes.** `#!python html.img({"scr": "typo.png"})` is accepted and renders an image with no source. There is no prop-type check; a misspelled attribute name is a silent no-op.

### `html(*children)` — fragments { #fragments }

Calling `#!python html` itself is the fragment constructor: children with no wrapper element. See [Common Props](common-props.md#fragments) — a fragment accepts `#!python key` and nothing else.

---

## Usage

### Any name is a tag { #any-name-is-a-tag }

ReactPy does not keep a list of valid HTML tags. It converts the attribute name and sends it as the tag name, so you can reach tags the module has never declared:

| You write | You get |
| --- | --- |
| `#!python html.div` | `<div>` |
| `#!python html.data_table` | `<data-table>` |
| `#!python html.my_widget` | `<my-widget>` |
| `#!python html.del_` | `<del>` |
| `#!python html.class_` | `<class>` |

Two transformations: a trailing underscore is stripped (so you can name tags that are Python keywords, like `#!python del` and `#!python class`), and remaining underscores become dashes (so you can name custom elements and hyphenated tags that are not valid Python identifiers).

That makes custom elements first-class — no registration step, no wrapper component:

=== "app.py"

    ```python
    {% include "../../examples/reference_usage/custom_elements/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The `#!python <user-badge>` element reaches the browser as written. Whether it *does* anything is up to whatever defines it — a web component, an external script, or nothing at all. A tag the browser does not know renders as an unknown element: its children show up, its attributes are set, and it is laid out inline by default.

!!! tip "Prefer a component over a mystery tag"
    A custom tag is only worth it when something on the client implements it. For grouping your own markup, write a `@component` — it takes part in rendering, can hold state, and is checkable by a type checker.

### Tags versus components { #tags-versus-components }

Both are called the same way and both produce VDOM, and the difference is what happens next:

| | `#!python html.div(...)` | `#!python my_component(...)` |
| --- | --- | --- |
| Returns | A `#!python VdomDict`, immediately | A `#!python Component`, rendered later by the layout |
| Owns state | No | Yes — hooks belong to it |
| Re-rendered | Only when its parent returns a new value | When its state changes or its parent re-renders it |
| Defined with | Provided by `#!python html` | `@component` over a function |

The practical rule: a tag is for HTML elements, a component is for anything with behaviour. A `#!python <div>` that has to remember something is not a div any more — it is a component that returns a div. See [Your First Component](../learn/your-first-component.md).

### Nested and adjacent tags

Tags nest by call nesting, and read left-to-right, innermost first:

```python linenums="0"
html.p(html.em("emphasized"), " and ", html.strong("bold"))
```

Because Python evaluates arguments eagerly, the inner call completes before the outer one runs. There is no indentation-scope or closing-tag syntax to get wrong, and no unbalanced-tag error — the structure either parses or it does not.

The one habit to build is the leading `#!python None`. Without it, a first child that is a plain `#!python dict` is consumed as attributes:

```python linenums="0"
html.div({"tagName": "span"})  # attributes named "tagName" — not a child
html.div(None, {"tagName": "span"})  # a <span> child
```

A complete page reads like the HTML it produces:

=== "app.py"

    ```python
    {% include "../../examples/reference_usage/tags/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

### Lists of tags

A list comprehension produces children directly; give each one a `#!python key`:

```python linenums="0"
html.ul(None, [html.li({"key": word}, word) for word in words])
```

See [Rendering Lists](../learn/rendering-lists.md) for why the key matters, and [Common Props](common-props.md#keys) for where it lives in the dictionary.

### Classes and inline styles

`#!python class` and `#!python className` both work, and `#!python style` takes a `#!python dict`. Include units inside the strings — a bare number is applied by some executors and silently dropped by others:

```python linenums="0"
html.p({"class": "muted"}, "...")
html.p({"style": {"font-size": "12px", "color": "#666"}}, "...")
```

Details, including the executor difference, are in [Common Props](common-props.md#style).

### SVG { #svg }

SVG elements live under `#!python html.svg`, because their tag names collide with HTML ones (`#!python <title>`, `#!python <a>`, `#!python <style>`):

```python linenums="0"
html.svg(
    {"viewBox": "0 0 24 24", "width": "24"},
    html.svg.circle({"cx": "12", "cy": "12", "r": "10"}),
)
```

`#!python html.svg` is itself a tag constructor, and nested names follow the same rules — trailing underscore stripped, underscores to dashes. Camel-cased SVG names are used as written, so `#!python html.svg.clipPath` produces `#!python <clipPath>`.

!!! note "Names are not case-normalized"
    `#!python viewBox` works because the name is forwarded exactly. Write SVG attribute names the way the spec spells them, capitals included.

### Raw HTML { #raw-html }

There is no way to hand ReactPy a block of HTML and have it parsed into VDOM. To put a raw HTML string into the page, use `#!python dangerouslySetInnerHTML`:

```python linenums="0"
html.div({"dangerouslySetInnerHTML": {"__html": "<b>bold</b>"}})
```

Never pass untrusted input to it, and note that a `#!python dangerouslySetInnerHTML` attribute cannot be combined with children. See [Common Props](common-props.md#dangerouslysetinnerhtml).

### Inspecting what a tag produced

A tag call is a plain `#!python dict`, so print it:

```python linenums="0"
>>> from reactpy import html
>>> html.li({"key": "a"}, "Item")
{'children': ['Item'], 'attributes': {'key': 'a'}, 'tagName': 'li'}
```

Key order can differ, and empty keys are omitted — a tag with no attributes has no `#!python "attributes"` entry at all. To see what a *component* renders, drive it through `#!python reactpy.core.layout.Layout` rather than printing the component instance, which shows only its arguments.

### Script tags { #script-tags }

`#!python html.script` is special-cased. It rejects event handlers:

```python linenums="0"
html.script({"onLoad": handler})
```

```text linenums="0"
ValueError: 'script' elements do not support event handlers
```

and it infers its own `#!python key` from its content, falling back to `#!python src`, so the script is not re-run on every render:

```python linenums="0"
>>> html.script({"src": "/analytics.js"})
{'tagName': 'script', 'attributes': {'src': '/analytics.js', 'key': '/analytics.js'}}
```

Because the key drives re-execution, giving a script an explicit `#!python key` is how you make it run again on purpose. As with `#!python dangerouslySetInnerHTML`, keep untrusted data out of the body of a script.

---

## Troubleshooting

### The first argument became an attribute

If your element has an attribute named `#!python children` or `#!python tagName` and renders nothing, a plain `#!python dict` child was read as the attributes dict. Pass `#!python None` first.

### `TypeError: '<tag>' nodes cannot have children.`

You passed content to a void tag. Remove the children.

### `TypeError: Fragments cannot have attributes besides 'key'`

Give the fragment a real element, or move the attributes onto a child.

### An attribute has no effect

The name is forwarded verbatim and never validated, so a typo is invisible. Print the `#!python dict` and compare the key against what the browser expects. Only `#!python class`/`#!python className` and `#!python for`/`#!python htmlFor` have aliases; nothing else does.

### A numeric style does nothing

Add the unit to the string. See [Common Props](common-props.md#style).

---

## At a glance

### Tag names { #tag-names }

| You write | You get | Rule |
| --- | --- | --- |
| `#!python html.div` | `<div>` | as-is |
| `#!python html.data_table` | `<data-table>` | `_` → `-` |
| `#!python html.del_` | `<del>` | trailing `_` stripped |
| `#!python html.class_` | `<class>` | trailing `_` stripped |
| `#!python html.svg.clipPath` | `<clipPath>` | as-is, under `#!python svg` |

### Arguments { #arguments }

| Position | Type | Meaning |
| --- | --- | --- |
| first | plain `#!python dict` | attributes, or pass `#!python None` for none |
| first (otherwise) | any accepted child | a child |
| rest | any accepted child | children, flattened |

### Accepted children { #accepted-children }

| Child | Renders as |
| --- | --- |
| `#!python str` | text, verbatim |
| `#!python int` / `#!python float` | `#!python str(value)` |
| `#!python None` | nothing |
| `#!python True` / `#!python False` | the words `True` / `False` |
| `#!python list` / `#!python tuple` | flattened children |
| `#!python dict` | an element (needs `#!python "tagName"`) |
| `@component` instance | that component's output |

## Related

-   [Common Props](common-props.md) — the VDOM dictionary: attributes, `#!python style`, `#!python key`, event handlers, `#!python dangerouslySetInnerHTML`
-   [Your First Component](../learn/your-first-component.md) — components, and when to write one instead of a tag
-   [Rendering Lists](../learn/rendering-lists.md) — keys
-   [Responding to Events](../learn/responding-to-events.md) — `#!python onClick` and friends
-   [ReactPy](reactpy.md) — serving a component tree to a browser
