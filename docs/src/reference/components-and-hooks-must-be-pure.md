## Overview

<p class="intro" markdown>

A component is a formula: given the same arguments, it must return the same VDOM, and it must change nothing outside itself. This page states that contract precisely — for components *and* for hooks — and names the places ReactPy expects side effects instead.

</p>

The short version:

-   A **component** may read its arguments, call hooks, and return VDOM. It must not mutate anything that existed before it was called, and its output must not depend on anything it did not receive.
-   A **hook** follows the same rule, plus one of its own: it must be called in the same order on every render — see [Rules of Hooks](rules-of-hooks.md).

This is not a style preference. ReactPy calls your component at times and frequencies you do not control, and rendering is where the shared-state bug below lives — because in ReactPy components run on a **server**, inside one long-lived Python process.

---

## The contract

A component body is allowed to:

| Do | Example |
| --- | --- |
| Read its own arguments | `#!python html.p(title)` |
| Call hooks | `#!python count, set_count = use_state(0)` |
| Compute from those values | `#!python html.p(f"{count} item(s)")` |
| Define functions it hands to the client | `#!python {"onClick": save}` |
| Call other components | `#!python html.div(None, Row(item))` |

A component body is **not** allowed to:

| Don't | Why it fails |
| --- | --- |
| Assign to a module-level or global variable | Shared by every connection in the process; see [The server makes this worse](#the-server-makes-this-worse) |
| Mutate an object it received as an argument | The caller still holds it, so the change is visible outside the render |
| Mutate a value read from `#!python use_state` | The comparison that decides whether to re-render can drop an in-place mutation silently |
| Read the clock, `#!python random`, or the environment | Same inputs, different output — the formula is broken |
| Do I/O: `#!python open`, `#!python requests`, a database, `#!python print` | Runs on every render, at a frequency you do not control |
| Start a task, thread, or timer | Leaks one per render |

The two halves of the rule are independent. `#!python random.choice` mutates nothing and is still impure of output; writing a module-level `#!python dict` is an outside effect whether or not it changes what you return.

The pair below is the difference, side by side. Both render identically on the first pass. The first one counts renders in a module-level variable, so the number it prints is a property of the *process*, not of the component — press the button twice in two browser tabs and the two pages disagree about what "the same render" produced:

=== "impure.py"

    ```python
    {% include "../../examples/reference_rules_of_react/impure_render/app.py" start="# start" %}
    ```

=== "pure.py"

    ```python
    {% include "../../examples/reference_rules_of_react/pure_render/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

---

## The server makes this worse

In a browser, module-level state belongs to one user. In ReactPy it belongs to **every connection your process serves**, for the whole life of the process. Rendering into a shared container is therefore not a code smell but a data leak — and it produces no error.

Three separate layouts, three separate visitors, one module-level `#!python dict`:

```python linenums="0"
SESSION = {}


@component
def account(name):
    SESSION.setdefault("cart", [])
    SESSION["cart"].append(f"{name}-item")
    return html.div(f"{name}: cart has {len(SESSION['cart'])} item(s)")
```

Measured output from three independent layouts:

```text linenums="0"
visitor A: cart has 1 item(s): ['A-item']
visitor B: cart has 2 item(s): ['A-item', 'B-item']
visitor C: cart has 3 item(s): ['A-item', 'B-item', 'C-item']
```

Nothing crashes, each page looks plausible, and every visitor after the first sees other people's data. The same failure appears with `#!python total += 1` at module scope, a module-level cache, or a mutable default argument on a component.

Per-user state belongs in `#!python use_state` or `#!python use_reducer`, which ReactPy keeps per component instance. State genuinely shared across connections belongs in an explicit store you pass in — through [context](use-context.md) or an argument — never in a bare module global that rendering reaches for.

---

## Where side effects belong

| Need | Put it in |
| --- | --- |
| React to a click, keystroke, submit | An event handler ([Responding to Events](../learn/responding-to-events.md)) |
| Run once on mount, or when values change | `#!python use_effect` ([Use Effect](use-effect.md)) |
| Await something outside the render | `#!python use_async_effect` ([Use Async Effect](use-async-effect.md)) |
| Read a request's headers or URL | `#!python use_connection`, `#!python use_scope`, `#!python use_location` |
| Build a value for the render, only when inputs change | `#!python use_memo` ([Use Memo](use-memo.md)) |
| Log for debugging | `#!python use_debug_value`, or a `#!python logging` logger *outside* the render |
| Load data at process start | Executor startup ([ReactPy](reactpy.md)) |

An event handler is the default answer. It is defined inside the component but runs later, in response to something the user did, so it may do anything a pure function may not.

!!! warning "`use_effect` is the escape hatch, not the habit"
    Effects run after the render, which makes them correct for touching the outside world and awkward for expressing logic. Most of the data you would reach for an effect for can be computed during the render instead. If you find yourself writing an effect to *derive* a value, stop and compute it in the body.

---

## Hooks must be pure too

A hook body is a function your component calls during its render, so it inherits every rule above, plus these:

-   **No `#!python global`, no module mutation.** Same leak, harder to see because the hook is shared by several components.
-   **No time, no randomness.** `#!python use_memo(lambda: random.random(), [])` fixes each instance to whatever the first render produced. Pass the value in as an argument instead.
-   **No I/O.** A custom hook that queries a database runs that query on every render of every component that uses it.
-   **No conditional hook calls, and no hooks in loops.** That is the [Rules of Hooks](rules-of-hooks.md), and it is the one a reviewer can catch by reading.

A custom hook that needs the outside world should take the data as an argument, or expose an event handler that does the work when called.

---

## What ReactPy cannot do with purity

React skips re-rendering a component whose props are unchanged — safe *because* pure functions are safe to cache. ReactPy has no such bailout: a child component re-runs whenever its parent renders, no matter how pure it is.

There is `#!python use_memo` for values and `#!python use_callback` for function identity, which reduce the *work* a render does, but neither stops the render. So purity here buys correctness, testability, and safety under restart — not performance. Do not add memoization on the theory that ReactPy will skip the render; it will not.

!!! info "Why the rule is enforced by review, not by tests"
    ReactPy cannot detect impurity — reading a global is a legal Python statement. The rule is about where the language lets you put things, which is why it belongs in code review.

---

## Testing purity

A pure component is an ordinary function, so test it as one — no browser:

```python linenums="0"
import asyncio

from reactpy.core.layout import Layout


def render_model(component):
    async def go():
        async with Layout(component) as layout:
            return (await layout.render())["model"]

    return asyncio.run(go())


def test_same_arguments_same_output():
    assert render_model(Greeting("a")) == render_model(Greeting("a"))
```

Run each layout in its own event loop and build a fresh component instance per call. If a component renders differently the second time, or one layout's render changes another's output, it is impure and the test says so — which is exactly what happens for a component that counts its own renders.

---

## Symptoms

| You see | Likely cause |
| --- | --- |
| Two users see each other's data | Module-level state written during render |
| A counter is higher than the number of clicks | The component rendered more often than you assumed, and it counts renders |
| Numbers change on reload with no user action | Clock or `#!python random` during render |
| A list mutation does nothing | State mutated in place; see [Updating Arrays in State](../learn/updating-arrays-in-state.md) |
| One component's render changes another's output | A shared object reached through a global, a default argument, or a class attribute |

## Related

-   [Rules of React](rules-of-react.md) — the section overview
-   [Rules of Hooks](rules-of-hooks.md) — the hook-order rule, and what breaking it does in ReactPy
-   [React calls Components and Hooks](react-calls-components-and-hooks.md) — why "it works locally" does not prove purity
-   [Keeping Components Pure](../learn/keeping-components-pure.md) — the tutorial version, with exercises
-   [Use State](use-state.md) — per-instance state, and the comparison that decides re-renders
-   [Use Effect](use-effect.md) — the sanctioned place for side effects
