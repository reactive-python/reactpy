## Overview

<p class="intro" markdown>

`use_effect` is a ReactPy hook that lets you synchronize a component with an external system.

</p>

```python linenums="0"
use_effect(effect)
use_effect(effect, dependencies=[value])
```

---

## Reference

### `use_effect(effect, dependencies=...)`

Call `use_effect` at the top level of your component to run an effect after rendering.

```python linenums="0"
from reactpy import use_effect
```

#### Parameters

-   **`effect`**: A function taking no arguments. ReactPy calls it after the component renders. It may **return a clean-up function** (also taking no arguments), which ReactPy runs before the next time this effect runs and again when the component unmounts.

    The effect must be [pure](../learn/keeping-components-pure.md), and it must **not** be declared `#!python async def` — ReactPy raises for that; use [`use_async_effect`](./use-async-effect.md) instead.

-   **`dependencies`** *(optional)*: Controls when the effect re-runs. Unlike React, this argument has **four** distinct settings, and the default is not React's:

    | Value | Behaviour (verified) |
    | --- | --- |
    | omitted (`...`) | **Inferred.** ReactPy reads the free variables of your closure (`core/hooks.py`, `_try_to_infer_closure_values`) and re-runs when any of them changes. A closure that reads nothing runs once. |
    | `#!python dependencies=[]` | Runs **once**, after mount. |
    | `#!python dependencies=[a, b]` | Runs when `#!python a` or `#!python b` changes. |
    | `#!python dependencies=None` | Runs after **every** render. |

    "Changes" means `#!python strictly_equal` (`core/hooks.py`), not `#!python is`: the two values must share a *type*, two locally-defined functions or lambdas are compared by bytecode, and everything else falls through to `#!python ==` with `#!python is` as the last resort. A rebuilt list or dict with equal contents does **not** re-run the effect. [Use Memo](./use-memo.md#caveats) documents the same function in full.

#### Returns

`None` when given the effect, or a decorator when called without one.

#### Caveats

-   **The default is inference, not "every render".** In React, omitting the dependency array means the effect runs after every render. In ReactPy it means "re-run when the variables my closure reads change". Code ported from React will therefore behave differently — pass `#!python dependencies=None` if you really want every-render behaviour, though usually you want to be explicit instead.
-   **Inference is structural, not declared, and it does not compare by `id`.** A closure that happens to read an extra local variable gains an extra dependency, and the comparison is `strictly_equal` — type, then bytecode for local functions, then `==` — so a rebuilt-but-equal container counts as unchanged. If the effect runs more or less often than you expect, look at which names it actually reads, and then at how those values compare.
-   Effects run on the **server**, after rendering, not in the browser. There is no DOM to touch: `#!python document` and `#!python window` do not exist here. There is no `#!python document` or `#!python window` to reach for, and no ReactPy equivalent of attaching a listener to a node — see [Responding to Events](../learn/responding-to-events.md) for the supported way to react to the browser.
-   **Children's effects run before their parent's, and siblings run in reverse order.** Verified output: `['child effect b', 'child effect a', 'parent effect']`. Two effects in one component run in declaration order. Do not rely on React's parent-first or source-order guarantees.
-   Passing `#!python async def` to `use_effect` fails loudly: `TypeError: use_effect does not support async functions. Use use_async_effect instead.` The error lands in the model's `error` field and the component stops rendering.
-   An exception raised *inside* an effect body is logged on the server only; the model carries no error and the UI looks unchanged. Check the server log.
-   Effects are **not** a substitute for computing values. Derive them during render or with [`use_memo`](./use-memo.md).
-   There is no `use_layout_effect`, `use_insertion_effect`, or `use_imperative_handle`. Nothing runs synchronously during the render phase.

---

## Usage

### Importing `use_effect`

```python linenums="0"
from reactpy import use_effect
```

### Describing an effect

Pass the setup function directly:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_effect/minimal/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/reference_use_effect/minimal/data.py" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Or use it as a decorator, which is equivalent:

```python linenums="0"
@use_effect
def effect():
    print("mounted")
```

### Telling ReactPy when to re-run the effect

Pass a dependency list to re-run only when something relevant changes:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_effect/dependencies/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/reference_use_effect/dependencies/data.py" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Switching topic tears down the old subscription before creating the new one — verified, the subscriber count stays at `#!python 1` across switches and drops to `#!python 0` on unmount.

#### Omitting the dependencies argument

```python linenums="0"
use_effect(effect)               # inferred from what the closure reads
```

The example below makes inference visible. The effect reads `#!python count` but not `#!python label`, so renaming re-renders the component without re-running the effect:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_effect/inferred/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Pressing Rename twice adds no new log line — verified. Be aware this works because of which names the closure reads; it is implicit, so many teams prefer to spell the list out.

#### Passing an empty dependency array

```python linenums="0"
use_effect(effect, dependencies=[])   # once, after mount
```

For mount-only work — subscribing, starting a timer, reading a config — say so explicitly.

#### Passing `None`

```python linenums="0"
use_effect(effect, dependencies=None)  # after every render
```

This is the closest ReactPy gets to React's "no array" behaviour. It re-runs the effect after every render, verified. Reach for it rarely: it usually means the effect is doing work that belongs in render or in `#!python use_memo`.

### Adding clean-up

Return a function from the effect. ReactPy calls it before the next run of that effect and when the component unmounts:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_effect/cleanup/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Connecting and disconnecting runs the pair in order — verified: `#!python connected`, `#!python disconnected`, `#!python connected` across connect / disconnect / reconnect.

!!! info "Clean-up is the difference between a leak and a working app"

    Because ReactPy components live in long-lived server processes, a forgotten subscription is not a brief flash of stale data — it is a permanent leak that outlives every browser tab that opened it. Every `#!python subscribe`, every timer, every held connection needs a clean-up function.

### Effects and the request lifecycle

An effect runs in the connection's own task, after the render that scheduled it. It can call setters, and those schedule further renders. Two consequences:

-   An effect that awaits gives the event loop control. Long `#!python await`s belong in [`use_async_effect`](./use-async-effect.md), which is built for it.
-   Setting state from an effect that depends on that same state loops forever. If an effect seems to spin, read what it sets and what it depends on.

### Reading the latest state inside an effect

An effect closes over the render that created it. If it then runs for a long time — an interval callback, a subscription handler — it can act on values that are no longer current. Two ways to handle it:

-   Put the value in the dependency list, so a change tears the effect down and starts a new one with fresh values.
-   Keep the value in a [`use_ref`](./use-ref.md) box and read `#!python ref.current` when you need it. The box persists across renders, so readers see the newest value — as long as the write happens somewhere legal. Do **not** assign `#!python ref.current` from the component body: a render-phase write is exactly the impurity [Use Ref](./use-ref.md#caveats) warns about, and ReactPy has no Strict Mode to catch it. Assign it where the value is already produced — the event handler that changed it — or in its own effect, which runs after the render.

If an effect reads state it does not declare, that is usually a sign the effect should be re-created when that state changes — reach for the dependency list first.
