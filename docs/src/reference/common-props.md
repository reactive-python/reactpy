## Overview

<p class="intro" markdown>

Every element a ReactPy component renders is a plain `dict` with a fixed set of keys, and the attributes you pass to a tag end up on the DOM node nearly untouched. This page is the reference for what you may put in there — and for the handful of places ReactPy behaves differently from React.

</p>

```python linenums="0"
{
    "tagName": "div",
    "children": [...],
    "attributes": {...},
    "eventHandlers": {...},
    "inlineJavaScript": {...},
    "importSource": {...},
}
```

Only `#!python "tagName"` is required. You almost never write this by hand — `reactpy.html` builds it for you — but everything below is what a tag call can carry.

---

## Attributes

An attribute is any key/value pair in the first argument to a tag:

```python linenums="0"
html.input({"type": "search", "placeholder": "Filter", "autoFocus": True})
```

ReactPy forwards the name **and** the value to the browser verbatim. There is no translation layer, which is the main difference from React, where JSX rewrites props before they reach the DOM.

The value must be JSON-serializable, because the model is sent to the browser as JSON. Nothing stops you from putting something else in there: with debug mode off, the value is accepted at the tag call and only fails when the layout tries to send the model, deep inside the connection:

```text linenums="0"
TypeError: Type is not JSON serializable: object
```

Run with `#!bash REACTPY_DEBUG=1` and the same mistake fails at the tag call, where you can see which element caused it:

```text linenums="0"
TypeError: Object of type object is not JSON serializable
```

!!! info "Write the name the browser expects"
    Attribute names are not validated against any allow-list. If the browser understands an attribute, ReactPy delivers it — including `data-*`, `aria-*`, and attributes ReactPy has never heard of:

    ```python linenums="0"
    html.div({"aria-live": "polite", "data-row-id": 7, "spellcheck": False})
    ```

### `class` and `className`

Both work, and both produce `class="..."` in the DOM:

```python linenums="0"
html.div({"class": "one two"}, "...")
html.div({"className": "one two"}, "...")
```

There is no JSX in Python, so nothing forces you toward `className`. Pick one and stay consistent — `class` reads better beside the HTML it mirrors, `className` is familiar to anyone arriving from React.

### `for` and `htmlFor`

Both work on `<label>`, and both produce `for="..."`. Prefer `for`; `htmlFor` exists only for readers who expect it.

### `style`

Pass a `dict`. Keys may be `camelCase` or `kebab-case` — both are accepted, and both reach the browser in a form it understands:

```python linenums="0"
html.div(
    {
        "style": {
            "backgroundColor": "rgb(255, 0, 0)",  # camelCase
            "font-size": "20px",  # kebab-case
        }
    }
)
```

!!! warning "Always write the unit as part of the string"
    Do not rely on a bare number being given a unit. React appends `px` to numeric style values; ReactPy's executors do not agree with each other on this. Measured in Chrome, the same component rendered through each executor:

    | `#!python style` value | `ReactPy` / `ReactPyMiddleware` | `ReactPyCsr` |
    | --- | --- | --- |
    | `#!python {"fontSize": "30px"}` | `font-size: 30px` | `font-size: 30px` |
    | `#!python {"font-size": "30px"}` | `font-size: 30px` | `font-size: 30px` |
    | `#!python {"fontSize": 30}` | `font-size: 30px` | **nothing at all** |
    | `#!python {"fontSize": "30"}` | nothing | nothing |
    | `#!python {"zIndex": 5}` | `z-index: 5` | `z-index: 5` |
    | `#!python {"opacity": 0.5}` | `opacity: 0.5` | `opacity: 0.5` |

    A number that needs a unit is dropped in silence — no warning, no log line, and the layout model shows the value untouched, so it is nowhere to be found by reading the server side. Unitless properties like `z-index` and `opacity` are the exception: a number is already a valid value there.

    The portable rule: **put units in the string**, everywhere.

    ```python linenums="0"
    {"style": {"font-size": 20}}  # works by accident in some executors
    {"style": {"font-size": "20px"}}  # works everywhere
    ```

### All together

A table of rows is where most of these rules meet at once — `#!python key` in `#!python attributes`, `#!python data-*` and `#!python aria-*` passed straight through, and units inside style strings:

=== "app.py"

    ```python
    {% include "../../examples/reference_common_props/attributes/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Rendering this through `#!python Layout` gives rows whose attributes are exactly what was written:

```python linenums="0"
{
    "tagName": "tr",
    "attributes": {
        "key": 1,
        "class": "is-active",
        "data-role": "admin",
        "aria-label": "Dana, admin",
        "style": {"opacity": "1"},
    },
    "children": [...],
}
```

Nothing was renamed, and nothing was dropped. In the DOM the row arrives as:

```html linenums="0"
<tr data-role="admin" aria-label="Dana, admin" class="is-active" style="opacity: 1;">
```

The one attribute that does not reach the DOM is `#!python key` itself: `#!python ReactPy` and `#!python ReactPyMiddleware` consume it for reconciliation and never set it on the element. `#!python ReactPyCsr` does leak it, so a `#!python key="1"` attribute shows up in the page — harmless, but do not rely on the attribute being absent or present. Every other name you write arrives as written.

### Booleans and numbers

Values are serialized as JSON and coerced by the browser:

| You write | The browser receives |
| --- | --- |
| `#!python {"hidden": True}` | `hidden=""` — present, therefore true |
| `#!python {"hidden": False}` | no attribute at all |
| `#!python {"readonly": True}` | `readonly="true"` |
| `#!python {"data-x": "1"}` | `data-x="1"`, readable as `#!python element.dataset.x` |
| `#!python {"tabindex": 2}` | `tabindex="2"` |

React's attribute quirks do not carry over. There is no `htmlFor` requirement, no auto-`px`, and no special-casing of `value` versus `defaultValue` — what you write is what arrives.

### `dangerouslySetInnerHTML`

Injects a raw HTML string, exactly as in React:

```python linenums="0"
html.div({"dangerouslySetInnerHTML": {"__html": "<b>bold</b>"}})
```

The key is the plain string `#!python "dangerouslySetInnerHTML"` — not a class to import — and its only field is `#!python "__html"`.

!!! danger "This is the XSS hole"
    ReactPy does nothing to sanitize the string. Never put user input in it.

    A `#!python dangerouslySetInnerHTML` attribute is also not allowed alongside children.

---

## Children

Children are the arguments that follow the attribute dict. ReactPy accepts a wide range of types and normalizes each one:

| Child | Becomes |
| --- | --- |
| `#!python str` | a text node, verbatim |
| `#!python int` / `#!python float` | its `#!python str()`, so `#!python 7` renders as `#!python "7"` |
| `#!python None` | dropped — renders nothing |
| `#!python True` / `#!python False` | the literal text `True` / `False` |
| `#!python list` / `#!python tuple` | flattened into the children |
| another `#!python dict` | an element |
| a `@component` instance | that component's rendered output |

Nested lists are flattened, so `#!python [items, "more"]` is the same as one flat list.

!!! warning "Only `None` renders nothing"
    `#!python False` renders the word `False`. React-style short-circuits therefore misfire:

    ```python linenums="0"
    html.div(None, items or False)  # renders the word "False" when items is empty
    html.div(None, banner if is_visible else None)  # renders nothing
    ```

    Replace every `#!python x and <element>` habit with a conditional expression ending in `#!python else None`.

### Void elements

`#!python html.br`, `#!python html.img`, `#!python html.input`, `#!python html.hr`, `#!python html.meta` and the rest of the void-element set reject children:

```python linenums="0"
html.br("oops")
```

```text linenums="0"
TypeError: 'br' nodes cannot have children.
```

Nothing special is needed for self-closing tags — a tag with no children is simply:

```python linenums="0"
html.img({"src": "/logo.png", "alt": "Logo"})
```

### Fragments

`#!python html.fragment` groups children without adding an element to the DOM. It renders as an element with an empty `#!python tagName`, which the client renders as its children:

```python linenums="0"
html.fragment(
    html.h1("Title"),
    html.p("Body"),
)
```

A fragment accepts `#!python key` and nothing else:

```python linenums="0"
html.fragment({"id": "x"}, html.p("..."))
```

```text linenums="0"
TypeError: Fragments cannot have attributes besides 'key'
```

`#!python html(...)` — calling `html` directly — is the same fragment constructor.

---

## Keys

ReactPy matches children between renders to decide what to update versus what to rebuild. It reads the key out of `#!python attributes["key"]`:

```python linenums="0"
html.ul(
    None,
    [html.li({"key": person["id"]}, person["name"]) for person in people],
)
```

!!! warning "`key` is an attribute, not a sibling of `tagName`"
    React treats `#!python key` as a top-level prop. ReactPy reads it from `#!python attributes`, so this has **no effect** — the key is silently ignored:

    ```python linenums="0"
    {"tagName": "li", "key": "row-1", "children": ["..."]}
    ```

    Write `#!python {"tagName": "li", "attributes": {"key": "row-1"}, "children": ["..."]}`, or simply `#!python html.li({"key": "row-1"}, "...")`. Passing `#!python key=` to `#!python VdomDict` directly raises `#!python ValueError: Invalid keys: {'key'}.`

Without a key, a child's **position** in the list becomes its key. That is why reordering a list makes state stick to the wrong row: nothing moved as far as ReactPy is concerned. Keys must be unique among siblings.

When debug mode is on, ReactPy warns for each unkeyed child that came out of a list:

```text linenums="0"
UserWarning: Key not specified for child in list {'children': ..., 'tagName': 'li'}
```

Run your app with `#!bash REACTPY_DEBUG=1` to see them — see [Rendering Lists](../learn/rendering-lists.md) for the same warning in context. The check only fires for children inside a `#!python list`; the direct children of a tag are never warned about, and a generator cannot be inspected at all:

```text linenums="0"
UserWarning: Did not verify key-path integrity of children in generator <generator object ...> - pass a sequence (i.e. list of finite length) in order to verify
```

Pass a `#!python list` — a comprehension is usually the smallest change.

---

## Event handlers

Any callable under any attribute name becomes an event handler:

```python linenums="0"
async def save(event):
    await store.save(event["target"]["value"])


html.button({"onClick": save}, "Save")
```

The name is forwarded as the DOM event to listen for, so the names that work are the DOM event names in camelCase — `#!python onClick`, `#!python onInput`, `#!python onKeyDown`. The handler receives one argument: the event data as a JSON-serializable `#!python dict`, wrapped in `#!python reactpy.types.Event` so nested keys are also readable as attributes. There is no `#!python "data"` key to unwrap — the browser sends a *list* of arguments, and ReactPy hands you its single element. Make the handler `#!python async` when the work is slow, because a plain function blocks the client while it runs — see [Responding to Events](../learn/responding-to-events.md).

!!! warning "A handler wrapped in `EventHandler` receives the raw list"
    A plain callable is called with the browser's argument list **unpacked**, so `def f(event)` gets the event dict. An `EventHandler` does the opposite: it is called with the **list itself**, so `def f(data)` must index into it. The difference stays invisible until a handler is converted, and then `event["target"]` becomes `TypeError: list indices must be integers or slices, not str`:

    ```python linenums="0"
    from reactpy.core.events import EventHandler

    def save(event):      # plain callable: receives the event dict
        store.save(event["target"]["value"])


    def save_all(data):   # EventHandler: receives the list of arguments
        store.save(data[0]["target"]["value"])


    html.button({"onClick": save}, "Save")
    html.button({"onClick": EventHandler(save_all, prevent_default=True)}, "Save")
    ```

### ReactPy's own options

Four behaviours run in the browser *before* the event is sent to the server. Configure them by wrapping the function, not by an attribute:

```python linenums="0"
from reactpy.core.events import EventHandler

html.form(
    {"onSubmit": EventHandler(submit, prevent_default=True)},
    html.button({"type": "submit"}, "Submit"),
)
```

| Parameter | Value | Effect |
| --- | --- | --- |
| `#!python prevent_default` | `#!python bool` | calls `#!python preventDefault()` in the browser before sending |
| `#!python stop_propagation` | `#!python bool` | calls `#!python stopPropagation()` in the browser before sending |
| `#!python debounce` | `#!python int` ms | rate-limits value updates on user-input elements |
| `#!python throttle` | `#!python int` ms | rate-limits outgoing events |

A non-negative integer is required for `#!python debounce` and `#!python throttle`; anything else is ignored with a browser-console warning rather than an error:

```text linenums="0"
Ignoring invalid debounce value "fast" on event handler "onInput": expected a non-negative integer.
```

!!! warning "A dict is not an event handler"
    The React-style `#!python {"function": ..., "preventDefault": True}` shape does **not** work here. A `#!python dict` is not callable, so ReactPy treats it as an ordinary attribute and no listener is ever registered. With debug mode on you get an immediate error instead of silence:

    ```text linenums="0"
    TypeError: Object of type function is not JSON serializable
    ```

    ```python linenums="0"
    # wrong: no listener is attached
    html.button({"onClick": {"function": save, "preventDefault": True}}, "...")

    # right
    html.button({"onClick": EventHandler(save, prevent_default=True)}, "...")
    ```

### Inline JavaScript

A `#!python str` under an event handler attribute is treated as JavaScript to run in the page instead of being sent to Python:

```python linenums="0"
html.button({"onClick": "console.log(event)"}, "Log the event")
```

ReactPy records it under the element's `#!python inlineJavaScript` rather than `#!python eventHandlers`:

```python linenums="0"
{
    "tagName": "button",
    "children": ["Log the event"],
    "inlineJavaScript": {"onClick": "console.log(event)"},
}
```

The string is `#!python eval`'d in the page; if it evaluates to a function, that function is called with the event.

!!! danger "Trusted strings only"
    This runs with your application's privileges. Never build the string from user input — use a Python handler and pass data through state.

!!! note "`<script>` elements reject handlers"
    `#!python html.script` raises `#!python ValueError: 'script' elements do not support event handlers`. It also infers a key from its content or `#!python src`, so the same script is not re-run on every render.

---

## `importSource`

`#!python importSource` marks an element as coming from a JavaScript module rather than a built-in tag. ReactPy's [web module](reactpy.md) support produces it for you; you rarely set it by hand. Its keys are `#!python source`, `#!python fallback`, `#!python sourceType` and `#!python unmountBeforeUpdate`, and `#!python sourceType` must be `#!python "URL"` or `#!python "NAME"`:

```text linenums="0"
JsonSchemaValueException: data.children[0].importSource.sourceType must be one of ['URL', 'NAME']
```

---

## Invalid dictionaries

ReactPy validates the six key names as it builds an element:

```python linenums="0"
from reactpy.types import VdomDict

VdomDict(tagName="div", bogus=1)
```

```text linenums="0"
ValueError: Invalid keys: {'bogus'}.
```

```python linenums="0"
element = VdomDict(tagName="div")
element["bogus"] = 1
```

```text linenums="0"
KeyError: 'Invalid key: bogus'
```

A `#!python dict` used as a child with no `#!python "tagName"` does not raise. It sends an error to the client, where it appears in the browser console as an `#!python error` field on the model:

```python linenums="0"
html.div(None, {"children": ["x"]})
```

```text linenums="0"
ValueError: Expected a VDOM element dict, not {'children': ['x']}
```

Anything the layout cannot render is reported this way rather than taking the server down: the client receives the `#!python error` field and the server logs the traceback. Check both when an element renders as nothing.

---

## At a glance

### `#!python VdomDict` keys { #vdomdict-keys }

| Key | Type | Notes |
| --- | --- | --- |
| `#!python tagName` | `#!python str` | required; `#!python ""` means a fragment |
| `#!python children` | `#!python list` | any accepted child type, flattened |
| `#!python attributes` | `#!python dict[str, Any]` | must be JSON-serializable |
| `#!python eventHandlers` | `#!python dict[str, EventHandler]` | written for you from callables |
| `#!python inlineJavaScript` | `#!python dict[str, str]` | written for you from `#!python str` handlers |
| `#!python importSource` | `#!python dict` | written for you by web modules |

Any other key raises, as shown above. `#!python VdomDict` is a `#!python dict` subclass, so you can read and update it with normal `#!python dict` access — but not add a seventh key.

### Attribute names worth knowing

| Attribute | Value |
| --- | --- |
| `#!python class` / `#!python className` | `#!python str` of space-separated class names |
| `#!python for` / `#!python htmlFor` | `#!python str`, the `#!python id` of the labelled control |
| `#!python style` | `#!python dict` of CSS property to value; **include units in strings** |
| `#!python dangerouslySetInnerHTML` | `#!python {"__html": str}` |
| `#!python key` | `#!python str` or `#!python int`, unique among siblings |
| anything else | forwarded to the browser verbatim |

## Related

-   [Usage](usage.md) — the tag API itself: naming rules, custom tags, SVG
-   [Responding to Events](../learn/responding-to-events.md) — the event `#!python dict`, `#!python async` handlers
-   [Rendering Lists](../learn/rendering-lists.md) — keys and why rows keep the wrong state
-   [Use Ref](use-ref.md) — ReactPy's `#!python Ref`, which is never attached to an element
