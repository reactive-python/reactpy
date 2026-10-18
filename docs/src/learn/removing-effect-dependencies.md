## Overview

<p class="intro" markdown>

Every dependency you list is a promise: "when this changes, redo the work." Removing one you don't need is fine — and proving it is not needed is the whole job. This page covers what counts as a change in ReactPy, and the six legitimate reasons a value can leave the list.

</p>

!!! summary "You will learn"

    -   How to prove a value is not a dependency, rather than guess
    -   How ReactPy actually compares dependencies — not what the docstring says
    -   The six safe ways to remove a dependency
    -   Why a rebuilt object is not "new" here, and when that saves you
    -   What to do when a value must stay out of the list for real

## Dependencies should match the code

The list describes the code, not your intent. Look at the Effect body, list every name it reads that came from the component body, and that is the list. Nothing more, nothing less.

A missing dependency is a **correctness** bug: the Effect reports values from an older render. An extra dependency is a **behaviour** bug: the work runs when it shouldn't, tearing down something that should have stayed up. Both are worth fixing, and they are fixed differently.

To remove a dependency, prove one of these about it:

-   it cannot change between renders (module constant, imported helper)
-   it is read only to *compute* a new value, not to decide what to do
-   it is read for a "latest value" snapshot, and reacting to it is unwanted
-   the code that reads it should be in an event handler, not an Effect
-   the Effect is doing two jobs and only one of them needs it
-   it changes unintentionally, and the real fix is to stop it changing

If none of those is true, the value stays. Deleting it from the list to quiet a symptom produces an Effect that looks fine and reports the past.

### A missing dependency is visible if you look

This Effect writes a summary into state but lists only `#!python topic`:

=== "app.py"

    ```python
    {% include "../../examples/removing_effect_dependencies/unread_dep/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified: press **Count** twice and **Theme** once, and the page reads

```text linenums="0"
live:    count=2 theme=dark
summary: topic=news count=0 theme=light
```

The summary describes the render that created the Effect. Press **Topic** and both lines agree again — because a new Effect was built from the current render. That pair of lines is the whole missing-dependency bug made visible: it is not frozen at mount, and it is not current. It is from *some* render.

## How ReactPy compares dependencies

This is where React's advice and ReactPy's behaviour part ways, and it decides which removals are safe.

Dependencies go through `core/hooks.py`, `#!python strictly_equal`:

1.  **Type gate first.** If `#!python type(x) is not type(y)`, it is a change — `#!python 1` and `#!python 1.0` never compare equal here.
2.  **Local functions compare code.** If *both* values have a `#!python __qualname__` containing `#!python <locals>` or `#!python <lambda>` *and* both expose `#!python __code__`, their `#!python co_*` bytecode attributes are compared — same code, and the same `#!python __qualname__`, means unchanged. One side qualifying is not enough: a locally-defined function compared against an import is not code-compared.
3.  **Otherwise `#!python ==`**, but only if the value has an `#!python __eq__` at all (`hasattr(x, "__eq__")`), and falling back to `#!python is` if `#!python ==` raises.

Note step 3. The `#!python strictly_equal` docstring claims only `#!python int`, `#!python float`, `#!python str`, `#!python bytes` and friends are compared by equality, but the implementation reaches `#!python x == y` for anything with an `#!python __eq__` — which is everything. Measured over 5 renders each (mount plus four unrelated state changes), counting how many times the Effect ran:

| Dependency, rebuilt on every render | Runs |
| --- | --- |
| `#!python {"sort": "date", "limit": 10}` — never changes | 1 |
| `#!python [1, 2, 3]` — never changes | 1 |
| `#!python DataFilter("a")` (`#!python @dataclass`) — content changed twice | 3 |
| `#!python TupleFilter("a")` (`#!python NamedTuple`) — content changed twice | 3 |
| `#!python {"sort": "date", "limit": count}` — content tracks state | 3 |
| plain class instance, no `#!python __eq__` | **5 (every render)** |
| `#!python (1, 2, 3)` alternating with `#!python [1, 2, 3]` | 3 (type gate) |

Consequences:

-   **React's "a rebuilt object is a new dependency" warning does not apply here.** A dict or list you rebuild on every render is not a dependency change, so it will not loop. That is why the classic infinite-loop example needs no fix in ReactPy — and why you must not *rely* on it either, since it depends on values comparing equal, not on identity.
-   **A plain class instance always counts as changed**, because it inherits `#!python object.__eq__` and identity never holds across renders. That is the shape that genuinely spins.
-   **The type gate catches things `#!python ==` would not:** `#!python strictly_equal(1, True)` is `#!python False` even though `#!python 1 == True`, and a tuple swapped for a list is a change.

Because ReactPy cannot check your list for you — a missing dependency produces no warning, no log record, and no error — proving the list is yours to do. See [Separating Events from Effects](./separating-events-from-effects.md) and [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md) for the `#!python Layout`-based test that catches what nothing else will.

## Removing unnecessary dependencies

### Should this code move to an event handler?

If the work should happen because the user did something, it belongs in the handler, and the dependency disappears along with the Effect. This is the most common removal and the one that deletes the most code — see [Separating Events from Effects](./separating-events-from-effects.md).

### Is your Effect doing several unrelated things?

One Effect connecting a socket *and* loading rows means each job inherits the other's dependencies:

=== "app.py"

    ```python
    {% include "../../examples/removing_effect_dependencies/unrelated_effects/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified: press **Toggle online** and the log shows `#!python disconnect news page=2` before `#!python offline — nothing to do`. Going offline tears down a connection by way of a page number. Split the Effect in two and each list shrinks to what its own job reads.

### Are you reading some state to calculate the next state?

Then that state is not a dependency — it is an input to the next value. Take an updater and it leaves the list:

=== "app.py"

    ```python
    {% include "../../examples/removing_effect_dependencies/next_state_updater/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified: each topic change appends exactly one entry; changing **Show** does not append anything.

Now the reason this rule matters. Listing `#!python lines` as well — "just to be safe", exactly the mistake the ReactJS page warns about in the other direction — gives:

```text linenums="0"
def record():
    def append(current):
        return [*current, f"opened {topic}"]

    set_lines(append)

use_effect(record, dependencies=[topic, lines])   # never settles
```

Measured: the connection rendered **400 times without settling** and the component body ran 800 times. The Effect appends, `#!python lines` changes, the Effect runs again. A functional updater is not a micro-optimisation here; it is what breaks the cycle.

### Do you want to read a value without reacting to its changes?

Keep it in a ref that you update during render, and leave it out of the list. The difference is easy to see on a poll loop with a user-adjustable delay.

The version that lists the delay:

=== "app.py"

    ```python
    {% include "../../examples/removing_effect_dependencies/restarting_interval/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The version that keeps it in a ref:

=== "app.py"

    ```python
    {% include "../../examples/removing_effect_dependencies/stable_interval/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified with the same script on both — two delay adjustments, half a second of ticking, then a topic change:

| | Loop starts | Loop stops |
| --- | --- | --- |
| `#!python delay` in the list | **4** | 2 |
| `#!python delay` in a ref | **2** | 1 |

Two of those restarts are pure waste: adjusting a setting nobody asked to reconnect for. And because the ref is assigned during render, the loop still sleeps with the newest delay — `#!python tick news delay=0.6s` appears in the log of the ref version even though the Effect never re-ran.

The ref assignment during render looks like a write in a render, and it is the one case that is safe: the box is created once, the write is idempotent, and nothing derived from it feeds the render output.

### Does some reactive value change unintentionally?

Sometimes the dependency is correct and the value is the problem.

**Move static values out of the component.** A module-level constant, an imported helper, or a frozen config is the same object on every render and every connection, so it is not a dependency at all:

=== "app.py"

    ```python
    {% include "../../examples/removing_effect_dependencies/hoisted_constant/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified: typing in the box re-renders the component and the Effect does **not** run; only the topic change logs `#!python load topic=newsx page_size=20 headers={'Accept': 'application/json'}`.

**Read primitive values out of objects.** `#!python user.id` is a dependency; `#!python user` is a wider promise than you need, and any unrelated field change re-runs the Effect. Depend on the scalars you actually use.

**Calculate primitives from functions, not objects.** This is also the fix for the trap that silently freezes an Effect: a locally defined function passed as a dependency compares *code-wise* and therefore never changes. Depend on the string or number the function would have produced.

### Rebuilding an object is not a dependency change — but don't rely on it

=== "app.py"

    ```python
    {% include "../../examples/removing_effect_dependencies/equality_deps/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Verified: press **Re-render** three times, which rebuilds `#!python options` every time — the Effect runs zero extra times. Press **Page** and it runs, because `#!python page` is a real dependency.

It is useful to know this: query-option dicts and filter objects do not have to be `#!python use_memo`-ed to avoid a reconnect storm. But it is a behaviour, not a contract. It holds only while your values compare equal, and it silently inverts for a plain class instance (5 runs out of 5 renders above). Write the list you mean, and let equality be a bonus.

## When a dependency must come out

There are cases where the honest answer is "I read this value, I do not want to react to it, and a ref is the wrong shape for it." Then be explicit about the exception rather than quietly deleting the name:

```python linenums="0"
def effect():
    notify(user_id, channel_id)   # reads channel_id

use_effect(effect, dependencies=[user_id])
# channel_id is read but not reacted to: it changes only when the user
# switches channel, which unmounts this component anyway.
```

The comment is the review surface. An unexplained missing name is indistinguishable from the bug in the first example on this page — and, as measured, nothing in ReactPy will tell you which one you wrote.

!!! warning "What `#!python dependencies=None` does not mean"

    `#!python None` is not "no dependencies"; it means **re-run after every render**. To create the Effect once and never replace it, use `#!python dependencies=[]` — which also seals the body against future renders. See the four-way table in [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md#what-an-effect-with-empty-dependencies-means).

## Recap

-   The list describes the code. Prove a value is not a dependency; don't vote it off.
-   ReactPy compares dependencies with `#!python strictly_equal`: type gate, then code comparison for local functions, then `#!python ==`. Rebuilt dicts and lists are not changes; plain class instances always are.
-   A missing dependency is silent — no warning, no log. Make the staleness visible in the page, as the first example does, or assert it in a test.
-   The six removals: hoist what cannot change, take an updater for next-state reads, keep latest-value reads in a ref, move interaction logic to handlers, split Effects that do two jobs, and stop values changing unintentionally.
-   Listing state you only append to is the classic self-triggering loop: measured, 400 renders and no settle.
-   Nothing checks the list for you, so an explanatory comment is the only reviewer you have.

## Related

-   [Lifecycle of Reactive Effects](./lifecycle-of-reactive-effects.md) — dependency semantics, the four settings, and silent Effect failures
-   [Synchronizing with Effects](./synchronizing-with-effects.md) — the patterns that genuinely need an Effect
-   [Separating Events from Effects](./separating-events-from-effects.md) — moving interaction logic into handlers
-   [You Might Not Need an Effect](./you-might-not-need-an-effect.md) — logic that belongs in the render
-   [Use Effect](../reference/use-effect.md) — parameter-level reference
