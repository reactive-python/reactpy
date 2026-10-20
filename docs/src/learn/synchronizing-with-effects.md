## Overview

<p class="intro" markdown>

Some components need to synchronize with an external system: send an analytics log when a page appears, keep a third-party object in step with state, or hold a connection open while a view is on screen. _Effects_ let you run code after a render so a component can talk to something outside of ReactPy.

</p>

!!! summary "You will learn"

    -   What an Effect is, and how it differs from an event handler
    -   How to declare one, and when it re-runs
    -   Why ReactPy infers dependencies instead of requiring an array
    -   How to write a clean-up function, and what happens if you skip it
    -   How to read the newest state from a long-lived Effect

!!! abstract "Note"

    Capitalized "Effect" means the ReactPy-specific idea above: a side effect caused by rendering. "side effect" keeps its ordinary programming meaning.

## What are Effects and how are they different from events?

Every ReactPy component contains two kinds of logic:

-   **Rendering code** (introduced in [Your First Component](./your-first-component.md)) sits at the top level of the component body. It takes props and state, does the math, and returns VDOM. [Rendering code must be pure.](./keeping-components-pure.md) It may only _calculate_; it may not do.

-   **Event handlers** (introduced in [Responding to Events](./responding-to-events.md)) are functions defined inside the component that ReactPy runs only when the user does something. They contain side effects — posting a form, updating a field — triggered by a specific interaction.

That covers most needs. But some work belongs to neither bucket. A chat view must connect to the server whenever it appears on screen, no matter which click or keystroke caused it to appear. There is no event for "this component was rendered", and putting the connection in the render body would break purity.

**An Effect declares side effects caused by rendering itself, rather than by a particular event.** It runs after the render is finished, in the connection's own task.

## You might not need an Effect

**Do not reach for an Effect first.** Effects exist to step outside ReactPy and synchronize with something that is not ReactPy: a network connection, a queue, a third-party library, the filesystem. If your logic only adjusts one piece of state in response to another, or computes a value from state you already have, it belongs in the render — see [You Might Not Need an Effect](./you-might-not-need-an-effect.md).

## How to write an Effect

Three steps:

1. **Declare it.** ReactPy registers the Effect for the render that created it.
2. **Say when it re-runs.** By default ReactPy _infers_ this from your closure, which is not what React does.
3. **Add a clean-up if it needs one.** Everything that opens, subscribes, or schedules needs the matching close, unsubscribe, or cancel.

### Step 1: Declare an Effect

Import the hook and call it at the top level of your component:

```python linenums="0"
from reactpy import use_effect
```

Pass it a plain function that takes no arguments:

```python linenums="0"
@component
def my_component():
    def effect():
        print("on screen")

    use_effect(effect, dependencies=[])
    ...
```

Or use it as a decorator. Because this particular Effect reads nothing from the component, that behaves the same way:

```python linenums="0"
@use_effect
def effect():
    print("on screen")
```

The decorator does **not** pin the dependency list, though. Written this way ReactPy infers the dependencies from the Effect's closure, exactly as it does when you call `#!python use_effect(effect)` without a `#!python dependencies` argument — so an Effect that reads a state variable re-runs whenever that value changes. `#!python @use_effect` means "infer", not "never again"; say `#!python @use_effect(dependencies=[])` when you want mount-only. And `#!python @use_effect()` with empty parentheses is worse than either: the function never reaches the inference, the dependencies become `#!python None`, and the Effect re-runs after **every** render (verified: three renders, three runs, against one run for the same Effect with `#!python dependencies=[]`).

Here is a working component. Open the server console and press **Re-check**: the log line appears once, on mount, and never again — the Effect does not depend on `#!python visit_count`:

=== "app.py"

    ```python
    {% include "../../examples/synchronizing_with_effects/declare_effect/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Two things about timing are worth stating precisely, because they differ from what a React tutorial will tell you:

-   An Effect is scheduled **after your component's render is complete**, not after the browser has painted. The task is created at the end of the render (`core/_life_cycle_hook.py`, `affect_layout_did_render`), and the update message has not necessarily reached the socket yet. Measured directly, an Effect's first line ran *before* `#!python layout.render()` returned to the backend. So never assume the user can already see the result.
-   **The Effect does not delay the render.** `#!python layout.render()` does not await your effect body; the two interleave on the event loop. If you need ordering, express it in state: have the Effect set state and let the next render depend on it.

!!! warning "SSR executor effects run on the server"

    When using SSR, there is no `#!python document` and no `#!python window`. An Effect cannot measure an element, focus a field, or attach a scroll listener, because there is no DOM where it runs. For browser-side behaviour see [Manipulating the DOM with Refs](./manipulating-the-dom-with-refs.md) and [Creating VDOM Event Handlers](./creating-vdom-event-handlers.md).

!!! warning "`#!python use_effect` rejects `#!python async def`"

    ```text linenums="0"
    TypeError: `use_effect` does not support async functions. Use `use_async_effect` instead.
    ```

    The failure is loud with `#!python REACTPY_DEBUG` on: the model comes back as `#!python {"tagName": "", "error": "TypeError: ..."}` and the region renders empty (with debug off you get the empty region and a traceback in the server log only). Anything `#!python await`-based belongs in [`#!python use_async_effect`](../reference/use-async-effect.md), whose effect takes **zero** arguments..
### Step 2: Specify the Effect dependencies

Pass the `#!python dependencies` argument to control when the Effect re-runs — and note that ReactPy gives this argument **four** meanings where React has two:

| Value | When the Effect runs (verified) |
| --- | --- |
| `#!python dependencies=[a, b]` | On mount, then whenever `#!python a` or `#!python b` changes. |
| `#!python dependencies=[]` | Once, on mount. |
| `#!python dependencies=None` | After **every** render. |
| omitted | **Inferred** from the free variables of your closure. |

That last row is the one that bites people porting code from React. In React, omitting the array means "run after every render". In ReactPy it means "re-run when the names my closure reads change" — `core/hooks.py`, `_try_to_infer_closure_values` reads `#!python func.__closure__` and uses those cells as the dependency list. Here the Effect reads `#!python count` and nothing else, so **Rename** re-renders the component without re-running the Effect:

=== "app.py"

    ```python
    {% include "../../examples/synchronizing_with_effects/inferred/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Press Rename twice and no new log line appears; press Add 1 and one appears per increment. Verified.

!!! warning "Dependencies are not compared by identity"

    The docstrings for these hooks say dependencies are compared by `#!python id`. They are not. `core/hooks.py`, `strictly_equal` gates on the type first, then uses `#!python ==`, and for two locally defined functions it compares their bytecode. In practice: a freshly built `#!python [1, 2]` does **not** re-trigger an Effect that listed the previous equal list, and neither does a structurally identical local `#!python def` — which means an Effect listing a local function as its dependency keeps the closure it captured first and reads stale state permanently. Both were measured. List the values, not wrappers around them.

!!! tip "Write the list out"

    Inference is invisible, so an Effect that happens to read one extra local variable quietly gains a dependency, and one that reads nothing re-runs never. If the Effect runs more or less often than you meant, look at which names the body actually reads. An explicit list removes the guesswork, and `#!python dependencies=[]` and `#!python dependencies=None` are honest too.

!!! warning "Declare state before the Effects that read it"

    ```python linenums="0"
    use_effect(effect)  # effect reads `count`
    count, set_count = use_state(0)
    ```

    ReactPy reads the closure's cells while resolving dependencies, and `#!python count`'s cell is not filled yet: `#!python ValueError: Cell is empty`. The component renders as a blank region, with the error in the model (debug on) or in the server log (debug off). State first, Effects after.

### Step 3: Add clean-up if needed

Return a function from the Effect. ReactPy runs it **before the next run of that same Effect** and again **when the component unmounts**:

=== "app.py"

    ```python
    {% include "../../examples/synchronizing_with_effects/cleanup/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Switch rooms and the server log reads `#!python connect lobby`, `#!python close lobby`, `#!python connect dev` — the teardown for the old room runs before the new one starts. Press **Leave** and the last connection closes. Verified.

This matters more in ReactPy than in React because of process lifetime. A closed browser tab destroys everything with it. A ReactPy server does not: a subscription you forgot to release is still live after the user went home, still holding your component, still firing callbacks into a view nobody can see. The counter-proof, measured in a `#!python Layout`:

| Effect body | Subscribers after 4 renders | One publish fires | After unmount |
| --- | --- | --- | --- |
| returns nothing | 4 | 4 callbacks | 4 still attached |
| returns `#!python unsubscribe` | 1 | 1 callback | 0 |

Same component, same re-renders. Without the clean-up, one message ran the handler four times.

!!! info "Clean-up is what makes restarts free"

    Whenever a dependency changes, ReactPy stops the old Effect and starts a new one. The rule of thumb is that nobody should be able to tell whether the Effect ran once or ran _setup → cleanup → setup_. Write it that way and restarts cost nothing; skip the clean-up and every dependency change leaks.

## Reading the newest value from a long-lived Effect

Here is the trap that bites hardest with `#!python use_async_effect`. An Effect's body closes over the render that created it. If that Effect then lives a long time — a polling loop, a subscription — it acts on values that are already stale.

The fix is to keep the value in a [ref](./referencing-values-with-refs.md), assigning it during render. The ref object is the same one on every render, so a reader that wakes up later sees the newest write:

=== "app.py"

    ```python
    {% include "../../examples/synchronizing_with_effects/latest_state/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Toggle the threshold from 50 to 10 and alerts start appearing; toggle back and they stop. The single long-lived task never restarts and always reads the current number. Verified.

The alternative — usually the better one — is to put the value in the dependency list so a change tears the Effect down and builds a new one with fresh values. Use the ref when restarting is expensive: an open socket, a loop with accumulated state.

## Common patterns

### Synchronizing with a non-ReactPy object

Third-party objects are imperative: you construct them, call setters, destroy them. State is the wrong home for one (constructing it would re-run each render, and setting it would trigger a render), so keep it in a ref and let Effects drive its lifecycle:

=== "app.py"

    ```python
    {% include "../../examples/synchronizing_with_effects/non_react_widget/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```reactpy-run
    props: name="Q3 Report"
    ```



Two Effects, two dependency lists: one creates and destroys the object when `#!python name` changes, the other pushes `#!python page_size` into it. Verified against the object's own log: `#!python created q3`, `#!python set_page_size letter`, `#!python set_page_size a4`, `#!python destroyed q3` on unmount — one instance, kept in step, cleaned up.

Two Effects in the same component run in declaration order, which is why `#!python create_engine` is registered first: the second Effect can assume the object exists. That ordering holds *within* a component; across components it does not. **Children's Effects run before their parent's, and siblings run in reverse order** — measured `#!python ['child effect b', 'child effect a', 'parent effect']`. Never write code that needs a parent to have run first.

### Subscribing to a stream

The shape is always the same: subscribe inside the Effect, unsubscribe in the clean-up, name the topic in the dependency list:

=== "app.py"

    ```python
    {% include "../../examples/synchronizing_with_effects/subscribe/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified through the bus's own log: `#!python subscribe news`, `#!python unsubscribe news`, `#!python subscribe sports`, `#!python unsubscribe sports`, `#!python subscribe news`, `#!python unsubscribe news` across a full switch-and-leave cycle — exactly one subscriber live at any moment.

Note that the callback is defined *inside* the Effect, so it closes over this Effect's values and the subscription is rebuilt when the dependencies change. Defining it in the component body instead would leave the subscription holding the first version of it.

### Fetching data

Fetching belongs in `#!python use_async_effect`, and cancellation is what makes it safe:

=== "app.py"

    ```python
    {% include "../../examples/synchronizing_with_effects/fetching/app.py" start="# start" %}
    ```

=== ":material-play: Run"

The example is deliberately lopsided: `#!python orders` takes 0.8 s and `#!python users` takes 0.05 s. Press **Toggle report** while the slow one is in flight and the screen settles on `#!python users: 500 rows` and stays there. The data source recorded that it computed **only** the `#!python users` answer — the `#!python orders` task was cancelled inside its `#!python await` and never reached its `#!python set_rows`. Verified.

That is ReactPy's version of React's `#!python ignore` flag, and it is stronger: the cancelled run's remaining lines never execute at all. Two consequences:

-   Code after an `#!python await` may never run. Anything that must happen — closing a handle, releasing a lock — goes in a `#!python try` / `#!python except asyncio.CancelledError` pair, and re-raises so asyncio can finish cancelling.
-   An Effect that sets state it depends on loops forever. If a component appears to spin, read what the Effect awaits, what it depends on, and what it sets.

!!! info "Good alternatives to fetching in an Effect"

    Manual fetching in an Effect works, and carries the same drawbacks here as in React: no deduplication, no cache shared between components, and a request that cannot start until the component exists. ReactPy has a better option available by default — **fetch during a parent's render, or at startup, and pass the result down as a prop.** The child then renders with data instead of loading it. Keep the Effect for data that genuinely depends on something only the connection knows, such as [`#!python use_location`](../reference/use-location.md).

### Sending analytics

Report a page view when the page changes, not when the component happens to render:

=== "app.py"

    ```python
    {% include "../../examples/synchronizing_with_effects/analytics/app.py" start="# start" %}
    ```

=== ":material-play: Run"

The Effect depends on `#!python path` only. Type into the field and the report count stays put; press **Navigate** and it climbs by one. Verified: two typing re-renders produced zero reports, two navigations produced two.

### Not an Effect: initializing the application

Logic that should run once for the whole process does not belong in a component at all — a component's Effect runs once **per connection**, and a server serves many:

```python linenums="0"
# module level: runs when the module is imported, once
configure_logging()
POOL = create_pool()
```

Put it in the ASGI app's startup, or in the module that builds the `#!python ReactPy` executor. Reach for a `#!python dependencies=[]` Effect only when the work is genuinely per-connection. Never guard it with `#!python my_component.started = True`: the function object is module-scope, so the first visitor flips the flag for everyone ([VDOM Mutations](./vdom-mutations.md)).

### Not an Effect: buying a product

An Effect is not the place for something that must happen exactly once per user action, because you cannot promise how many times an Effect runs — dependencies change, components unmount, processes restart. Charging a card belongs in an event handler, where a click is the only trigger:

```python linenums="0"
async def handle_buy(event):
    set_status("buying...")
    order = place_order(sku)
    set_status(f"ordered {order.id}")
```

## Deep dive: each render has its own Effects

An Effect belongs to the render that created it. Its closure holds that render's props and state, and it never sees a later one. The dependency list chooses *which* render's Effect survives; it does not update the one that did:

=== "app.py"

    ```python
    {% include "../../examples/synchronizing_with_effects/per_render/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Press **Type !** twice, then **Switch room**. The log gains `#!python lobby <- hello` from the mount, and then `#!python dev <- hello!!` — the Effect that ran for `#!python dev` was created by the render whose `#!python message` was already `#!python 'hello!!'`. Verified. No entry ever records an intermediate message, because only the renders whose dependencies changed created an Effect.

This is why "my Effect reads an old value" has exactly two correct answers: add the value to the dependency list, or read it through a ref.

## There is no double-invoke in development

React remounts every component twice under Strict Mode to expose Effects that are not restart-safe. **ReactPy has no Strict Mode and never calls your component twice** — verified: a component that increments a counter in its own body counted exactly one render per render.

Two consequences:

-   **Nothing will find your unclean Effects for you.** The restart-safety check React gives away for free is one you have to run yourself: render the component, unmount it, mount it again, and assert the external system is back where it started. A `#!python reactpy.core.layout.Layout` in a pytest makes that a ten-line test.
-   **Do not add artificial guards to compensate.** `#!python if already_ran.current: return` inside an Effect is evidence the dependency list is wrong, not a fix. Write the clean-up so a restart is free and the question stops mattering.

## Recap

-   An **Effect** is a side effect caused by rendering; an **event handler** is one caused by a user action. Prefer the handler.
-   Effects are scheduled after the render completes, in the connection's own task. They do not block the render, and the browser may not have the update yet.
-   They run on the **server**: no DOM, no `#!python window`, no element to focus.
-   `#!python use_effect` takes a plain `#!python def`; `#!python use_async_effect` takes a zero-argument `#!python async def`. One mismatch fails loudly, the other (the old `#!python async def effect(stop)` shape) fails silently.
-   `#!python dependencies` has four settings. Omitted means **inferred from the closure**, not "every render" — and the comparison is `#!python ==`, not identity.
-   Return a **clean-up** function. It runs before the Effect's next run and on unmount. Skipping it leaks, and a leak in a long-lived server process leaks forever.
-   A long-lived Effect sees a frozen snapshot; read current values from a ref, or restart the Effect by depending on them.

## Related

-   [Use Effect](../reference/use-effect.md) and [Use Async Effect](../reference/use-async-effect.md) — full parameter reference
-   [You Might Not Need an Effect](./you-might-not-need-an-effect.md) — the cases that belong back in the render
-   [Separating Events from Effects](./separating-events-from-effects.md) — reading the newest state without restarting an Effect
-   [Removing Effect Dependencies](./removing-effect-dependencies.md) — when to omit a dependency, safely
-   [Referencing Values with Refs](./referencing-values-with-refs.md) — the box that survives renders
