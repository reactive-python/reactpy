## Overview

<p class="intro" markdown>

Every element you write in ReactPy is a function call that returns a dictionary. `#!python html.div(...)` is not a keyword, a macro, or a parser — it is an attribute lookup that manufactures a constructor on first use, and a `#!python __call__` that assembles the model. Knowing how that works explains why there is no allow-list to fight, why `#!python html.del_` means `#!html <del>`, and where the handful of hard errors come from.

</p>

!!! summary "You will learn"

    -   How `#!python html` turns an attribute name into a tag name
    -   The rule that decides whether your first argument is attributes or a child
    -   Which elements reject children, and why `#!python html.script` is stricter still
    -   How to build fragments, SVG, and tag names that are not valid Python identifiers

## `html` manufactures tags on demand

`#!python html` is an instance of `#!python HtmlConstructor` with a single `#!python __getattr__` (`_html.py`). Ask it for anything and you get a `#!python Vdom` constructor back, cached by name:

=== "app.py"

    ```python
    {% include "../../examples/creating_html_tags/any_tag_name.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

There is **no allow-list.** ReactPy does not know or care whether `#!html <definitely-not-a-real-tag>` exists; the string travels to the browser and the browser decides. The names spelled out on `#!python HtmlConstructor` exist only so your editor can autocomplete them — the comment in the source says as much. Two practical consequences:

-   A misspelled tag renders as an unknown element with your text inside it, silently. Nothing in ReactPy will tell you that `#!python html.hdeader` is wrong.
-   Custom elements work with no ceremony: `#!python html.my_widget(...)` produces `#!python {"tagName": "my-widget"}` and the browser hands it to whatever registered that name.

### The underscore rules

`#!python __getattr__` applies exactly two transformations — `#!python value.rstrip("_").replace("_", "-")` — which is how you write names Python will not let you spell:

=== "app.py"

    ```python
    {% include "../../examples/creating_html_tags/tag_name_translation.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Read the rules literally, because they are applied blindly:

| You write | Tag name | Rule |
| --- | --- | --- |
| `#!python html.del_` | `#!python del` | trailing `#!python _` stripped (a keyword) |
| `#!python html.data_table` | `#!python data-table` | every `#!python _` becomes `#!python -` |
| `#!python html.my_widget` | `#!python my-widget` | same |
| `#!python html.h1` | `#!python h1` | no underscore, nothing changes |
| `#!python html._private` | `#!python -private` | leading underscore is *not* special |
| `#!python html.a__b` | `#!python a--b` | doubles are not collapsed |

Casing is passed through untouched, so `#!python html.myWidget` gives you `#!python myWidget`. Because translation happens *before* the cache lookup, `#!python html.data_table is html.data_table` holds — but two spellings that translate to the same tag are the same object, and two that do not are different elements.

If a name cannot be written as an attribute at all — a leading digit, or one you are building from a variable — construct it directly:

```python linenums="0"
from reactpy import Vdom

tag = Vdom("2fa-code")
tag("123456")  # {'tagName': '2fa-code', 'children': ['123456']}
```

`#!python Vdom(tag_name, /, allow_children=True, custom_constructor=None, import_source=None)` is the same class every `#!python html.*` name is built from, so you get identical behaviour. It is exported from the package root. Reach for it only for generated or unspellable names; anything else should go through `#!python html` so it reads consistently.

!!! warning "`#!python html` is not a namespace of plain functions"

    `#!python html.div` is a `#!python Vdom` *object*, not a function — `#!python html.div("x")` works because `#!python Vdom.__call__` is the constructor. So `#!python html.div.__name__` is the tag name rather than a qualified name, and any name you ask for is fair game: `#!python html.allow_children("x")` returns a perfectly valid `#!python {"tagName": "allow-children"}` element rather than tripping over the `#!python Vdom` attribute of the same name.

## The two call shapes

`#!python Vdom.__call__` accepts either children only, or an attribute dictionary followed by children (`core/vdom.py`, `Vdom.__call__`):

=== "app.py"

    ```python
    {% include "../../examples/creating_html_tags/two_call_shapes.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The discriminator is exact-type, not `#!python isinstance`: `#!python type(values[0]) is dict` (`core/vdom.py`, `separate_attributes_and_children`). Two consequences that bite:

-   A `#!python VdomDict` — which *is* a `#!python dict` subclass — in first position is treated as a **child**, which is what you want when nesting models you built earlier.
-   Any other `#!python dict` subclass in first position is also a child, so a custom mapping you meant as attributes becomes a rendered object instead. Pass a plain `#!python dict` literal for attributes.

A `#!python dict` in any *later* position is always a child. There is one slot for attributes and it is the first.

### Attribute values are forwarded verbatim

ReactPy renames nothing. `#!python className`, `#!python class`, `#!python htmlFor`, and `#!python for` all reach the DOM as whichever string you typed, and unknown names like `#!python data-*` and `#!python aria-*` pass straight through. Nothing validates names against a list, so a typo is a silent no-op — `#!python {"class_name": "card"}` renders `#!html <div class_name="card">`, an attribute nobody reads.

There are no exceptions to this rule on the live path. `#!python class_name` is not a thing. See [Common Props](../reference/common-props.md) for the full picture, including the one case where numeric `#!python style` values behave differently between executors.

!!! warning "Attributes must be JSON-serializable, but you may not be told"

    Everything in the attribute dict is JSON-encoded on its way to the browser. ReactPy checks that with `#!python json.dumps` only when `#!python REACTPY_CHECK_JSON_ATTRS` is on — and that option's parent is `#!python REACTPY_DEBUG`, so turning debug on turns this on too:

    ```python linenums="0"
    from reactpy import config

    config.REACTPY_DEBUG.current = True
    ```

    With the check on, `#!python html.div({"data": object()})` raises `#!python TypeError: Object of type object is not JSON serializable` **at the tag call**, pointing at your line. With it off, the model is accepted and the failure surfaces much later, inside the websocket send, as an `#!python orjson` error in a server log. If a page renders nothing and the browser console is empty, this is why.

## Fragments

`#!python html.fragment(...)` and the shorter `#!python html(...)` build a child list with no element of its own — `#!python tagName` is the empty string, and the client renders it as nothing:

=== "app.py"

    ```python
    {% include "../../examples/creating_html_tags/fragments.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

A fragment accepts `#!python key` and nothing else: a `#!python className`, a `#!python style`, or an event handler all raise `#!python TypeError: Fragments cannot have attributes besides 'key'`. There is no node to put them on, so ReactPy refuses rather than dropping them quietly.

Use a fragment when a component must return siblings and a wrapper `#!html <div>` would break the layout or the CSS. When the children are already in a list, pass the list — you do not need a fragment for that, though you do need keys, covered in [Rendering Lists](./rendering-lists.md).

## Void elements

`#!python html.br("x")` is a hard error, not a warning that scrolls past:

=== "app.py"

    ```python
    {% include "../../examples/creating_html_tags/void_and_script.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The rejecting set is `#!python NO_CHILDREN_ALLOWED_HTML_BODY` (`_html.py`): `#!python area`, `#!python base`, `#!python br`, `#!python col`, `#!python command`, `#!python embed`, `#!python hr`, `#!python img`, `#!python input`, `#!python iframe`, `#!python keygen`, `#!python link`, `#!python meta`, `#!python param`, `#!python portal`, `#!python source`, `#!python track`, `#!python wbr`. The check happens after the model is built, so the message names the tag rather than your mistake — read the name in the error.

`#!python iframe` is on that list, which surprises people who put fallback content inside one. ReactPy will not let you, and the browser-side renderer would not have shown it anyway.

## `html.script` is its own thing

`#!python html.script` uses a custom constructor (`_html.py`, `_script`) with three rules and a side effect:

-   **At most one child**, and it must be a `#!python str` — `#!python ValueError: 'script' nodes may have, at most, one child.` and `#!python The child of a 'script' must be a string.`
-   **No event handlers at all** — `#!python ValueError: 'script' elements do not support event handlers`. Attach behaviour to a sibling element instead, or use the inline-JavaScript handler form on a normal tag ([Creating VDOM Event Handlers](./creating-vdom-event-handlers.md)).
-   **A `#!python key` is injected** from the script's content, or from its `#!python src` if it has no content. Upstream documents the purpose as allowing the script "to be run multiple times if its key changes", browser permitting. Pass your own `#!python key` to control re-execution yourself.

!!! warning "Scripts are an injection surface"

    The child string reaches the browser as JavaScript. Never interpolate untrusted text into it — ReactPy's own docstring on `#!python _script` says so, and there is no escaping step to save you. Build the string from your own constants, or pass a `#!python src` you control.

## SVG is a second constructor

`#!python html.svg` is a separate `#!python SvgConstructor`, so SVG element names live in their own namespace and cannot collide with HTML names. Children come off it:

=== "app.py"

    ```python
    {% include "../../examples/creating_html_tags/svg.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

It has its own void set (`#!python NO_CHILDREN_ALLOWED_SVG`), and that set is broader and less intuitive than the HTML one — it includes `#!python text`, `#!python tspan`, `#!python title`, `#!python desc`, `#!python path`, `#!python use`, and `#!python foreignObject`. So the element you most need children inside is exactly the one that rejects them:

```python linenums="0"
html.svg.text("hello")  # TypeError: 'text' nodes cannot have children.
```

Build those nodes with `#!python Vdom`, which shares all the behaviour minus the void check:

```python linenums="0"
from reactpy import Vdom

Vdom("text")("hello")  # {'tagName': 'text', 'children': ['hello']}
```

The bundled client creates every element through `#!js document.createElementNS(namespace, ...)`, picking the namespace from the tag name: `#!python "svg"` gets `http://www.w3.org/2000/svg`, `#!python "math"` gets the MathML URI, everything else the XHTML one. That logic lives in the preact runtime ReactPy bundles into its client chunks, not in ReactPy's own `#!js @reactpy/client` source — so grep there for `createElementNS` and you will find nothing. Inside the SVG namespace attribute names are forwarded verbatim rather than lower-cased, so `#!python viewBox` keeps its capital `#!python B` — write it that way, since `#!python viewbox` is a different attribute to the DOM.

## Choosing children over attributes

`#!python html.div({"children": ["a", "b"]})` does not do what it looks like. The dict is attributes, so you get an attribute literally named `#!python children` and no children at all. Children are always positional arguments after the attribute dict — that is the only way to supply them:

```python linenums="0"
html.div({"id": "list"}, html.li("one"), html.li("two"))   # correct
html.ul({"children": [html.li("one")]})                     # an attribute named children
```

Children are flattened fully, not one level at a time, for any iterable that is not a string or a mapping — `core/vdom.py`, `#!python _flatten_children` recurses, and verified `#!python html.div([[["a"], "b"]])` yields `#!python children: ['a', 'b']`. A list or tuple comprehension therefore works at any nesting depth, and `#!python None` is skipped by the layout. Two rules from there are worth internalizing now, because both failures are quiet:

-   **Elements inside a list need keys**, in debug mode, or you get `#!python Key not specified for child in list ...`.
-   **A generator in place of a list skips that check entirely**, with `#!python Did not verify key-path integrity of children in generator ...`. Pass a `#!python list`. The deeper hazard — storing an iterator in state — is covered in [Rendering Lists](./rendering-lists.md).

## Summary

-   `#!python html` invents a tag for any attribute name; the two rules are trailing `#!python _` stripped and every `#!python _` turned into `#!python -`. There is no allow-list and no warning for a typo.
-   The first argument is attributes only if it is exactly a `#!python dict`; everything else, including `#!python VdomDict` and `#!python dict` subclasses, is a child.
-   Attribute names are forwarded verbatim — use the DOM's spelling. Turn on `#!python REACTPY_DEBUG` to catch un-serializable attribute values at the call site.
-   `#!python html.fragment` and `#!python html()` take only a `#!python key`.
-   The void elements in `#!python NO_CHILDREN_ALLOWED_HTML_BODY` reject children with a `#!python TypeError`; `#!python html.script` additionally allows one string child, forbids handlers, and infers its own `#!python key`.
-   `#!python html.svg.*` uses a broader void set that includes `#!python text`; build those with `#!python Vdom`.
-   `#!python Vdom(tag_name)` is the class behind every `#!python html.*` name — use it for tag names you cannot spell as an attribute, and for the SVG nodes `#!python html.svg` rejects.

## Related

-   [Common Props](../reference/common-props.md) — attribute naming, `#!python style`, and the executor differences
-   [Creating VDOM Event Handlers](./creating-vdom-event-handlers.md) — the `#!python eventHandlers` half of the model
-   [VDOM Mutations](./vdom-mutations.md) — editing a model after you built it
-   [Conditional Rendering](./conditional-rendering.md) and [Rendering Lists](./rendering-lists.md) — the child rules with their failure modes
-   [Convert Between VDOM and HTML](./convert-between-vdom-and-html.md) — the same models as text, and what that loses
