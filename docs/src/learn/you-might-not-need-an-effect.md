## Overview

<p class="intro" markdown>

Most Effects are unnecessary. If your logic only adjusts one thing based on another thing you already have, it belongs in the render — not in an Effect. This page walks through the common cases where an Effect looks right and isn't, with the render counts each one costs.

</p>

!!! summary "You will learn"

    -   How to recognize an Effect that is doing a render's job
    -   What to write instead, case by case
    -   Why ReactPy cannot use React's "set state during render" escape hatch
    -   Which Effects genuinely _are_ necessary

## How to remove unnecessary Effects

Work through each Effect in your code and ask: **does this code need to run after a render, or could it run while rendering?**

An Effect is genuinely necessary when the component must reach something outside ReactPy — subscribing to a queue, opening a socket, starting a task. Everything below is the opposite case: the "external system" is a value your component already has.

If you're not sure what Effects are for in the first place, start with [Synchronizing with Effects](./synchronizing-with-effects.md).

### Updating state based on props or state

A component shows a name built from two fields. The tempting version stores the combination and keeps it in step with an Effect:

=== "app.py"

    ```python
    {% include "../../examples/you_might_not_need_an_effect/full_name_effect/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Remove the state variable and the Effect, and calculate it during render:

=== "app.py"

    ```python
    {% include "../../examples/you_might_not_need_an_effect/full_name_derived/app.py" start="# start" %}
    ```

=== ":material-play: Run"

The difference is measurable, and the first row of each is the part users actually see:

| | First paint | Renders for two keystrokes |
| --- | --- | --- |
| Effect + stored state | `#!python "(nothing yet)"` | 6 |
| Derived during render | `#!python "Ada Lovelace"` | 3 |

Verified in a `#!python Layout`. The Effect version renders once with an empty name, sets state from the Effect, renders again — every keystroke costs two renders instead of one, and the very first paint is wrong. **Nothing downstream can rescue that first frame, because it is a real render that a real client receives.**

**When something can be calculated from existing props or state, don't put it in state.** Calculate it during render. Fewer state variables means less code, no way for two of them to drift apart, and half the renders. If this feels unfamiliar, [Thinking in React](./thinking-in-react.md) covers what belongs in state.

!!! info "How expensive is too expensive?"

    If you're not sure whether a calculation is costly enough to worry about, **write it without caching first,** then measure it: time the component body, or count how often it runs. In practice the work that is genuinely slow is usually obvious — parsing, sorting or filtering thousands of rows, regex over a large string, cryptographic hashes. String concatenation, `#!python len()`, and a loop over a page's worth of items are not worth a cache, and a cache costs more than it saves when its dependency list is wrong.

### Caching expensive calculations

When a calculation genuinely is expensive, the answer is still not state plus an Effect — it is `#!python use_memo`, which caches a _value_ without adding a render:

=== "app.py"

    ```python
    {% include "../../examples/you_might_not_need_an_effect/expensive_filter/app.py" start="# start" %}
    ```

=== ":material-play: Run"

The filter records each run so the result is countable. Verified: after two keystrokes the component has rendered three times and the filter has run **once**; pressing **Change filter** adds a render and a second run. The value is recomputed exactly when the inputs it reads change, and never on a render that didn't change them.

Two properties worth knowing, both verified:

-   `#!python use_memo` **infers** its dependencies the same way `#!python use_effect` does — from the names the function reads. Pass `#!python dependencies=[]` to pin a value forever, or `#!python dependencies=None` to recompute on every render. See [Use Memo](../reference/use-memo.md).
-   It caches the **value**, not the render. The component body still runs on every render; ReactPy has no component-level `#!python memo`, so a child re-runs whenever its parent does. `#!python use_memo` saves the computation, never the render — see [Render and Commit](./render-and-commit.md).

Mutating a value in place and "setting" it back defeats `#!python use_memo` too, for the same reason it defeats `#!python use_state`: the new value compares equal to the old one. Build a new object instead ([Updating Arrays in State](./updating-arrays-in-state.md)).

### Resetting all state when a prop changes

A profile page holds a comment draft. When the user navigates to a different profile, the draft should not follow them:

=== "app.py"

    ```python
    {% include "../../examples/you_might_not_need_an_effect/reset_with_key/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: type a draft, press **Next profile**, and the draft is empty on the new profile — in a single extra render.

Passing `#!python key=user_id` tells ReactPy that a different `#!python user_id` means a different component instance. It tears down `#!python profile()` and everything below it and builds them again, so all of their state starts fresh. One line, and it covers every piece of state in the whole subtree — no Effect, and no remembering to add one to each nested component.

The Effect version (`#!python set_comment("")` in an Effect depending on `#!python user_id`) is worse in three ways: the subtree renders once with the previous user's draft still in it, every nested component needs its own copy, and a piece of state added later silently fails to reset. See [Preserving and Resetting State](./preserving-and-resetting-state.md) for the full mechanism.

!!! warning "`#!python key` is spelled differently for elements and components"

    Here it is a **keyword** argument to the component call: `#!python profile(user_id, key=user_id)`. On an element it goes in the attribute dict instead: `#!python html.li({"key": 1}, ...)`. Put it in the wrong place and you get `#!python TypeError: Vdom.__call__() got an unexpected keyword argument 'key'`, or a literal `#!python key="..."` attribute in the page.

### Adjusting some state when a prop changes

Sometimes you don't want to throw state away — just invalidate part of it when an input changes. A list keeps a selection, and a new `#!python items` prop should clear it. React's advice is to call the setter during render, and **that escape hatch does not work in ReactPy.** Measured, the render-phase-setter version takes four renders and the client receives this sequence:

```text linenums="0"
<root>                     items: [a,b,c]     selected: None
/children/0/children/1     items: [a,b,c]     selected: a
<root>                     items: [a,b,c,i4]  selected: a     <-- stale, and delivered
/children/0/children/1     items: [a,b,c,i4]  selected: None
```

React throws the discarded render away; ReactPy hands the model to the socket as soon as it exists, so the stale frame ships. Use a derived read instead. Store the value alongside what it belonged to, and let the read decide whether it is still valid:

=== "app.py"

    ```python
    {% include "../../examples/you_might_not_need_an_effect/adjust_on_prop_change/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: **Select** costs one render and shows the selection; **Add item** costs one render and the selection is already gone in that same patch — three renders total, no stale frame.

The general shape is a guard on the read rather than a call to the setter:

```python linenums="0"
is_valid = chosen["items"] == items
selection = chosen["value"] if is_valid else None
```

!!! warning "Do not set state from an Effect that depends on it"

    The reflexive alternative — an Effect calling `#!python set_selection(None)` with `#!python dependencies=[items]` — is not merely slow. When the value it sets is one it also reads, it is a loop, and ReactPy has no detector for one. Measured: an Effect that set a counter it depended on rendered **86 times** before the probe gave up. If a component visibly spins, read what the Effect awaits, what it depends on, and what it sets.

### Sharing logic between event handlers

Two handlers should do the same thing on input. There is no reason for this to involve an Effect:

=== "app.py"

    ```python
    {% include "../../examples/you_might_not_need_an_effect/shared_handler_logic/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: type in the shipping field and the billing readout changes with it, in one render, because both setters were called from one handler.

Event handlers are ordinary functions — ordinary `#!python async def`s, which is to say the coroutine ReactPy requires of anything in a handler slot. Call one from the other (with `#!python await`, since it is a coroutine), extract the shared part into a plain function, or pass the other setter as a parameter. Whatever React's docs tell you here transfers unchanged, because none of it is rendering work.

### Sending a POST request

Submitting a form is an event, not a consequence of rendering. Do the work in the handler:

=== "app.py"

    ```python
    {% include "../../examples/you_might_not_need_an_effect/form_submit/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: fill the field, submit, and the transport recorded exactly one send — `#!python ['ada@example.com']`.

The version to avoid is a flag plus an Effect: `#!python set_pending(True)`, and an Effect that watches `#!python pending`. It costs a state variable, an extra render per submission, and — because Effects re-run on dependency changes and remounts — a way to send twice. `#!python event.preventDefault()` stops the page navigating, and must appear **literally in the handler's body**, since ReactPy detects it by bytecode inspection ([Creating VDOM Event Handlers](./creating-vdom-event-handlers.md)).

### Notifying parent components about state changes

A child should tell its parent something happened. Pass a callback and call it from the child's event handler — this works exactly as it does in React:

=== "app.py"

    ```python
    {% include "../../examples/you_might_not_need_an_effect/parent_notify/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: type `#!python ada`, submit, and the parent's paragraph reads `#!python searching for 'ada'...`.

What you must not do is call the parent's function from an Effect that watches a value. Handlers run once per user action; Effects run once per dependency change, which includes renders the user never caused. There is also no `#!python use_imperative_handle` for the reverse direction — pass data down as props and callbacks up as arguments ([Sharing State Between Components](./sharing-state-between-components.md)).

### Chains of computations

When several values feed each other, keep the whole chain in render. Each intermediate is a local variable, not a state variable:

```python linenums="0"
@component
def report(rows, currency):
    priced = [(*row, row[1] * RATES[currency]) for row in rows]
    total = sum(item[-1] for item in priced)
    heading = f"{currency.upper()}: {total:,.2f}"
    return html.div(html.h1(heading))
```

An Effect at any link in that chain means every upstream change costs an extra full render — and, as above, each of those renders is visible to the client. If one link is genuinely expensive, wrap _that one_ in `#!python use_memo` rather than putting the whole chain in state.

### Initializing the application

Code that should run once per process does not belong in a component at all — a component's Effect runs once **per connection**, and a server serves many connections:

```python linenums="0"
# module level, or the ASGI app's startup: runs once
configure_logging()
POOL = create_pool()
```

Keep a `#!python dependencies=[]` Effect for work that is genuinely per-connection, such as a subscription or a session-scoped task. Never guard a process-level side effect with `#!python my_component.started = True`: the function object is module-scope, so the first visitor flips the flag for everyone ([VDOM Mutations](./vdom-mutations.md)).

## Subscribing to an external store

Here is the case where the Effect is correct. The value does not live in ReactPy at all, so there is nothing to derive it from — ReactPy has to be told when it changes:

=== "app.py"

    ```python
    {% include "../../examples/you_might_not_need_an_effect/external_store/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: pressing **Tick** once shows `#!python 1 ticks`; pressing **Stop watching** unmounts the view and leaves `#!python 0` listeners registered on the store.

Three things make this one legitimate where the others were not:

1.  **The source of truth is outside ReactPy.** Deriving would mean reading `#!python clock.get()` during render, which has no way to know when to run again.
2.  **The subscription needs a lifetime,** and the clean-up is what returns the store to zero listeners.
3.  **The state exists to trigger a render** — that is its whole purpose.

This is also where `#!python use_async_effect` earns its place, when the external system is an `#!python async` stream rather than a callback. See [Synchronizing with Effects](./synchronizing-with-effects.md) for cancellation and the four-way dependency table.

## Fetching data, without the extra Effects

Fetching genuinely needs an Effect — the network is external. Everything you would otherwise stack on top of it does not. Store the response, and shape it in render:

=== "app.py"

    ```python
    {% include "../../examples/you_might_not_need_an_effect/transform_data/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: the Effect stores the raw response; the labels, the per-row formatting, and the total are computed during render. One request per report name (`#!python ['orders', 'users']`), and no `#!python rows` or `#!python total` state variables that could fall out of step with the response.

The example carries one more lesson in its state shape. It stores the response **together with the name that produced it** and derives the read:

```python linenums="0"
raw = loaded["data"] if loaded["name"] == name else {}
```

Storing the response alone looks fine and is wrong: switch from `#!python orders` to `#!python users` and the component re-renders immediately, before the new response arrives, so the client receives `#!python users: 55 total` above the *orders* rows — 55 being orders' total. Measured, and the derived read above is what fixes it, without remounting the component.

The anti-pattern is a second Effect that watches the response and sets three more state variables from it. Each of those is a value you can calculate, and each adds a render in which the page is half-updated.

Because ReactPy already runs on the server, there is usually a better option than fetching in the child at all: **fetch in a parent during render, or at startup, and pass the result down as a prop.** Then the child has no Effect and no loading state, and the response is shared rather than re-requested. Keep the Effect for data that depends on something only the connection knows, like [`#!python use_location`](../reference/use-location.md).

## How to tell whether an Effect is necessary

| The Effect... | Verdict |
| --- | --- |
| reads state or props and sets other state | unnecessary — compute it during render |
| caches a calculation | unnecessary — `#!python use_memo` |
| resets state when a prop changes | unnecessary — pass a `#!python key` |
| invalidates state when a prop changes | unnecessary — derive the read from what it belonged to |
| runs logic shared by two handlers | unnecessary — call a function |
| reacts to a user action | unnecessary — put it in the event handler |
| calls a parent's callback when a value changes | unnecessary — call it from the handler |
| subscribes to a queue, socket, or store | **necessary**, with a clean-up |
| starts `#!python async` work that outlives the render | **necessary**, with `#!python use_async_effect` |
| starts per-connection work on mount | **necessary**, with `#!python dependencies=[]` |

If you cannot name what the Effect is synchronizing with, it is probably doing a render's job.

!!! warning "Two failure modes that cost hours"

    -   **An Effect that sets state it depends on loops silently.** ReactPy has no loop detector. Measured: 86 renders and counting before the probe stopped.
    -   **Hooks do not work inside an effect body.** `#!python use_context`, `#!python use_state`, and friends all raise `#!python RuntimeError: No life cycle hook is active. Are you rendering in a layout?` — effects run in their own task, with no hook on the stack. Read what you need **during render** and let the closure carry it in. The traceback appears only in the server log; the page just goes quiet.

## Recap

-   An Effect runs after a render. If the work could happen **during** the render, it should.
-   Values calculated from props or state are not state. Compute them; do not store and re-sync them. Measured: the Effect version costs twice the renders and ships a wrong first frame.
-   `#!python use_memo` caches expensive calculations without adding a render — but it caches values, not component renders.
-   Reset state with a `#!python key`, not with an Effect.
-   ReactPy cannot use React's render-phase setter trick: the stale patch reaches the client. Derive the value instead.
-   Sharing logic between handlers, notifying a parent, and submitting a form are all handler work.
-   Subscriptions and async streams are the real use for Effects — with a clean-up, always.

## Related

-   [Synchronizing with Effects](./synchronizing-with-effects.md) — how Effects work, and their four-way dependency table
-   [Choosing the State Structure](./choosing-the-state-structure.md) — avoid redundant state in the first place
-   [Preserving and Resetting State](./preserving-and-resetting-state.md) — resetting with `#!python key`
-   [Use Memo](../reference/use-memo.md) and [Use Callback](../reference/use-callback.md)
-   [Separating Events from Effects](./separating-events-from-effects.md) — the remaining case where reading fresh state matters
