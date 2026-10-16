## Overview

<p class="intro" markdown>

Two rules make ReactPy predictable: components and hooks must be pure, and ReactPy must be the one that calls them. They look like style advice. They are load-bearing — and in ReactPy, one of them is not enforced by anything except you.

</p>

| Rule | In one line | Read |
| --- | --- | --- |
| **Purity** | A component or hook returns the same output for the same inputs, and changes nothing outside itself. | [Components and Hooks must be pure](components-and-hooks-must-be-pure.md) |
| **Who calls what** | You write components and hooks; ReactPy calls them — always from the top level of a component, in the same order. | [React calls Components and Hooks](react-calls-components-and-hooks.md), [Rules of Hooks](rules-of-hooks.md) |

The two are one idea seen from either side. ReactPy is free to call your component whenever it likes, as often as it likes, because purity makes that safe. In return, your component gets to assume nothing about *when* it ran — which is why state lives in hooks rather than in variables.

---

## Why the rules exist

ReactPy renders on a **server**, inside one Python process that serves many connections, and re-renders a component whenever its state changes or its parent renders. Both facts are what the rules protect against.

-   **Impure rendering leaks between users.** A module-level `#!python dict` written during a render is shared by every connection in the process. Three visitors, one cart. No error, and each page looks fine. Measured in [Components and Hooks must be pure](components-and-hooks-must-be-pure.md#the-server-makes-this-worse).
-   **Render frequency is not yours to predict.** Code that counts, accumulates, or logs in a component body runs more often than the user acts. A child re-renders every time its parent does — ReactPy has no `#!python memo` bailout for components.
-   **Hook state is positional.** ReactPy hands out hook values from a list by index, so changing *which* hooks run changes *which value each hook reads*. The usual outcome is not an error but a component quietly reading its neighbour's state. See [Rules of Hooks](rules-of-hooks.md#what-breaking-the-rules-actually-does).

The last point is the one that surprises people coming from React. React's hook dispatcher validates call order and throws; ReactPy's does not. Several violations are tolerated silently, and one of them corrupts state with nothing logged anywhere. The rules are still exactly React's — the safety net underneath them is not.

---

## The rules, as a checklist

For a **component** body:

-   reads only its arguments, and values from its own hooks
-   assigns no global or module-level name
-   mutates no object it did not create during this render
-   reads no clock, `#!python random`, environment, or I/O
-   starts no task, thread, or timer
-   may freely define event handlers — they run later, and may do all of the above

For a **hook** call site:

-   called from a component body or another hook — never an event handler, effect body, or plain function
-   at the top level of that body: not under `#!python if`, `#!python for`, `#!python try`, and not inside a nested `#!python def` that runs *outside* the render (an event handler, an effect callback). A nested `#!python def` whose name starts with `use_` and which the body calls during the render is a custom hook, and calling hooks in it is the point.
-   the same hooks, in the same order, on every render
-   no early `#!python return` before a hook

`#!python use_context` is the one hook that takes no slot, so it alone may be called on only some renders without shifting the others. See [Rules of Hooks](rules-of-hooks.md#the-rules).

For a **custom hook** (`#!python use_*`): everything above, plus it must not skip its own hooks on some calls.

---

## What ReactPy cannot check for you

`reactpy-flake8` covers the call-site rule at build time (see [Rules of Hooks](rules-of-hooks.md#catching-violations)), but there is no runtime assertion for hook *order*, and that is the one that bites silently. Two settings get you most of the way:

-   `#!bash REACTPY_DEBUG=1` turns a render failure into a visible error in the model instead of a blank region, and enables the VDOM checks described in [Common Props](common-props.md#invalid-dictionaries).
-   Tests are cheap precisely *because* of the rules: a pure component is an ordinary function — call it inside `#!python reactpy.core.layout.Layout`, render it twice, assert the models are equal. No browser involved.

Everything else is review. The greppable version: any `#!python use_` call that appears below the first non-hook statement of a component body, or inside a conditional, loop, or nested function, is a defect until proven otherwise.

---

## At a glance

| You might be tempted to | Instead |
| --- | --- |
| Cache a computation in a module-level `#!python dict` | `#!python use_memo` |
| Keep a per-user counter in a global | `#!python use_state` or `#!python use_reducer` |
| Fetch data in the component body | An event handler, or `#!python use_async_effect` |
| Fetch request headers with `#!python os.environ` | `#!python use_scope` / `#!python use_location` |
| Call a hook from an event handler | Call it in the body and close over the value |
| Skip a hook when a prop is falsy | Return early only after all hooks, or split into two components |
| Loop over `#!python use_state` | One component per item, keyed |
| Reach for `#!python use_effect` to derive a value | Compute it in the body |

## Related

-   [Components and Hooks must be pure](components-and-hooks-must-be-pure.md) — the contract, the server-shared-state leak, where effects belong
-   [React calls Components and Hooks](react-calls-components-and-hooks.md) — constructors versus calls, reserved `#!python key`, where hooks may run
-   [Rules of Hooks](rules-of-hooks.md) — slots, and the measured cost of breaking order
-   [Keeping Components Pure](../learn/keeping-components-pure.md) — the tutorial version, with exercises
-   [Your First Component](../learn/your-first-component.md) — start here if you have not written one yet
