## Overview

<p class="intro" markdown>

ReactPy's UI is a plain dictionary. Two functions move it across the boundary to and from ordinary HTML text: `#!python reactpy_to_string()` renders a VDOM dictionary or a component to an HTML string, and `#!python string_to_reactpy()` parses an HTML string into a VDOM dictionary. Both live at the top of the package, and both are load-bearing inside ReactPy itself — the executors build the initial document and the PyScript head with them.

</p>

!!! summary "You will learn"

    -   How to turn VDOM into an HTML string, and what that conversion throws away
    -   How to parse HTML text into a VDOM dictionary, and the renames it performs on the way in
    -   Why `#!python className` survives parsing but not serialization
    -   When to reach for `#!python string_to_reactpy()` instead of writing `#!python html.*` calls

## The two functions

| Function | In | Out | Raises on bad input |
| --- | --- | --- | --- |
| `#!python reactpy_to_string(root)` | `#!python VdomDict` or a called `#!python Component` | `#!python str` of HTML | `#!python TypeError` on a callable attribute |
| `#!python string_to_reactpy(html, *transforms, strict=True, intercept_links=True)` | `#!python str` of HTML | `#!python VdomDict` | `#!python HTMLParseError`, `#!python ValueError`, `#!python TypeError` |

Both are exported from the package root:

```python linenums="0"
from reactpy import reactpy_to_string, string_to_reactpy
```

Neither is a serializer for the wire. The socket protocol has its own shape, described in [Protocol Structure](../reference/protocol-structure.md); these two functions exist so you can hand ReactPy's output to something that speaks HTML, and hand HTML from somewhere else to ReactPy.

## VDOM to HTML: `reactpy_to_string()`

Give it an element, or a component that has already been called:

=== "app.py"

    ```python
    {% include "../../examples/convert_between_vdom_and_html/reactpy_to_string_demo.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

There is no formatting option, no `#!python indent`, no doctype. You get the tags and the attributes and nothing else.

### What it renders

`#!python reactpy_to_string()` walks `#!python tagName`, `#!python attributes`, and `#!python children` (`utils.py`, `_add_vdom_to_etree`). Everything else in the dictionary is ignored:

-   **Event handlers disappear.** A `#!python {"onClick": handler}` produces no attribute at all. The value is a Python function; there is nothing sensible to write into HTML text.
-   **Inline JavaScript disappears too.** `#!python inlineJavaScript` is not consulted, so `#!python reactpy_to_string(html.button({"onClick": "this.innerText = 1"}, "x"))` returns `#!python <button>x</button>` with the script gone.
-   **An `#!python importSource` disappears.** A web-module component renders as its bare tag name, which no browser knows what to do with.
-   **A component child is rendered one level deep.** `#!python _add_vdom_to_etree` calls `#!python component_to_vdom()` on any child with a `#!python .render` attribute, recursively, so nested components come out as HTML.

That list is why this function cannot render your average app. It has no `#!python Layout`, so there is no hook stack: `#!python use_state`, `#!python use_ref`, `#!python use_effect`, `#!python use_location` all raise `#!python RuntimeError: No life cycle hook is active. Are you rendering in a layout?` **Only hook-free components and plain `#!python html.*` elements convert.** This is the same path `#!python ReactPy(prepend_body=...)` uses, which is why that argument takes an element and not a stateful component.

!!! warning "Passing an uncalled component raises `AttributeError`"

    `#!python reactpy_to_string(my_component)` fails with `#!python AttributeError: 'function' object has no attribute 'render'` — the decorator has not run, so there is nothing to render. Call it: `#!python reactpy_to_string(my_component())`.

### Attribute names are lowercased

This is the sharpest edge on the page, and it is silent. On the way out, every attribute name goes through `#!python .lower()` (`utils.py`, `_react_attribute_to_html`), with the exception of `#!python data-*` and `#!python aria-*`, which are left exactly as you wrote them:

=== "app.py"

    ```python
    {% include "../../examples/convert_between_vdom_and_html/round_trip_case.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

`#!python htmlFor` becomes `#!python htmlfor` and `#!python className` becomes `#!python classname` — neither of which is a real HTML attribute, so the browser ignores both. The label stops labelling and the class stops styling, with no error anywhere.

**Write the HTML name when the string is the destination.** `#!python {"for": "email"}` and `#!python {"class": "card"}` produce correct markup; `#!python {"htmlFor": ...}` and `#!python {"className": ...}` do not. There is no single spelling that satisfies both this and live rendering — see [Common Props](../reference/common-props.md) for why `#!python className` is what the browser-side path wants.

The one attribute ReactPy does translate is `#!python style`, which it flattens from a dict into a `#!python key:value;` string and kebab-cases on the way:

```python linenums="0"
reactpy_to_string(html.div({"style": {"fontSize": "20px", "zIndex": 3}}, "s"))
# <div style="font-size:20px;z-index:3">s</div>
```

Note what did **not** happen to the `#!python 3`: no unit is inferred. `#!python z-index:3` is fine because it takes no unit, but `#!python font-size:30` would be invalid CSS where the browser-side renderer would have applied it as `#!python 30px`. Always put the unit in the string.

!!! warning "Some boolean attributes obey lxml, not HTML"

    ReactPy renders the string through `#!python lxml`, which carries its own list of known boolean attributes. For a name on that list the value is discarded and only presence matters — so `#!python False` still emits the attribute:

    === "app.py"

        ```python
        {% include "../../examples/convert_between_vdom_and_html/boolean_attributes.py" start="# start" end="# end" %}
        ```

    === ":material-play: Run"

        ```python
        # TODO
        ```

    `#!python checked` renders as `#!html <input type="checkbox" checked>` even though you said `#!python False`. Names outside that list get `#!python str(value)` instead, which leaks the word `#!python False` into your markup as in `#!html <div hidden="False">`. Which names fall in which group depends on your `#!python lxml` build, so test the attribute you care about. The safe form for a server-rendered string is to omit the key entirely rather than set it to `#!python False`.

## HTML to VDOM: `string_to_reactpy()`

=== "app.py"

    ```python
    {% include "../../examples/convert_between_vdom_and_html/string_to_reactpy_demo.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Parsing is done by `#!python lxml.html`, then each node is rebuilt through the normal `#!python html.*` constructors (`utils.py`, `_etree_to_vdom`), which means what comes back is a genuine `#!python VdomDict` you can render, patch, and send over the socket.

### What parsing renames and rewrites

The parser does not give you a mirror of the input. It runs a table of renames and a handful of node rewrites (`transforms.py`, `attributes_to_reactjs` and `RequiredTransforms`):

| In the HTML | In the VDOM | Why |
| --- | --- | --- |
| `#!html class="card"` | `#!python {"className": "card"}` | React-style prop name |
| `#!html for="email"` | `#!python {"htmlFor": "email"}` | React-style prop name |
| `#!html checked` | `#!python {"defaultChecked": ...}` | Controlled-vs-uncontrolled |
| `#!html accept-charset` | `#!python {"acceptCharset": ...}` | React-style prop name |
| `#!html http-equiv` | `#!python {"httpEquiv": ...}` | React-style prop name |
| `#!html style="font-size:20px"` | `#!python {"style": {"fontSize": "20px"}}` | Style strings become dicts |
| `#!html <input value="ab">` | `#!python {"defaultValue": "ab"}` | A `#!python value` prop makes an input controlled |
| `#!html <textarea>hi</textarea>` | `#!python {"defaultValue": "hi"}`, no children | Same reason |
| `#!html <option selected>` | `#!python defaultValue` on the parent `#!html <select>` | React puts the selection on the parent |
| `#!html <a href="/x">` | an `#!python onClick` handler with `#!python prevent_default` | Keeps a client router in charge |
| `#!html <div id="uniq">` | `#!python {"id": "uniq", "key": "uniq"}` | A key is inferred from `#!python id`, then `#!python name` |

The last two deserve a second look, because they change behaviour rather than spelling.

**Every anchor gets a click handler.** By default `#!python intercept_links=True` installs a `#!python preventDefault`-only `#!python onClick` on every `#!html <a>` (`transforms.py`, `intercept_link_clicks`). The link looks dead: clicking it does nothing, because ReactPy has no router to hand the navigation to. Pass `#!python intercept_links=False` to keep real links.

**An `#!python id` becomes a `#!python key`.** `#!python infer_key_from_attributes` copies `#!python id` — or `#!python name` on `#!html <input>`, `#!html <select>`, `#!html <textarea>` — into `#!python attributes["key"]`. That is usually what you want, since a stable `#!python id` is a stable identity, but it also means two elements parsed with the same `#!python id` collide: the layout rejects them with `#!python ValueError: Duplicate keys [...]`.

!!! warning "Whitespace you did not ask for"

    `#!python lxml` is configured to drop comments, processing instructions, and *blank text* — but `remove_blank_text` only removes whitespace that is purely formatting. The newline and indentation between tags in a pretty-printed document survive as text children:

    ```python linenums="0"
    string_to_reactpy("<ul>\n  <li>a</li>\n  <li>b</li>\n</ul>")["children"]
    # [{'tagName': 'li', 'children': ['a']}, '\n  ', {'tagName': 'li', 'children': ['b']}, '\n']
    ```

    Those strings render as visible whitespace. If you parse an indented template literal, expect stray spaces and newlines in the layout — write the markup flat, or strip the text children in a transform.

### Errors, and when to turn strictness off

`#!python string_to_reactpy()` raises in four distinct ways:

```python linenums="0"
string_to_reactpy(12)          # TypeError: Expected html to be a string, not int
string_to_reactpy("no tags here")  # ValueError: Expected html string to contain HTML tags, but no tags were found.
string_to_reactpy("<div <p>x</p>")  # HTMLParseError (a subclass of lxml.LxmlSyntaxError)
string_to_reactpy("<div <p>x</p>", strict=False)  # parses; '<p' becomes an attribute name
```

`#!python strict=True` reaches `#!python lxml` as `#!python recover=False`, so a document `#!python lxml` refuses to parse cleanly becomes an `#!python HTMLParseError` whose message tells you to turn strictness off. Do that deliberately: recovery invents attribute names out of the malformed text rather than complaining, so you trade a loud failure for a quietly wrong model.

A few things you might expect `#!python strict` to catch, and it does not:

-   Unclosed or mismatched tags — `#!html <div><span>x</div>` parses fine and the `#!html span` is closed for you.
-   Orphan fragments — `#!html <td>orphan</td>` and `#!html <li>x</li>` parse into bare `#!python td`/`#!python li` models, which then render somewhere HTML forbids them.
-   Unknown entities — `#!html &notreal;` becomes the literal text `#!python ¬real;`.

### Wrapping, empty input, and multiple roots

`#!python lxml` wants a single well-formed root, so it adds one for you:

-   `#!html <p>a</p><p>b</p>` comes back wrapped in a `#!python div`.
-   `#!html <body>hi</body>` comes back as a `#!python span`, not a `#!python body` — `#!python lxml.html`'s document scaffolding leaks through.
-   `#!html <meta http-equiv="refresh">` is likewise pulled into an `#!python html`/`#!python head` pair.
-   Empty or whitespace-only input returns `#!python {"tagName": ""}` — a fragment, not an error.

Do not write code that indexes `#!python children` by position on parsed input; the wrapper is `#!python lxml`'s decision, not yours.

## Transforming every node: the `*transforms` argument

`#!python string_to_reactpy()` takes any number of one-argument callables and applies each to every node after parsing (`utils.py`, `_etree_to_vdom`). This is the supported way to post-process the model rather than editing it after the fact:

```python linenums="0"
def add_card_class(vdom):
    if vdom["tagName"] == "div":
        vdom.setdefault("attributes", {})["className"] = "card"
    return vdom


string_to_reactpy("<div>x</div>", add_card_class)
# {'tagName': 'div', 'attributes': {'className': 'card'}, 'children': ['x']}
```

Mutate and return the same dictionary; the return value replaces the node, assigned unconditionally (`utils.py`, `_etree_to_vdom`). A transform that returns `#!python None` deletes the node — for a child it leaves `#!python None` in `#!python children`, for the root it makes `#!python string_to_reactpy()` itself return `#!python None`. Always return the model.

Transforms run **after** the built-in ones, so a `#!python style` value is already a dict by the time yours sees it, and an `#!html <a>` already has its `#!python onClick`. Use this hook to strip attributes you do not trust from third-party HTML — but note that removing an attribute is not the same as making untrusted HTML safe:

!!! warning "Never parse untrusted HTML without filtering"

    `#!python string_to_reactpy()` does not sanitize. An `#!html <img src=x onerror=...>` comes back as an attribute, and an `#!html <script>` comes back as a `#!python script` element with its content intact. ReactPy's own `#!python html.script` refuses event handlers and injects an inferred `#!python key`, but it does not inspect the JavaScript inside. If the string came from a user, run it through a sanitizer first and pass `#!python intercept_links=False` only once you have decided links are wanted.

## Using the result in a component

A parsed model is an ordinary element, so a component can return it directly:

=== "app.py"

    ```python
    {% include "../../examples/convert_between_vdom_and_html/component_from_string.py" start="# start" end="# end" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

That is exactly how ReactPy builds its own document head: `#!python ReactPy(pyscript_setup=True)` parses a block of PyScript markup with `#!python string_to_reactpy()` and splices it into `#!python html_head` (`executors/asgi/standalone.py`).

!!! warning "Do not parse inside the render body"

    The parse is a full `#!python lxml` document build, and it runs on the server on every render. Parse once at module level and return the stored model, or memoize it with `#!python use_memo`. Re-parsing per render is pure waste, and if you put the model in state you also hand yourself the mutation hazard covered in [VDOM Mutations](./vdom-mutations.md).

## Choosing a direction

Reach for these when the HTML exists somewhere other than in your Python code:

-   **`#!python string_to_reactpy()`** when markup arrives from a CMS, a markdown renderer, an email body, or a template you do not control. It is also the shortest path to pasting a snippet of HTML from a design mock into a component.
-   **`#!python reactpy_to_string()`** when you must hand ReactPy's output to something that is not the ReactPy client: server-rendered `#!html <head>` content, an `#!html <noscript>` fallback, an email or PDF generator, a test assertion.

If the markup is yours to write, write `#!python html.*` calls. The constructors validate at the call site, keep their arguments JSON-serializable, and support handlers — none of which the string path gives you.

## Summary

-   `#!python reactpy_to_string()` takes a `#!python VdomDict` or a called component and returns HTML text; it drops event handlers, inline JavaScript, and import sources, and can only render components that use no hooks.
-   It lowercases every attribute name except `#!python data-*` and `#!python aria-*`, so write `#!python "class"` and `#!python "for"` when the string is the destination.
-   `#!python string_to_reactpy()` parses HTML into a real `#!python VdomDict`, renaming to React-style prop names, converting `#!python style` strings to dicts, and moving `#!python value`/`#!html <textarea>` content to `#!python defaultValue`.
-   It intercepts link clicks and infers a `#!python key` from `#!python id` unless you tell it not to.
-   `#!python strict=False` turns a loud `#!python HTMLParseError` into a guessed model; `#!python lxml` never complained about unclosed tags anyway.
-   Neither function is the wire format — that is [Protocol Structure](../reference/protocol-structure.md).

## Related

-   [Creating HTML Tags](./creating-html-tags.md) — building the same models with `#!python html` and `#!python Vdom`
-   [VDOM Mutations](./vdom-mutations.md) — what you may and may not do to a model after you get one
-   [Creating VDOM Event Handlers](./creating-vdom-event-handlers.md) — the `#!python eventHandlers` slot these functions ignore
-   [Common Props](../reference/common-props.md) — attribute naming on the live rendering path
-   [Protocol Structure](../reference/protocol-structure.md) — what actually goes over the socket
