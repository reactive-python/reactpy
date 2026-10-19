## Overview

<p class="intro" markdown>

A reducer keeps a component's update logic in one pure function; context carries values past components that only forward them. Together they let a deep tree read and change shared state without any wiring through props. In ReactPy there is one extra fact that makes this work cleanly: `#!python dispatch` has a stable identity across renders, so it is safe to put in a context value.

</p>

!!! summary "You will learn"

    -   How to combine a reducer with context, in three steps
    -   Why `#!python dispatch` is safe to share through context in ReactPy
    -   How to move all the wiring into a single module the UI never imports from directly

## Combining a reducer with context

Start with the version where state and dispatch travel as props. Only `#!python task_form` and `#!python task` want `#!python dispatch`, but it has to be handed to everyone in between:

=== "app.py"

    ```python
    {% include "../../examples/scaling_up_with_reducer_and_context/task_state_props/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Read the signatures: `#!python task_list(state, dispatch)` receives both and reads neither — it only builds children and passes both along. `#!python task` forwards `#!python state` untouched to `#!python task_form`, which uses only `#!python dispatch`. Every new layer in the middle copies the same two parameters.

The reducer is already correct for ReactPy: module-level, reading nothing but its two arguments, returning new objects, and raising on an unknown action type. See [Extracting State Logic into a Reducer](./extracting-state-logic-into-a-reducer.md) for why each of those matters here.

### Step 1: Create the context

One context carries both halves — the state to read and the dispatch to change it with. Keep it beside the reducer, in a module that does not import the UI:

=== "app.py"

    ```python
    {% include "../../examples/scaling_up_with_reducer_and_context/task_context/app.py" start="# start" %}
    ```

=== "tasks.py"

    ```python
    {% include "../../examples/scaling_up_with_reducer_and_context/task_context/tasks.py" %}
    ```

=== ":material-play: Run"

Two things to notice in `#!python tasks.py`.

The context object is matched by identity, so create it once and import it from here everywhere. The annotation is load-bearing: `#!python create_context` infers the value type from its default, so without `#!python Context[TaskValue]` a type checker fixes the value to the default's shape and rejects a real one. Write the default first, then annotate. See [Use Context](../reference/use-context.md#caveats).

The default value is a *usable* value, not `#!python None`: an empty state and a dispatch that does nothing. A component rendered without a provider then renders an empty list instead of crashing when a handler fires.

### Step 2: Put state and dispatch into context

Call `#!python use_reducer` once, in the component that owns the state, and provide both halves:

```python linenums="0"
state, dispatch = use_reducer(tasks_reducer, INITIAL_STATE)
...
TaskContext(task_list(), value=(state, dispatch))
```

A tuple is the simplest value that carries both. If you prefer a dict or a dataclass, the same rules apply — but do not expect the value to control how often consumers render. ReactPy compares nothing here: `use_context` hands back whatever the provider is currently holding, and a provider that re-renders re-renders its children whether the value is new, equal, or literally the same object. Re-render cost is governed by where you place the provider, not by how you build the value.

### Step 3: Use context anywhere in the tree

Now the middle of the tree forgets both parameters:

```python linenums="0"
@component
def task_list():
    state, _ = use_context(TaskContext)
    return html.ul([task(item, key=item["id"]) for item in state["tasks"]])
```

`#!python task_list` no longer mentions `#!python dispatch` at all, and `#!python task` and `#!python task_form` each call `#!python use_context` themselves. Verified: this version and the prop version above are behaviourally identical — the same initial two tasks, the same row struck through by **Toggle**, the same count after **Add task**, the same rows after **Delete**. All three versions in this page pass the same user-journey comparison.

!!! abstract "Note"

    `#!python use_context` reserves no state slot, so unlike `#!python use_state` it is safe to call conditionally. That is not an invitation to hide it: read it at the top of the component, the way you would a prop, so it is obvious where the value comes from.

## Why dispatch is safe to share in ReactPy

In React, sharing `#!python dispatch` through context is safe because React guarantees its identity. In ReactPy it is safe for a more concrete reason you can check in the source: `#!python use_reducer` builds the dispatcher once with `#!python _use_const` — a `#!python use_state` holding the function — and returns that same object on every render. Verified: across five renders and four dispatches, `#!python id(dispatch)` took exactly one value.

That matters because the dispatcher closes over the *reducer*, which ReactPy also freezes at the first render. A stale dispatcher is not a hazard here as long as the reducer is module-level — which is exactly the rule [the reducer page](./extracting-state-logic-into-a-reducer.md#the-rule-reactpy-adds-the-first-reducer-wins) already imposes. Share `#!python dispatch` freely; do not share a value you expect to be re-read from a closure.

What context does **not** do: it is not a render optimisation. ReactPy has no `#!python memo`, so when the provider re-renders with a new value, the whole subtree re-renders, including every component whose read value did not change. Context removes parameters, not work. See [What context does not do](../reference/use-context.md#what-context-does-not-do).

## Moving all wiring into a single file

Once the UI reads everything from context, the reducer, the context object, and even `#!python use_reducer` can disappear from it. Move the whole mechanism into `#!python tasks.py`, and expose exactly two names — a provider component and an accessor hook:

=== "app.py"

    ```python
    {% include "../../examples/scaling_up_with_reducer_and_context/task_wiring/app.py" start="# start" %}
    ```

=== "tasks.py"

    ```python
    {% include "../../examples/scaling_up_with_reducer_and_context/task_wiring/tasks.py" %}
    ```

=== ":material-play: Run"

The UI file now imports only `#!python task_store` and `#!python use_tasks`. It never mentions `#!python use_reducer`, `#!python create_context`, `#!python tasks_reducer`, or `#!python TaskContext`. Two consequences worth having:

-   The UI cannot reach the reducer except through an action, so there is no way to bypass it.
-   Changing how the state is stored — a different reducer, a different initial shape, even dropping context entirely — touches one file and no component.

`#!python task_store` is a component that calls `#!python use_reducer` and returns the provider. A component's render may return another component, so this composes without ceremony. Note that `#!python use_tasks` is a plain function that calls `#!python use_context`: it is a custom Hook, so name it `#!python use_*` — the linter's regex is `^_*use_\w+$`, and camelCase variants get a less accurate diagnostic. See [Reusing Logic with Custom Hooks](./reusing-logic-with-custom-hooks.md).

!!! warning "Pitfall"

    Because the provider is now a component, **removing it from the tree unmounts everything below it** and throws their state away. Do not write `#!python task_store(page()) if logged_in else page()`. Keep the provider in the tree and vary only its value — verified: a conditional provider resets a leaf's state (its render counter returns to 1 and its draft text clears), while a stable `#!python key` on the child does not prevent it. See [Removing a provider resets the subtree below it](./passing-data-deeply-with-context.md#removing-a-provider-resets-the-subtree-below-it).

Two `#!python task_store` instances are two independent stores, not one shared store: verified, three presses on one side moved `#!python one=5` while the other stayed at its initial `#!python two=2`. Context propagates down from the provider that happens to be above you. To genuinely share state, there must be one provider above both consumers — usually near the root.

!!! info "Deep Dive"

    Should you also provide a *derived* value, such as a filtered list or a total? Compute it in the component that needs it. ReactPy re-renders the subtree whenever the provided state changes anyway, so a cached derivation saves nothing, and `#!python use_memo` around it adds a dependency list to keep correct. Reserve the context value for what is genuinely shared: the state object and `#!python dispatch`. For the caching rules, see [You Might Not Need an Effect](./you-might-not-need-an-effect.md#caching-expensive-calculations).

## Recap

-   A reducer owns the transitions; context carries `#!python (state, dispatch)` past components that would only forward them. Both are needed together — context without a reducer leaves the update logic scattered, a reducer without context leaves the props.
-   Create the context beside the reducer, at module level, with a usable default and a `#!python Context[...]` annotation so the value type is not narrowed by the default.
-   Provide `#!python (state, dispatch)` from one component that owns `#!python use_reducer`; read it in each component that needs it.
-   `#!python dispatch` is identity-stable across renders in ReactPy (verified: one `#!python id` over five renders), which is what makes sharing it through context sound.
-   A module that exports a provider component and a `#!python use_*` accessor lets the UI import two names and never touch the reducer.
-   Keep the provider in the tree. Removing it remounts the subtree and discards state; a `#!python key` does not save it (verified).
-   One provider per shared store. Two providers are two stores (verified).
-   Context removes parameters, not renders — ReactPy has no render bailout.

## Related

-   [Extracting State Logic into a Reducer](./extracting-state-logic-into-a-reducer.md) — the reducer rules this pattern depends on, including the frozen-first-reducer rule
-   [Passing Data Deeply with Context](./passing-data-deeply-with-context.md) — the context mechanics, and the provider-removal trap
-   [Use Context](../reference/use-context.md) — parameters, caveats, and error messages
-   [Use Reducer](../reference/use-reducer.md) — parameter-level reference and troubleshooting
-   [Reusing Logic with Custom Hooks](./reusing-logic-with-custom-hooks.md) — naming and rules for the `#!python use_tasks` accessor
-   [Choosing the State Structure](./choosing-the-state-structure.md) — what belongs in state before you decide who provides it
