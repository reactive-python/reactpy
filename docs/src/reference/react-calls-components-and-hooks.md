## Overview

<p class="intro" markdown>

You do not call a component or a hook — ReactPy does. Understanding who calls what explains why components must be pure, why hook order matters, and why calling a component yourself almost never does what you meant.

</p>

```python linenums="0"
@component
def counter():
    count, set_count = use_state(0)  # ReactPy runs this, not you
    return html.h1(count)
```

Writing `#!python counter()` does not run the function. And `#!python use_state` does not work from anywhere you like — it works only while ReactPy is in the middle of rendering the component that called it.

---

## Reference

### ReactPy calls components { #reactpy-calls-components }

`@component` turns a function into a *constructor*. Calling it returns a `#!python Component` object — a description of "render this function with these arguments", to be rendered later, by the layout:

```python linenums="0"
>>> type(counter())
<class 'reactpy.core.component.Component'>
```

The layout is what invokes your function body, at times it decides:

| ReactPy calls your component | When |
| --- | --- |
| On mount | The first time it appears in the tree |
| On state change | A `#!python use_state` or `#!python use_reducer` in that component is updated |
| On parent render | Whenever the component that renders it re-renders |
| On an event | Indirectly — your handler runs, and any state it sets schedules a render |

Two consequences follow immediately.

**You do not control how often it runs.** A parent re-render re-renders its children, and ReactPy has no memo bailout for components. Code that counts, logs, or accumulates in a component body accumulates faster than the number of user actions. Measured: one press of a parent's button produced exactly one render of the parent and one of an unrelated child — but nothing guarantees those counts match your mental model once several state updates are in play.

**Calling it yourself does not render it.** Two mistakes, both silent:

```python linenums="0"
html.div(None, my_component)  # passing the function, not calling it
html.div(None, my_component())  # correct: an instance to be rendered
```

The first is accepted, and the function's *repr* becomes a text child — the page shows something like `#!python <function my_component at 0x7f0d1b2c4e00>`. There is no error, because a callable that is not a known child type is stringified like a number would be. If your page ever displays a hex address, this is why.

Calling `#!python .render()` on an instance does not work either:

```python linenums="0"
await my_component().render()
```

```text linenums="0"
RuntimeError: No life cycle hook is active. Are you rendering in a layout?
```

Rendering needs a life cycle hook, which only a layout provides. To see what a component produces, put it in one:

```python linenums="0"
import asyncio

from reactpy.core.layout import Layout


def render_model(component):
    async def go():
        async with Layout(component) as layout:
            return (await layout.render())["model"]

    return asyncio.run(go())
```

### Components are values { #components-are-values }

An instance is an ordinary Python object, so you can build one in a loop or pass it as an argument — the way ReactPy expects you to compose:

```python linenums="0"
html.ul(None, [row(item) for item in items])
```

Each call creates a fresh instance, and each gets its own state. Reusing one instance in two positions in the tree is the thing to avoid: build a new one per position, and key them when they come from a loop.

### `key` is a reserved parameter { #key-is-reserved }

A component constructor accepts an optional `#!python key` keyword, which the layout uses for reconciliation:

```python linenums="0"
[row(item, key=item["id"]) for item in items]
```

Because of that, `#!python key` is **reserved** as a component parameter name, and a component that declares one is rejected at import time — before anything renders:

```python linenums="0"
@component
def row(key):  # do not do this
    return html.li(key)
```

```text linenums="0"
TypeError: Component render function <function row at 0x...> uses reserved parameter 'key'
```

Name the argument something else — `#!python row_key`, `#!python label`, `#!python item_id` — and pass the reconciliation key as `#!python key=` at the call site.

Note this differs from plain elements, where the key lives *inside* the attributes dict. See [Common Props](common-props.md#keys).

### Hooks are called by ReactPy, during a render { #hooks-are-called-by-reactpy }

A hook is a plain function that reads the *current* life cycle hook off a task-local stack. That is why it raises outside a render — and in several places that look like renders:

| You call a hook from | Result |
| --- | --- |
| A component body | Works — the intended place |
| A custom hook called from a component body | Works, and is how you build one |
| Module level, directly | `RuntimeError: No life cycle hook is active. Are you rendering in a layout?` |
| `await component().render()` | The same `RuntimeError` |
| An event handler | The same `RuntimeError`, logged on the server as `Failed to execute event handler ...` |
| An `use_effect` callback body | The same `RuntimeError`, logged on the server only |

The last two are the trap. Calling `#!python use_state` from inside an event handler does not crash the app; it kills that handler, and the traceback goes to the server log:

```text linenums="0"
Failed to execute event handler EventHandler(...)
...
RuntimeError: No life cycle hook is active. Are you rendering in a layout?
```

Nothing changes in the browser, so the symptom is "the button does nothing". Move the hook call to the component body and close over the value instead.

---

## Usage

### The mental model

| You | ReactPy |
| --- | --- |
| Define what to render | Decide when to render |
| Return VDOM from a component | Call the component |
| Declare state with a hook | Store it, per component instance |
| Write an event handler | Run it, when the event arrives |
| Declare dependencies | Compare them, and decide whether to re-run an effect |

Everything in the [Rules of React](rules-of-react.md) follows from the left column being yours and the right column being ReactPy's. You cannot ask ReactPy to render less often, so you write components that are safe to render often.

### A custom hook is a component's helper, not a standalone function

Because a hook is called during a render, a custom hook is only usable from a render:

```python linenums="0"
def use_cart():
    items, set_items = use_state([])  # fine: runs during the caller's render
    return items, add_item
```

Calling `#!python use_cart()` from an event handler, a utility function, or a background task raises the same `#!python RuntimeError`. If logic must be callable from there, write it as a normal function that takes what it needs as arguments.

---

## Troubleshooting

### A hex address appeared on the page

You passed a component instead of calling it: `#!python html.div(None, my_component)`. Add the parentheses.

### `RuntimeError: No life cycle hook is active. Are you rendering in a layout?`

A hook ran with no render in progress. Usual causes: called from an event handler, from an effect body, from a helper that a handler calls, or by awaiting `#!python .render()` yourself. Read the *server* log for the traceback — the browser will not show it.

### `TypeError: ... uses reserved parameter 'key'`

A component parameter is named `#!python key`. Rename it, and pass the reconciliation key as `#!python key=` at the call site.

### A button does nothing, and the browser shows no error

The handler raised on the server. Handlers that call hooks fail this way. Check the server log.

## Related

-   [Rules of React](rules-of-react.md) — the section overview
-   [Components and Hooks must be pure](components-and-hooks-must-be-pure.md) — what these calling rules require of your code
-   [Rules of Hooks](rules-of-hooks.md) — the ordering rule, and what breaking it does in ReactPy
-   [Your First Component](../learn/your-first-component.md) — writing your first component
-   [Responding to Events](../learn/responding-to-events.md) — where handler code may and may not reach
