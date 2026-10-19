## Overview

<p class="intro" markdown>

Call hooks at the top level of a component, in the same order, on every render. No loops, no conditions, no early returns, no nesting inside a function that runs later. ReactPy will not always tell you when you break this rule — in one case it corrupts state in silence.

</p>

```python linenums="0"
@component
def form():
    name, set_name = use_state("")  # top level, every render, same order
    email, set_email = use_state("")
    return html.form(name, email)
```

ReactPy identifies a hook's state by **where it was called**, not by what it is called into. The nth `#!python use_state` in a component body gets the nth stored slot. Change which hooks run, and you change which slot each one reads.

---

## The rules

-   **Only call hooks from a component body or another hook** — never from an event handler, an effect body, a plain function, or module level. See [React calls Components and Hooks](react-calls-components-and-hooks.md#hooks-are-called-by-reactpy).
-   **Call them at the top level** — not inside `#!python if`, `#!python for`, `#!python try`, a `#!python while`, a comprehension, or a nested function that runs later.
-   **Always call the same hooks in the same order** — which hooks run may not depend on props, state, or anything else that can change between renders.
-   **No early `#!python return` before a hook** — an early exit skips the hooks after it.

The one exception is `#!python use_context`: it takes no slot at all (`core/hooks.py` reads the provider off the current hook and never touches the state list), so calling it conditionally shifts nothing — verified, a component whose `#!python use_context` call runs on only some renders keeps `#!python _state` at the same length throughout. It is still a hook and still needs an active render to call.

---

## Why: hooks are slots, not names

ReactPy keeps a component's hook values in a plain list and hands out the next entry on each call — a running index, not a name. From `reactpy/core/_life_cycle_hook.py`, `LifeCycleHook.use_state`:

```python linenums="0"
if not self._rendered_atleast_once:
    # since we're not initialized yet we're just appending state
    result = function()
    self._state.append(result)
else:
    # once finalized we iterate over each succesively used piece of state
    result = self._state[self._current_state_index]
self._current_state_index += 1
```

The first render appends one entry per hook call, in order. Every later render reads back by position. Nothing records the variable name, the hook's type, or what it stores — so position *is* identity.

That is why the rules are phrased as "same order". The component cannot tell ReactPy which value is which; only the sequence of calls says so.

---

## What breaking the rules actually does

This is where ReactPy and React part ways, and why the rules must be enforced by review rather than trusted to a loud failure.

### More hooks than the first render: a crash

A component that mounts with one hook and later calls two tries to read a slot that was never appended:

```python linenums="0"
@component
def grow():
    n, set_n = use_state(0)

    async def bump(event):
        set_n(n + 1)

    if n >= 1:  # a second hook appears only after the first click
        extra, set_extra = use_state("EXTRA")
        return html.div(f"n={n} extra={extra}")
    return html.div(f"n={n}", html.button({"onClick": bump}, "bump"))
```

With debug mode on, the component is replaced by an error node and the server logs the cause:

```text linenums="0"
IndexError: list index out of range
```

With debug mode off, the `#!python error` field is an empty string, so the region simply renders as nothing. This case fails loudly enough to find.

### Fewer hooks than the first render: silent state corruption

This is the dangerous one. A hook call that disappears from *above* another one shifts every later index by one — and the shift is invisible:

```python linenums="0"
@component
def shifting():
    show, set_show = use_state(True)  # slot 0
    if show:
        hidden, set_hidden = use_state("HIDDEN")  # slot 1, only while show
    n, set_n = use_state("N")  # slot 1 while show, slot 2 once it is off
    return html.div(f"show={show} n={n}")
```

Measured, flipping `#!python show` from `#!python True` to `#!python False` once (through its setter — this snippet has no button; the runnable `broken_toggle` below wires the same shape to a real **Toggle** button):

```text linenums="0"
mount:          show=True  n=N
after toggle:   show=False  n=HIDDEN     <-- `n` is now reading `hidden`'s slot
```

No error, no warning, no traceback. `#!python n` starts showing another hook's value and keeps doing so until the branches line up again. React, by contrast, throws `Rendered fewer hooks than expected.` A ported component can therefore be *wrong* in ReactPy where it was a crash in React.

The corruption usually surfaces later, somewhere that looks unrelated. With a counter that should hold an `#!python int`, the shifted read hands a string to arithmetic, and the *next* click dies in the handler:

```text linenums="0"
TypeError: can only concatenate str (not "int") to str
```

That traceback names the event handler, not the hook — so the hunt starts in the wrong file. The button stops working, and the error is on the server log only.

=== "app.py"

    ```python
    {% include "../../examples/reference_rules_of_hooks/conditional_hook/app.py" start="# start" %}
    ```

=== ":material-play: Run"

In `broken_toggle`, **Add 1** works, then **Toggle** makes the heading read `#!python NOT-A-NUMBER`, and the next **Add 1** does nothing at all — the handler raised `TypeError` on the server. `fixed_toggle` is the same component with the hooks moved out of the condition: both of its buttons keep working through every toggle.

### A hook in a loop: frozen values, then a crash

```python linenums="0"
@component
def rows(n):
    out = []
    for i in range(n):
        value, set_value = use_state(f"v{i}")
        out.append(value)
    return html.div(out)
```

Measured with `#!python n` going 3 → 2 → 1 → 0:

```text linenums="0"
vals=['v0', 'v1', 'v2']
vals=['v0', 'v1']
vals=['v0']
vals=[]
```

It looks correct. It is not: `#!python use_state(f"v{i}")` applies its initial value only on the first render, so the `#!python i` in it is decoration, and the list's length is driven by an argument while its contents come from frozen slots. Growing `#!python n` past its first-render value raises the `#!python IndexError` from the first case. A loop of hooks is wrong either way — build one component per item, which gives each its own state legitimately:

```python linenums="0"
html.div(None, [row(item, key=item["id"]) for item in items])
```

### An early return before a hook

```python linenums="0"
@component
def loading():
    n, set_n = use_state(0)
    if n == 2:
        return html.div("early")  # skips the hook below
    label, set_label = use_state("LABEL")
    return html.div(f"{n} {label}")
```

ReactPy does not crash, and `#!python label` survives while the branch is away. But this is the same slot-shifting hazard as above, arriving whenever the condition flips. Put the early return *after* every hook, or move the conditional content into a child component:

```python linenums="0"
@component
def loading():
    n, set_n = use_state(0)
    label, set_label = use_state("LABEL")  # all hooks first
    if n == 2:
        return html.div("early")
    return html.div(f"{n} {label}")
```

!!! warning "Tolerance is not safety"
    ReactPy lets several of these through; React does not. The case above corrupts state without a word, and the same code raises the moment it is ported, tested against React semantics, or read by someone who assumes React's guarantees. Treat the rules as absolute.

---

## Custom hooks follow the same rules

A custom hook is only a function, so nothing checks it:

```python linenums="0"
def use_auth(token):
    if not token:
        return None, None  # hooks skipped on some calls
    user, set_user = use_state(None)
    return user, set_user
```

Call it with a falsy `#!python token` and the caller silently loses a slot — measured, the happy path consumes one hook slot and the falsy path consumes none. Return early only after every hook has run, or split into two hooks and choose between them at the call site, where the choice is visible in the component body:

```python linenums="0"
@component
def page(token):
    return authed(token) if token else anonymous()
```

Because a hook's name is all a reviewer has, name custom hooks `#!python use_*` and call them only from component bodies or other hooks.

---

## Catching violations

Nothing checks these rules for you. ReactPy has no runtime assertion for the call-site rule or for the order rule, and a component that breaks them usually renders and then misbehaves rather than failing:

-   **Fewer hooks than the first render** → the state list is walked by position, so slots shift and values silently migrate between variables. Nothing is logged.
-   **More hooks than the first render** → `#!python IndexError: list index out of range`, the render aborts, and with debugging off the region simply goes blank.

Run with `#!bash REACTPY_DEBUG=1` during development, so a render failure becomes a visible error in the model instead of an empty region, and keep the two habits that replace a checker:

-   Treat any `#!python use_` call that appears below the first non-hook statement of a component body, or inside an `#!python if` / `#!python for` / `#!python try` / nested `#!python def`, as a review defect.
-   Prove behaviour in a test instead of trusting a glance: a pure component is an ordinary function, so render it twice inside `#!python reactpy.core.layout.Layout` and assert. A hook called conditionally shows up as state that does not survive the render which flips the branch.

---

## Reference

| Pattern | ReactPy behaviour | Verdict |
| --- | --- | --- |
| Hook at component top level | Works | Do this |
| Hook in a custom hook called from a body | Works | Do this |
| Hook in an `#!python if` that never changes | Works by accident | Broken |
| Hook in an `#!python if` that can change | Fewer hooks: silent state corruption. More hooks: `#!python IndexError` | Broken |
| Hook in a `#!python for` | Frozen initial values; `#!python IndexError` if the loop grows | Broken |
| Hook after an early `#!python return` | Slot shift when the branch flips | Broken |
| Hook in an event handler | `#!python RuntimeError`, server log only | Broken |
| Hook in an effect body | `#!python RuntimeError`, server log only | Broken |
| Hook at module level | `#!python RuntimeError: No life cycle hook is active.` | Broken |

## Related

-   [Rules of React](rules-of-react.md) — the section overview
-   [Components and Hooks must be pure](components-and-hooks-must-be-pure.md) — the other half of the contract
-   [React calls Components and Hooks](react-calls-components-and-hooks.md) — who runs a hook, and when
-   [Use State](use-state.md), [Use Effect](use-effect.md), [Use Memo](use-memo.md) — the hooks these rules govern
-   [Use Callback](use-callback.md), [Use Debug Value](use-debug-value.md) — hooks worth writing your own wrappers around
