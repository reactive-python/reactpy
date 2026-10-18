## Overview

<p class="intro" markdown>

An Effect is a piece of synchronization code attached to a render. It runs, it may clean up after itself, and it runs again if its inputs change. Understanding that lifecycle — not a memorized list of rules — is what makes Effects predictable in ReactPy.

</p>

!!! summary "You will learn"

    -   How an Effect setup and clean-up pair forms one synchronization
    -   Which values an Effect "reacts" to, and what happens to the ones it doesn't
    -   Why a dependency list, not the Effect's own text, decides re-synchronization
    -   How Effects are ordered, and what is not guaranteed
    -   Why a broken Effect reports itself nowhere the user can see

## The lifecycle of an Effect

Think of an Effect as a synchronization process between a value your component holds and something outside ReactPy. Each Effect has a setup and, sometimes, a clean-up:

=== "app.py"

    ```python
    {% include "../../examples/lifecycle_of_reactive_effects/setup_cleanup/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified against the server's own log: mount produces `#!python connect lobby`; pressing **Leave lobby** produces `#!python close lobby` then `#!python connect dev`; and the last connection closes on unmount. The open-connection count never climbs above 1.

Read the pair as a single unit — "be connected to this room". Setup and clean-up are not two independent callbacks: **ReactPy runs the clean-up of a run right before that run's successor sets up**, using the same captured state. So switching rooms means *leave the old room, join the new one*, in that order, and the process is complete no matter how many times the inputs change.

### Why synchronization may need to happen more than once

The value being synchronized can change while the component is on screen: `#!python room` above, a search query, an auth token. Every such change means the previous synchronization is describing the past, so ReactPy tears it down and starts a new one.

That is why the clean-up is not optional boilerplate. In a browser, forgetting it leaks one subscription until the tab closes. On a ReactPy server it leaks until the **process** exits — and the leaked callback still holds your component, still fires, and keeps a connection or file handle alive for a user who left hours ago.

### How ReactPy re-synchronizes an Effect

When a dependency changes, ReactPy runs this sequence:

1. The component renders and registers the Effect again.
2. A new Effect task starts, and **its first act is to run the previous run's clean-up** — `core/hooks.py`, `use_effect` calls `run_effect_cleanup` before invoking your function.
3. Your setup runs and returns the next clean-up.

Two consequences worth internalizing:

-   The clean-up runs on the *new* task, not the old one. It sees the previous run's captured values, which is exactly what a teardown needs.
-   The old task is not cancelled. A sync Effect's task parks on `#!python stop.wait()` and is only reaped when the component unmounts. Measured: three dependency changes leave **4** live Effect tasks where there was 1, and all 4 disappear at unmount. The clean-ups still ran in the right order; the parked tasks are simply waiting for a signal that will come at unmount. For a long-lived component re-synchronizing constantly, that is memory you are paying for.

### Thinking from the Effect's perspective

When you read an Effect, read it as the outside world would. The code above says: *"while this component is on screen and `room` is X, stay connected to X."* Everything in that sentence is checkable:

| Sentence part | Where it comes from |
| --- | --- |
| "while this component is on screen" | the component's mount/unmount |
| "and `room` is X" | the dependency list |
| "stay connected to X" | setup |
| (leaving) | the returned clean-up |

If part of that sentence is a lie, the Effect is wrong — not the dependency list, not the linting setup. `#!python dependencies` is how you spell "and `room` is X"; it is not a performance knob.

### Each Effect represents a separate synchronization process

Two Effects in one component are two processes, not one with two steps. Keep them apart when their synchronization targets differ, and let each own its own clean-up:

```python linenums="0"
use_effect(connect_to_room, dependencies=[room])
use_effect(subscribe_to_feed, dependencies=[user_id])
```

Do not merge them because they live in the same component: merging means a room change tears down the feed subscription too. Two Effects in the same component run in **declaration order**, so ordering within a component is available to you when one genuinely depends on the other's setup having happened.

## Effects "react" to reactive values

Every value in the component body — props, state, anything computed from them — belongs to one render. An Effect created by that render reads *that render's* values and never sees a later one. The dependency list is how you say which values should trigger a new Effect.

Here an Effect reports an error flag but leaves it out of the dependency list:

=== "app.py"

    ```python
    {% include "../../examples/lifecycle_of_reactive_effects/reactive_values/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified: pressing **Toggle error** re-renders the component and runs the Effect **zero** times — the list says `#!python dependencies=[count]`, so nothing happens. Press **Add 1** and the Effect runs, and this time it reports the *new* value of the flag, because a brand-new Effect was created by that render.

That is the precise meaning of "stale": the Effect reports values from the render that created it. It does not freeze at mount, and it does not read the latest — it reads whichever render it was born in. Adding the missing value to the list is the fix.

!!! warning "A local function as a dependency never counts as changed"

    This one bites hard, and it contradicts the docstrings. ReactPy compares dependencies with `core/hooks.py`, `#!python strictly_equal` — **not** by `#!python id`. For two locally defined functions it compares their *code*: same `#!python co_*` attributes means same dependency. So a `#!python def` re-created on every render is never detected as changed:

    === "app.py"

        ```python
        {% include "../../examples/lifecycle_of_reactive_effects/frozen_body/app.py" start="# start" %}
        ```

    === ":material-play: Run"

        ```python
        # TODO
        ```

    Verified: press **Add 1** twice and **Rename** once — the heading shows `#!python count!!: 2`, yet the Effect has run exactly once and `#!python describe()` still returns `#!python 'count=0'`. The Effect is permanently frozen on its first closure, and nothing warns you.

    The same rule bites the other way: a fresh `#!python [1, 2]` or `#!python {"a": 1}` that compares equal is also "unchanged", so rebuilding an options dict on every render will not re-trigger an Effect that lists it. Depend on the scalar values you actually use, not on containers or local functions.

### What an Effect with empty dependencies means

`#!python dependencies=[]` does not mean "run once, like a `#!python componentDidMount`". It means **create this Effect and never replace it** — including its body:

```python linenums="0"
def effect():
    print(f"body sees label={label}")

use_effect(effect, dependencies=[])
```

Verified: change `#!python label` three times and the component re-renders three times; the Effect never runs again, and when something else finally forces it, it prints the **first** render's `#!python label`. An `#!python []` Effect is sealed at mount. Reach for it only when the Effect genuinely reads nothing but stable values (module constants, a setter, a ref).

The four settings, restated with their lifecycle meaning:

| Value | Meaning |
| --- | --- |
| `#!python dependencies=[a, b]` | Re-synchronize when `#!python a` or `#!python b` changes. |
| `#!python dependencies=[]` | Synchronize once, at mount; the body is never replaced. |
| `#!python dependencies=None` | Re-synchronize after **every** render. |
| omitted | **Infer** the list from the closure's free variables — then compare with `#!python ==`, so a rebuilt-but-equal value will not re-trigger. |

### All variables declared in the component body are reactive

Props, state, and anything derived from them are per-render values, so they belong in the dependency list whenever the Effect reads them. Module-level constants and imported singletons do not: they are the same object for every render and every connection.

Careful with the middle case. A `#!python dict` built at module level looks like a constant and is not safe to mutate — every connection shares it ([VDOM Mutations](./vdom-mutations.md)). And a mutable default argument is shared too. Neither is a dependency, because neither *changes*; both are bugs if you write to them.

!!! danger "Hooks are unusable inside an effect body"

    ```python linenums="0"
    def effect():
        theme = use_context(theme_context)   # RuntimeError
    ```

    Effects run in their own task, after rendering, with no life cycle hook on the stack. `#!python use_context`, `#!python use_state`, and every other hook raise `#!python RuntimeError: No life cycle hook is active. Are you rendering in a layout?` — and that traceback reaches only the server log. Read what you need **during render** and let the closure carry it:

    ```python linenums="0"
    theme = use_context(theme_context)

    def effect():
        apply(theme)

    use_effect(effect, dependencies=[theme])
    ```

### What to do when you don't want to re-synchronize

Three legitimate reasons, three different answers.

**The value is genuinely constant.** Import it, define it at module level, or hoist it out of the component. Then it is not a dependency because it cannot change:

```python linenums="0"
POLL_INTERVAL = 5


@component
def poller(topic):
    async def effect():
        ...

    use_async_effect(effect, dependencies=[topic])
```

**You want the latest value without restarting the process.** Keep it in a ref and read `#!python .current` — the box persists across renders, so a long-lived Effect always reads the newest assignment ([Synchronizing with Effects](./synchronizing-with-effects.md#reading-the-newest-value-from-a-long-lived-effect)).

**You want to switch the process off.** Do not delete the hook call — that changes the hook order and corrupts every hook after it. Pass a flag and branch *inside* the Effect:

=== "app.py"

    ```python
    {% include "../../examples/lifecycle_of_reactive_effects/gating/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified: **Stop** runs `#!python unsubscribe news`; while stopped, switching topics logs **nothing** (correct — there is nothing to synchronize); and **Start** then runs `#!python subscribe sports` for the new topic. The hook call always happens; only the setup is conditional. Note the dependency list includes `#!python enabled` — leaving it out would mean toggling did nothing at all.

!!! warning "Do not omit a dependency to dodge a loop"

    An Effect that re-triggers itself is telling you something. Measured: an Effect that sets a piece of state it also lists as a dependency rendered **86 times** before the probe stopped. Deleting the dependency silences the symptom and leaves you with an Effect that reports the past. Fix the loop — usually by moving the value into the dependency list and making the setup idempotent, or by deriving the value during render instead ([You Might Not Need an Effect](./you-might-not-need-an-effect.md)).

## ReactPy will not verify your dependencies

React's side of this is `eslint-plugin-react-hooks`, which reads the Effect and its dependency list and warns when they disagree. ReactPy has nothing comparable: nothing reads your Effect, nothing compares it to the list, and a missing dependency is **completely silent** — no warning, no log record, no error. The value simply arrives from an older render, surfacing later, when something else finally re-runs the Effect.

The shapes that go wrong are worth knowing, because the list is not a formality:

| What you wrote | What actually happens |
| --- | --- |
| a free variable missing from `#!python dependencies` | the Effect keeps the value from the render that created it; nothing warns |
| `#!python dependencies=[]` on a body that reads state | the body, not just the schedule, is sealed at mount |
| a dependency that is a rebuilt dict, list, or tuple | no re-run — those compare equal, see `#!python strictly_equal` below |
| a dependency that is a plain class instance with no `#!python __eq__` | re-runs after **every** render — identity never holds |
| a `#!python Ref` in the list | never triggers anything: `__eq__` compares `.current` against itself |
| a bound method, `#!python functools.partial`, or callable object, with `#!python dependencies` omitted | inference gives up, the value becomes `#!python None`, and the Effect runs after **every** render |

Two habits replace the missing dependency check:

1.  **Read the Effect and list the names.** Every free variable in the body should appear in `#!python dependencies`, or be provably module-level. This is mechanical — do it once per Effect at write time.
2.  **Test the re-synchronization, not just the mount.** Render, change the input, assert the outside world changed:

    ```python linenums="0"
    async def test_switching_room_reconnects():
        async with Layout(app()) as layout:
            await layout.render()
            ...  # deliver the click that changes the room
            assert server.log == ["connect lobby", "close lobby", "connect dev"]
    ```

    A `#!python reactpy.core.layout.Layout` in pytest is enough — no browser, and it catches exactly the bugs nothing else will surface.

## The order Effects run in

Verified output for a parent with two children, each declaring two Effects:

```text linenums="0"
beta: first effect
beta: second effect
alpha: first effect
alpha: second effect
panel: my own effect
```

=== "app.py"

    ```python
    {% include "../../examples/lifecycle_of_reactive_effects/ordering/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Three rules, and nothing else:

-   **Children before parent.** A parent's own Effects run after everything below it has set up.
-   **Siblings in reverse source order.** `#!python beta` before `#!python alpha`. This surprises everyone and is worth knowing if two siblings write to the same external resource.
-   **Within one component, declaration order.** This one you can rely on.

Do not build anything on the first two. They are behaviour, not contract — the reverse-sibling rule in particular is an artifact of how effects are collected, and code that depends on a particular cross-component order is code that will break. Within a component, order Effects deliberately; across components, make each Effect self-contained.

## Async Effects: cancellation is not instant

`#!python use_async_effect` wraps your coroutine in a task. On re-synchronization the old task is **cancelled**, which means it stops at its next `#!python await` — not before, and not necessarily in time.

Two things follow, both measured.

**Two runs can be alive at once.** Switch topics three times quickly, before any 0.4 s poll resolves, and the log is:

```text linenums="0"
start polling news
cancelled news
start polling sports
start polling news          # the older run is still awaiting
cancelled news
start polling sports
finished polling sports
finished polling sports
```

Verified, and identical across three repeats: two runs are simultaneously awaiting. Cancellation happens when the *successor* task starts, so a run that has already passed its awaits cannot be recalled — and notice the two `#!python finished` lines belong to the same topic.

**A superseded run can still write state.** With a 0.4 s source and four rapid switches (`#!python a → b → c → d`), the runs that actually applied their result were `#!python ['DATA FOR b', 'DATA FOR d']` — `#!python a` and `#!python c` were cancelled, `#!python b` and `#!python d` completed and called their setters. Reproducible across runs.

So cancellation is a *bias* toward the newest value, not a guarantee. If a stale write would be damaging, do not rely on being cancelled — tag the data with what produced it and check on write:

```python linenums="0"
loaded, set_loaded = use_state({"name": None, "data": {}})

async def effect():
    data = await fetch(name)
    if name == expected_name.current:   # still the value we care about?
        set_loaded({"name": name, "data": data})
```

Put teardown that must run in the cancellation branch, and re-raise:

```python linenums="0"
async def effect():
    handle = open_connection()
    try:
        while True:
            await handle.poll()
    except asyncio.CancelledError:
        handle.close()
        raise
```

Swallowing `#!python CancelledError` leaves the task in a state asyncio did not expect.

!!! warning "A sync Effect blocks the whole connection"

    `#!python use_effect` runs on the connection's event loop. Measured: an Effect calling `#!python time.sleep(0.4)` made the next click take **0.40 s** to be served, and every other handler on that connection waited behind it. Only the browser's own local typing stays responsive. Long or blocking work belongs in `#!python use_async_effect`, with blocking calls wrapped in `#!python asyncio.to_thread` ([Communicating Data Between Server and Client](./communicate-data-between-server-and-client.md)).

## When an Effect fails, nothing reports it

This is the section that saves the most hours. An Effect body that raises is **invisible** in three places at once:

-   the page looks completely fine,
-   the browser console is clean,
-   and — the part that misleads people — **the server log stays silent too.**

=== "app.py"

    ```python
    {% include "../../examples/lifecycle_of_reactive_effects/silent_failure/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Measured with a log handler attached to the `#!python reactpy` logger: after mount, after three dependency changes, and after half a second idle, **zero** log records. The single `#!python ERROR Error in effect` record appears only when the component unmounts — because `core/_life_cycle_hook.py`, `affect_component_will_unmount` is where the Effect tasks are finally awaited and their exceptions gathered (`core/hooks.py` parks each task on `#!python stop.wait()`, so nobody looks at its result before then).

Consequences to design around:

-   **Never diagnose an Effect from the page.** Read the server log, and read it *after* navigating away — that is when failures surface.
-   **Assert the external world in tests.** A render assertion passes happily while your Effect is throwing; assert that the connection happened, the row was written, the file exists.
-   **Catch inside the Effect and set state** when a failure should be visible to the user. ReactPy will not do it for you:

    ```python linenums="0"
    def effect():
        try:
            set_metrics(fetch_metrics())
        except Exception as error:
            set_error(str(error))   # now the user can see it
    ```

Contrast with the failure modes that *are* reported, so you can tell which one you have:

| Symptom | Cause |
| --- | --- |
| Blank region, `#!python error` in the model (debug on) or a server traceback | the **component body** raised — e.g. an `#!python async def` passed to `#!python use_effect` |
| `#!python ValueError: Cell is empty` in the model | an Effect registered **above** the state it reads |
| Page looks fine, log silent until unmount | the **Effect body** raised |
| Page looks fine, log clean forever, Effect never runs | wrong `#!python dependencies` |

## Recap

-   An Effect is a synchronization process: setup, clean-up, and a dependency list that says when to redo it.
-   The clean-up of a run executes on its successor's task, before that successor's setup — so a re-synchronization is leave-then-join, in order.
-   An Effect reads the values of the render that **created** it. Not the latest, not necessarily the first.
-   The dependency list, not the Effect's own text, decides re-synchronization. `#!python dependencies=[]` seals the body at mount.
-   Dependencies compare with `#!python ==` via `#!python strictly_equal`, so local functions and rebuilt-but-equal containers never count as changed — and a frozen Effect is silent.
-   Nothing checks your dependency list — not the runtime, not a warning, not a log line. Write the list yourself and test the re-synchronization.
-   Children's Effects run before the parent's, siblings in reverse, and within a component in declaration order. Only the last is safe to depend on.
-   Async cancellation lands at the next `#!python await`: runs can overlap and a superseded run can still write. Guard the write; don't trust the cancel.
-   A raising Effect shows nothing in the page, nothing in the browser, and nothing in the log until unmount. Verify Effects by asserting their effect on the world.

## Related

-   [Synchronizing with Effects](./synchronizing-with-effects.md) — the four-way dependency table, clean-ups, and the common patterns
-   [You Might Not Need an Effect](./you-might-not-need-an-effect.md) — the cases that belong in the render
-   [Separating Events from Effects](./separating-events-from-effects.md) — reading fresh values without restarting a process
-   [Removing Effect Dependencies](./removing-effect-dependencies.md) — the legitimate ways to drop a dependency
-   [Use Effect](../reference/use-effect.md) and [Use Async Effect](../reference/use-async-effect.md) — parameter-level reference
