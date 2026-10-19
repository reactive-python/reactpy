## Overview

<p class="intro" markdown>

A custom Hook is a plain Python function whose name starts with `use_` and which calls other Hooks. It lets you reuse stateful *logic* between components — each caller still gets its own state, and nothing about it is special to ReactPy beyond the naming convention that marks it as subject to the rules of Hooks.

</p>

!!! summary "You will learn"

    -   How to extract a custom Hook, and what it does and does not share
    -   Why each call site gets independent state
    -   Why passing a callback into a Hook silently freezes it
    -   What actually happens when a Hook is called conditionally
    -   Why the `#!python use_` prefix is a contract rather than a style choice

## Custom Hooks: sharing logic between components

Consider a shopping list where each row can be selected. The selection logic is stateful, and a second screen will need it too. Pulling it out gives you a function that reads like a Hook and behaves like one:

=== "app.py"

    ```python
    {% include "../../examples/reusing_logic_with_custom_hooks/extract_hook/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: pressing **apple**, **cheese**, **bread**, then **apple** again walks the counter `1 → 2 → 3 → 2` and the total follows it. Nothing about `#!python use_cart` is registered, exported, or declared — it is an ordinary function that happens to call `#!python use_state`.

Two rules make it a Hook rather than a helper:

-   Its name starts with `#!python use_`. This is not cosmetic; see below.
-   It is called during rendering, at the top level of a component or another Hook — never in an `#!python if`, a loop, a callback, or after an early return.

### The `#!python use_` prefix is a contract

ReactPy never inspects the name. A function called `#!python get_form` that calls `#!python use_state` behaves exactly like one called `#!python use_form`, and neither gets special treatment at runtime. The prefix is how a **reader** knows the function is subject to the rules of Hooks: it must be called at the top level of a component or another Hook, on every render, in the same order. That is the whole payoff — and it is what stops a conditional call from quietly corrupting state two functions away, which no error would otherwise reveal.

Write them in `#!python use_snake_case`: `#!python use_form`, not `#!python useForm` (which reads like a class, not a render-time call) and not `#!python get_form` (which reads like a helper a caller might safely reach for inside an event handler).

!!! info "Not every render-time function needs the prefix"
    Add `#!python use_` when the function calls Hooks. Leave it off when it does not — a `#!python format_rows()` or `#!python total_price()` is an ordinary function, and prefixing it claims a contract it does not keep.

## Custom Hooks share logic, not state

A common fear is that a Hook is a singleton. It is not: state is stored per **call site**, in order. Call the same Hook twice in one component and you get two independent boxes.

=== "app.py"

    ```python
    {% include "../../examples/reusing_logic_with_custom_hooks/isolated_state/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: pressing **left** gives `#!python left ON right off`; pressing **right** gives `#!python left ON right ON`; pressing **left** again gives `#!python left off right ON`. Same function, same arguments, two unrelated pieces of state — and `#!python both on` only when both are flipped.

The same Hook called from two different components is equally independent, since each component instance has its own Hook slots. There is no shared registry, no module-level store, and no `#!python Context` involved.

This is also why a custom Hook is not a place to put values you want everyone to see. For that, pass props or use `#!python create_context` ([Passing Data Deeply with Context](./passing-data-deeply-with-context.md)).

## Passing reactive values between Hooks

A Hook receives plain values during render and returns plain values. It re-runs whenever its caller re-renders, so it sees the same props and state the caller does.

```python linenums="0"
def use_selection(items, limit):
    selected, set_selected = use_state([])
    too_many = len(selected) > limit          # re-evaluated every render
    return selected, set_selected, too_many
```

What you cannot do is pass a *callback* in and list it as a dependency.

### The callback you pass in will go stale

`#!python use_polling` below takes a result handler and lists it as the Effect's dependency — which looks exactly right, and never works:

=== "app.py"

    ```python
    {% include "../../examples/reusing_logic_with_custom_hooks/callback_dep/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: press **Topic** once so the page reads `#!python Topic newsx`, and the line still says `#!python handler saw topic=news`. The poll counter keeps climbing, so it looks alive — but it is calling the handler from the *first* render, forever.

The reason is in `core/hooks.py`, `#!python strictly_equal`: a `#!python def` nested in a component is compared by its `#!python co_*` bytecode attributes, not by identity. `#!python on_result` re-created on the next render compares code-equal, so the dependency never changes and the Effect is never replaced.

The fix is to keep the callback in a ref that is refreshed during render, and leave it out of the list:

=== "app.py"

    ```python
    {% include "../../examples/reusing_logic_with_custom_hooks/handler_argument/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: after changing the topic, the same line reads `#!python (topic was newsx)`. The Effect still has exactly one dependency; only the ref's contents changed.

This is the same trap as a locally defined function used as an Effect dependency ([Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md)), and it is nastier inside a Hook because the code that lists the dependency and the code that created the callback live in different files.

## When a Hook is called conditionally, nothing fails

This is the section React's version of the page does not need, because React's compiler and dev-mode warnings are not present here.

ReactPy matches Hooks to their state slots **by call order**. Nothing names them, and nothing checks them. When the number of Hooks called changes between renders, the slots shift and values land in the wrong variables:

=== "app.py"

    ```python
    {% include "../../examples/reusing_logic_with_custom_hooks/hook_order_violation/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified: press **bio=** twice, then **toggle nickname**. The page prints

```text linenums="0"
bio=bio!!          # before the branch changes
bio=nickname       # after — bio is now nickname's state
```

No exception. No warning. No log record — the probe captured a completely silent `reactpy` logger across the whole transition. `#!python bio` is the third Hook when the branch is taken and the second when it is not, so after the flip it reads the box that `#!python nickname` used to own.

The corrected version calls every Hook unconditionally and makes only the *return value* conditional:

=== "app.py"

    ```python
    {% include "../../examples/reusing_logic_with_custom_hooks/hook_order_safe/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified with the same script: `#!python bio=bio!!` before and after the toggle. The toggle now changes only what is displayed.

### What nothing will catch

ReactPy raises for neither of the two broken shapes above. A Hook under an `#!python if` inside a custom Hook is perfectly legal Python, and the layout simply walks the component's state list by position:

-   a call that **disappears** on some renders shifts every later Hook into its neighbour's slot — silently, with nothing logged;
-   a call that **appears** raises `#!python IndexError: list index out of range` and blanks the region unless `#!bash REACTPY_DEBUG=1` is on;
-   the *order* Hooks actually run in is a runtime property, and there is no assertion for it anywhere.

So the rule is the fix, not a checker: Hooks at the top level, always, on every render. The dependency-list half of the rules is the same story — see [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md#reactpy-will-not-verify-your-dependencies).

!!! danger "Do not branch to disable a Hook"
    ```python linenums="0"
    # wrong: the second Hook disappears when polling is off
    if polling:
        use_async_effect(loop, dependencies=[topic])
    ```
    Keep the call and branch inside the Hook body instead, returning `#!python None` when there is nothing to do. See [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md).

## Passing event handlers into custom Hooks

A handler is an ordinary value: pass it in, call it, done — it does not need to be a dependency, and listing it does not make it fresher (measured above). The two shapes that work:

```python linenums="0"
# the Hook calls it; the ref keeps it current
def use_polling(on_result):
    latest = use_ref(on_result)
    latest.current = on_result
    ...

# or the caller owns the callback entirely and the Hook just hands back a value
selected, toggle = use_cart(items)
```

If you find yourself wanting to *store* a callback so it stays fresh, that is the same problem `#!python useEffectEvent` solves in React — and ReactPy has no such Hook. The ref-updated-during-render idiom above is the equivalent, with the caveat that reading `#!python .current` during render makes the render depend on an external value ([Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md)).

## When to use custom Hooks

Write one when you have logic — not markup — that two components genuinely need in the same shape. Good candidates in ReactPy:

-   selection, pagination, and form-draft logic
-   a subscription or polling loop with its clean-up wired correctly
-   reading a value from a `#!python use_connection`-scoped resource
-   a compound updater that several components apply to the same kind of state

Keep them focused on a concrete use case. A `#!python use_async(fetcher, deps)` that wraps `#!python use_async_effect` in generic terms tends to encode one person's cancellation assumptions for everyone; the specific `#!python use_polling(topic, on_result)` is easier to reason about and easier to change.

Two things a custom Hook is not:

-   **A render bailout.** ReactPy has no `#!python memo`, so extracting a Hook does not reduce how often a component's body runs ([Separating Events from Effects](./separating-events-from-effects.md)).
-   **A state container.** It cannot share state between components; only props and Context can.

## Recap

-   A custom Hook is a function named `#!python use_*` that calls Hooks; extract one to reuse stateful logic.
-   State is per call site, in call order: the same Hook called twice is two independent boxes (verified).
-   Name them `#!python use_snake_case`. ReactPy never reads the name — the prefix is the only signal to a reader that the function must be called at the top level of a render.
-   Never list a callback you were handed as a dependency: it compares code-equal and freezes the Effect on the first render. Read it through a ref updated during render.
-   Conditional Hook calls do not raise; state slots shift and values silently migrate between variables (verified: `#!python bio` became `#!python nickname`). Call every Hook unconditionally and branch on the return value.
-   Nothing checks the rules of Hooks for you — not the order, not the dependency list. Prove a Hook with a `#!python Layout` test, not with a glance.

## Related

-   [Synchronizing with Effects](./synchronizing-with-effects.md) — the Effect patterns a Hook will most often wrap
-   [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md) — `#!python strictly_equal`, frozen closures, and silent Effect failures
-   [Separating Events from Effects](./separating-events-from-effects.md) — handlers, and why identity buys nothing here
-   [Rules of Hooks](../reference/rules-of-hooks.md) and [Components and Hooks Must Be Pure](../reference/components-and-hooks-must-be-pure.md) — the constraints a Hook inherits
-   [Use State](../reference/use-state.md) and [Use Ref](../reference/use-ref.md) — parameter-level reference
