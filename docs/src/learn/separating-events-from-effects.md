## Overview

<p class="intro" markdown>

Event handlers and Effects run at different times and for different reasons. Most Effect bugs are not Effect bugs — they are interaction logic that was put in the wrong place. Move it back and the Effect disappears.

</p>

!!! summary "You will learn"

    -   Why interaction logic belongs in a handler, not an Effect
    -   Why handler logic is *not* reactive — and why that is a feature
    -   How ReactPy picks which render's handler actually runs
    -   What `#!python use_callback` does in ReactPy, and what it does not buy you
    -   How to read the newest value from a callback you cannot re-create

## Choosing between event handlers and Effects

The question is never "which hook?" but **"when should this logic run?"**

| | Event handler | Effect |
| --- | --- | --- |
| Runs | when the interaction happens | after a render, whenever a dependency changed |
| Re-runs when | only if the user repeats the interaction | any dependency changes — including one you forgot to list |
| Right for | submit, click, input, drag, "do this now" | subscribing, polling, syncing to a server |

Both cost one render per click in the examples below — the difference is not performance, it is *what triggers the work*. An Effect that sets state it also lists as a dependency re-triggers itself; measured, that loop reached **86 renders** before it was stopped. A handler has no such feedback path, which is most of why interaction logic belongs there.

If the logic should run *when the user does the thing*, it goes in the handler. If it should run *whenever a value is a certain way*, it goes in an Effect.

### Logic in an Effect, driven by click-only state

Here the shipping quote is computed by an Effect watching a flag that only a click sets:

=== "app.py"

    ```python
    {% include "../../examples/separating_events_from_effects/intent_in_effect/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

This is where the ReactJS version of this example stops matching reality. Verified behaviour: type a city and country, then press **Get quote** three times.

-   Click 1 logs `#!python quoted Portland, US — $20`.
-   Clicks 2 and 3 increment the counter and log **nothing at all**.

`#!python set_quoted(True)` sets the same value every time, so ReactPy sees no change, and the dependency list says nothing re-synchronized. The user gets a button that works once. Nothing about this is obvious from the code — the Effect looks correct.

### The same logic in the handler

=== "app.py"

    ```python
    {% include "../../examples/separating_events_from_effects/intent_in_handler/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

No trigger state, no Effect, no `#!python use_effect` import. Verified: every click logs `#!python quoted Portland, US — $20`, at the same one-render-per-click cost as a plain button.

The general rule: **if the only thing that sets a piece of state is an event handler, and the only thing that reads it is an Effect, delete both** and call the function directly.

!!! info "When an Effect really is the right home"

    Keep the Effect when the logic must also run for reasons *other than* the interaction: the value changed while the user was idle, the component just mounted, another component changed something. "The user pressed Save" is a handler; "the document is dirty and should be persisted" is an Effect.

## Reactive values and reactive logic

Every value in the component body belongs to one render. Logic placed in the component body or in an Effect re-runs when those values change. Logic inside a handler does not — it runs when called, on whatever render produced it.

### Logic inside event handlers is not reactive

```python linenums="0"
def submit(event):
    print(f"submitting {city}, {country}")   # reads one render's values
    send(city, country)
```

Nothing about this code will re-run when `#!python city` changes. That is not a defect: a click should do the thing once, using the values the user saw when they clicked. Making handler logic "reactive" is what produces double-submits and the click-once bug above.

### Logic inside Effects is reactive

```python linenums="0"
def reconnect():
    open_socket(room)

use_effect(reconnect, dependencies=[room])
```

This one re-runs on its own whenever `#!python room` changes, including changes you did not expect. That is the whole point of an Effect — and the whole reason logic you *don't* want repeated does not belong there.

## Extracting non-reactive logic out of Effects

Once intent lives in the handler, the shared part is usually an ordinary function. Give it its inputs as parameters and both sides can use it:

```python linenums="0"
def calculate_shipping(city, country):
    if not city or not country:
        return ""
    return f"{city}, {country} — ${15 + 5}"


@component
def shipping_form():
    ...

    def submit(event):
        set_shipping_info(calculate_shipping(city, country))
```

No hook needed. A function that only *reads* values and *returns* something does not need to be a hook, and making it one costs a render.

ReactPy has no `#!python useEffectEvent`, no `#!python useOptimistic`, and no `#!python useTransition` — verified against `reactpy` 2.0.0b13. That is not a gap to route around with an Effect: the handler-is-not-reactive property that Effect Events exist to give you in React is what you already have here for free.

## Which handler actually runs

ReactPy keeps **one handler per target**, registered when the component renders (`core/layout.py`, `_event_handlers`), and looks it up at dispatch time — when the event is processed, not when it arrived.

Two things follow, both measured.

**A normal click sees current values.** Click after click with the connection settling between them, and the handler always reads the latest state:

```text linenums="0"
added item, discount=0
added item, discount=10
added item, discount=20
```

**Events that arrive before the next render all see the same snapshot.** Deliver two clicks without a render in between and both run the *same* closure:

=== "app.py"

    ```python
    {% include "../../examples/separating_events_from_effects/handler_freshness/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified with two clicks delivered back-to-back:

| | Handler log | Final list |
| --- | --- | --- |
| **Add (naive)** | `#!python 0 items` twice | `#!python item-1@0` — the second click is gone |
| **Add (safe)** | `#!python 0 items`, then `#!python 1 items` | `#!python item-1@0, item-2@0` |

This is not a hypothetical. On a real connection, events are queued per target (`core/layout.py`, `_process_event_queue`) and a double-click, a fast key repeat, or any latency between the browser and a busy server produces exactly this. The naive `#!python set_items(items + [...])` reads a snapshot; the updater `#!python set_items(lambda current: ...)` is applied against the state at the moment it lands.

So the handler-staleness story in ReactPy is narrower than in React, and it is worth being precise:

-   You generally do **not** need `#!python use_callback` to "get fresh values" in a handler — the handler that runs is the current one.
-   You **do** need the functional updater form whenever an update depends on the current state and two events can arrive in the same round trip.

### Async handlers

A handler may be `#!python async def`, and it may set state after an `#!python await`:

```python linenums="0"
async def submit(event):
    set_status("saving")
    result = await save(document)
    set_status("saved")          # works — the render happens after the await
```

Verified: the page shows `#!python status=saving` immediately, then `#!python status=saved` once the await resolves — two renders, both after the click.

But if the component unmounts during the `#!python await`, the update is **discarded** and the only trace is a debug line — `#!python Did not render component with model state ID ... - component already unmounted`. Nothing errors, nothing warns, and the user who navigated away is unaffected. Do not treat "the setter did not raise" as evidence the write landed; if it matters, assert it in a test that keeps the component mounted.

## Keeping a callback's identity stable

`#!python use_callback` exists and memoizes through `#!python use_memo`, so it shares the dependency semantics described on [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md) — `#!python strictly_equal`, not `#!python id`.

=== "app.py"

    ```python
    {% include "../../examples/separating_events_from_effects/callback_identity/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified: pressing **Theme** (not a dependency) reports `#!python handler reused on this render`; pressing **Count** (a dependency) reports `#!python handler recreated`.

Be clear about what that buys you. ReactPy has **no render bailout**: there is no `#!python memo` (absent from both `reactpy` and `reactpy.reactjs`), and a child re-renders whenever its parent does. Measured — a child whose props and handler never changed ran its body **4 times** across one mount and three parent re-renders. So a stable callback does not make anything re-render less. What it does is keep a value out of an Effect's or `#!python use_memo`'s dependency list without re-triggering it.

There is no `#!python useEvent`, so the nearest equivalent to React's Effect Event — a stable callable that always reads the newest values — is a ref updated during render:

=== "app.py"

    ```python
    {% include "../../examples/separating_events_from_effects/latest_value_ref/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified: **Apply coupon** logs the value currently in the box even though the callback is pinned to `#!python dependencies=[]` and is never re-created.

!!! warning "A callback pinned to a local function never updates"

    Same trap as Effects, and it is worse here because the callback is *supposed* to be stable. `#!python dependencies=[describe]`, where `#!python describe` is a local `#!python def`, compares code-equal forever:

    === "app.py"

        ```python
        {% include "../../examples/separating_events_from_effects/callback_frozen_dep/app.py" start="# start" %}
        ```

    === ":material-play: Run"

        ```python
        # TODO
        ```

    Verified: type `#!python shoes`, press **Run**, type `#!python shoes2`, press **Run** again. The page shows the new query both times; the console says `#!python handler sees query=''` both times. The counter keeps counting (`#!python Run (2)`), which is what makes this so easy to miss — the callback looks alive while reading a snapshot from mount.

    Depend on the scalar values the callback actually reads, and never on a function defined inside the component.

## Recap

-   Ask *when* the logic should run. Interaction → handler. Synchronization → Effect.
-   State that only a handler sets and only an Effect reads is a smell: call the function from the handler and delete both. Verified symptom: the button works once.
-   Handler logic is deliberately not reactive; that is why you do not need React's Effect Events here.
-   ReactPy stores one handler per target and looks it up at dispatch, so a normal click sees current values — but events delivered before the next render share one snapshot. Use the functional updater for read-modify-write.
-   An async handler may set state after `#!python await`; after unmount that update is silently dropped.
-   `#!python use_callback` pins identity, not freshness, and identity buys you nothing for render cost in ReactPy. Reach for a render-updated ref when you need both.
-   Never list a locally defined function as a dependency of a callback or Effect — it compares code-equal and freezes the closure.

## Related

-   [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md) — dependency semantics, `#!python strictly_equal`, and silent Effect failures
-   [You Might Not Need an Effect](./you-might-not-need-an-effect.md) — logic that belongs in the render
-   [Synchronizing with Effects](./synchronizing-with-effects.md) — the patterns that genuinely need an Effect
-   [Use Callback](../reference/use-callback.md) and [Use Ref](../reference/use-ref.md) — parameter-level reference
