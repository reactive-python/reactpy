## Overview

<p class="intro" markdown>

A component whose state is updated by many handlers spread across its body gets hard to reason about. A reducer moves every update rule into one pure function, so the handlers say only what the user did. In ReactPy there is one rule to learn on top of React's: the reducer you pass on the first render is the one ReactPy keeps, so a reducer defined inside the component body closes over frozen values.

</p>

!!! summary "You will learn"

    -   What a reducer is, and how dispatching differs from setting
    -   Why ReactPy keeps the first reducer, and what that forbids
    -   Where a ReactPy reducer actually runs, and what that means for purity
    -   When a reducer is worth the extra code

## Consolidate state logic with a reducer

This component holds a list of tasks and updates it from three handlers:

=== "app.py"

    ```python
    {% include "../../examples/extracting_state_logic_into_a_reducer/tasks_state/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Each handler knows how to rebuild the list. That is fine at three handlers and one field. It stops being fine when a fourth handler appears, when a second field has to change alongside `#!python tasks`, or when you are debugging which of the four produced a wrong list — and here `#!python handle_add_task` already has to keep two state variables in step.

Managing state with a reducer inverts it. Instead of telling ReactPy *what to do*, each handler says *what just happened*, and one function decides what that means:

=== "app.py"

    ```python
    {% include "../../examples/extracting_state_logic_into_a_reducer/tasks_reducer/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Both examples are verified to behave identically — add twice, toggle, delete produces the same readouts and the same single flipped row in each. The difference is where the knowledge lives. The handlers now read as a list of user intentions:

-   `#!python dispatch({"type": "added"})`
-   `#!python dispatch({"type": "toggled", "id": task_id})`
-   `#!python dispatch({"type": "deleted", "id": task_id})`

`#!python next_id` moved into the same state object as `#!python tasks`, so `#!python added` bumps both in one return value. That is the first concrete gain: there is no longer a pair of setters that can be called in the wrong combination.

The reducer ends with `#!python raise ValueError(f"unknown action type {kind!r}")` rather than `#!python return state`. A fallthrough that silently does nothing is the hardest bug in this pattern to find, because every other symptom looks correct.

!!! abstract "Note"

    `#!python use_reducer(reducer, initial_value)` takes exactly two arguments. There is no third "init function" parameter as in some React versions. If building the initial state is expensive, pass a zero-argument callable as `#!python initial_value` — ReactPy calls it once and stores the result, the same way `#!python use_state` does.

## The rule ReactPy adds: the first reducer wins

This is the part that differs from React, and it will bite you once. `use_reducer` builds its dispatcher once and reuses it, so **the reducer function from the first render is the one that runs forever** — `core/hooks.py`, `use_reducer`.

Swapping the reducer at runtime does nothing at all:

=== "app.py"

    ```python
    {% include "../../examples/extracting_state_logic_into_a_reducer/reducer_swapped/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Press **Switch reducer** — the readout shows `#!python version=2`, so the component body really did pick `#!python add_by_hundred` — then press **Add**: `#!python by=add_by_one`. Every later action still runs the original function.

The same mechanism is subtler, and much more common, when the reducer is defined *inside* the component:

=== "app.py"

    ```python
    {% include "../../examples/extracting_state_logic_into_a_reducer/reducer_frozen_value/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Press **Add** once: `#!python count=1 total=10`. Then **Raise price**, which takes the displayed price to `#!python 50` — and press **Add** again. You get `#!python total=20`, not `#!python 60`. The line reads `#!python price=50` while the arithmetic used `#!python 10`.

Nothing crashed and nothing was logged. The reducer still holds the closure from the first render, in which `#!python item_price` was `#!python 10`. This is the frozen-effect-body problem from [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md) wearing a different hat, and it is the single most likely way to be quietly wrong with a ReactPy reducer.

The fix is the same instinct as always: keep the reducer pure *and* self-contained. Define it at module level, and let the action carry every value it needs. Handlers are not frozen — they are rebuilt each render — so a handler can read the current prop and hand it over:

=== "app.py"

    ```python
    {% include "../../examples/extracting_state_logic_into_a_reducer/reducer_action_data/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Same buttons: **Add**, **Raise price**, **Add** now gives `#!python count=2 total=60 price=50`. `#!python cart_reducer` sits at module level with no enclosing scope to freeze, and `#!python dispatch({"type": "add", "price": item_price})` supplies the live value.

So the ReactPy rule is: **a reducer must be a module-level function that reads nothing but its two arguments.** That is stricter than React's "reducers must be pure", and it costs nothing — a reducer that closes over component scope is a reducer you cannot unit-test with two plain arguments anyway.

## Where a ReactPy reducer runs

React's docs say reducers run during rendering, because React queues actions and calls the reducer at the next render. ReactPy is more direct, and the difference is worth knowing when you reach for a print statement:

```text linenums="0"
handler:enter
reducer(add)
handler:exit
render
```

Verified trace of one click. `#!python dispatch` calls your reducer *immediately*, inside the handler, then compares the result against the current state with `==` and schedules a render only if it differs — `core/hooks.py`, `_create_dispatcher`.

Three consequences:

-   **A reducer that raises surfaces as a failed event handler, not a reducer error.** Verified: dispatching an action whose branch raises `#!python ValueError` leaves the state untouched and produces zero renders. `#!python dispatch` ran the reducer inside the handler, so the exception propagates to `core/layout.py`, `Layout._process_event_queue`, which catches it and calls `#!python logger.exception` — one `#!python ERROR: Failed to execute event handler` record on the `#!python reactpy.core.layout` logger, with the reducer's traceback attached. ReactPy itself never reports "a reducer raised". The component stays mounted and keeps working for later actions.
-   **Multiple dispatches in one handler batch into one render.** Verified: three `#!python dispatch` calls in a single handler produce three reducer calls, applied in order, and **one** render.
-   **Purity is not optional, but for a different reason than in React.** Since the result is compared with `==`, mutating and returning the same object compares equal and schedules nothing.

That last one is the most common reducer bug in ReactPy, and it is silent:

=== "app.py"

    ```python
    {% include "../../examples/extracting_state_logic_into_a_reducer/reducer_mutates/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Press **Add task** three times. The rendered count stays at `#!python 2 tasks rendered` and the component body never runs again — verified at zero renders. The list did grow; the returned state compared equal to the old one, so ReactPy decided nothing had changed. Return new objects (`#!python {**state, "tasks": [*state["tasks"], task]}`), exactly as you would with `#!python use_state`.

!!! warning "Pitfall"

    `#!python return state` after modifying `#!python state` is a no-op, and so is any branch that falls through to `#!python return state`. If an action's `#!python "type"` matches no branch — a typo, a renamed constant — the dispatch is silently ignored. End the reducer with `#!python raise ValueError(...)` for unknown types instead of a bare `#!python return state`, so the mistake surfaces where it is made.

## Comparing `use_state` and `use_reducer`

-   **Code size.** `#!python use_state` needs less code upfront: a reducer *and* actions is two artefacts, not one. A reducer pays off when many handlers mutate state in similar shapes, or when one transition touches several fields at once — moving `#!python next_id` next to `#!python tasks` above is that case.
-   **Readability.** With `#!python use_state` the update logic lives in the handlers, which is where you want it while it is three lines. When handlers grow conditionals, the reducer lets you separate *how* state changes from *what happened*.
-   **Debugging.** With `#!python use_state` you must find which setter was wrong. With a reducer you can log the two arguments of one function and reconstruct the session — in ReactPy the log also tells you the order, because dispatch is eager. If each action is right, the bug is in the reducer.
-   **Testing.** A module-level reducer — which ReactPy already requires — is a plain function. `#!python tasks_reducer(state, {"type": "deleted", "id": 1})` is an assertion, no rendering involved.
-   **Render count.** Neither is cheaper. Both compare with `==` and both skip a render when the value is unchanged; neither bails out of rendering the component, because ReactPy has no `#!python memo`.

Use a reducer when a component has produced real bugs from the wrong update path, not as a default. Mixing is fine: `#!python use_state` for a draft input, `#!python use_reducer` for the form's submitted record, in the same component.

!!! info "Deep Dive"

    ReactPy has no `#!python immer` equivalent that earns its keep here, because `#!python {**state, ...}` and `#!python [*items, item]` are already the copy idioms a reducer needs. What *is* worth doing once a reducer grows past a couple of branches: make the state a frozen `#!python @dataclass`. Then a mutation raises `#!python FrozenInstanceError` at the line that did it instead of quietly comparing equal — verified, and with it the two halves that make this safe: `strictly_equal` compares dataclass instances field by field, so dispatching an action that changes nothing renders nothing, while one that changes a field renders once. Because the raise happens inside the event handler, though, it is caught like any other handler exception: it appears as a root-logger `#!python ERROR`, not on screen. Use `#!python dataclasses.replace(state, ...)`, and read the server log. See [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md) for the full comparison table.

## Writing reducers well

-   **One action per user interaction**, not per field. A "Reset" button on a five-field form should dispatch `#!python {"type": "reset_form"}`, not five `#!python set_field` actions. If you logged every action, the log should read like a transcript of the session.
-   **Actions describe what happened, not what to change.** `#!python {"type": "toggled", "id": 3}` survives a change in how toggling is displayed. `#!python {"type": "set_done", "value": True}` does not, and is usually shorter written as a setter.
-   **Put the data in the action.** `#!python {"type": "add_item", "item": item, "price": price}` — this is also exactly what keeps a ReactPy reducer honest, since the reducer cannot read live values from a closure.
-   **Keep transitions in the reducer, not in the handler.** A handler that does `#!python dispatch(...)` *and* `#!python set_something_else(...)` has two sources of truth again.
-   **Do not dispatch during render.** Dispatch is eager, so it updates the pending state while the component body is still running; the render then reflects an update that has already happened. Put it in an effect or a handler.

## Recap

-   A reducer collects every state transition in one pure function; handlers shrink to a description of what the user did.
-   ReactPy keeps the **first** reducer it is given. Verified: swapping the reducer argument changes the body, not the behaviour.
-   Therefore define reducers at **module level**, reading nothing but `#!python state` and `#!python action`. A reducer defined in the component body freezes its closure — verified charging `#!python total=20` at a displayed `#!python price=50`.
-   `#!python dispatch` runs the reducer **immediately**, inside the handler, not at the next render. Verified by trace.
-   Mutating the state and returning it compares equal, so nothing renders — verified: three presses, zero renders, no log line. Return new objects.
-   A raising reducer surfaces as `#!python ERROR: Failed to execute event handler` from `#!python reactpy.core.layout`, not as a reducer error; end the reducer with `#!python raise ValueError` so unknown actions surface.
-   Several dispatches in one handler apply in order and cost one render (verified).
-   `use_reducer` takes two arguments; pass a callable as `#!python initial_value` to build it lazily, once.

## Related

-   [Choosing the State Structure](./choosing-the-state-structure.md) — the `==` comparison and the copy idioms a reducer depends on
-   [Queueing a Series of State Updates](./queueing-a-series-of-state-updates.md) — functional updaters, the `#!python use_state` sibling of dispatch
-   [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md) — frozen closures and `strictly_equal`, the two mechanisms behind the traps on this page
-   [Passing Data Deeply with Context](./passing-data-deeply-with-context.md) — how to hand `#!python dispatch` to distant components
-   [Use Reducer](../reference/use-reducer.md) — parameter-level reference and troubleshooting
