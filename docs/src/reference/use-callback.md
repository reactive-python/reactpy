## Overview

<p class="intro" markdown>

`use_callback` is a ReactPy hook that caches a function, replacing it only when one of its listed dependencies changes.

</p>

```python linenums="0"
cached_handler = use_callback(handler, dependencies=[dep_1, dep_2])
```

It is the function-shaped counterpart of [`use_memo`](./use-memo.md): same rules, same dependency behaviour, but the thing you cache is a callable rather than a value.

!!! info "You probably do not need it"
    In React, `useCallback` earns its place by keeping a child from re-rendering behind `memo` and by keeping effect dependencies from thrashing. **Neither reason applies to ReactPy.** There is no render bailout and no `memo`, and a function you define in the component body already counts as an unchanged dependency, because ReactPy compares local functions by their code rather than by identity. So the effect-churn problem `useCallback` exists to solve does not occur here.

    What it *does* give you is a genuinely stable function object, which matters only when the function leaves ReactPy and something else keys on its identity — a subscription registry, an event bus, a cached table. If none of that describes your code, write a plain `#!python def` and skip this page.

---

## Reference

### `use_callback(function, dependencies)` { #use-callback }

Call `use_callback` at the top level of your component to cache an event handler or other callback.

```python linenums="0"
from reactpy import use_callback
```

#### Parameters

-   **`function`**: The function you want to keep. It must be [pure](../learn/keeping-components-pure.md) in the sense that matters here: same closure, same behaviour.
-   **`dependencies`**: The values the function reads. ReactPy replaces the cached function when any of them changes. Three shapes, identical to `use_memo`:

    | You pass                       | Meaning                                                            |
    | ------------------------------ | ------------------------------------------------------------------ |
    | `#!python dependencies=[a, b]` | Replace the function when `#!python a` or `#!python b` changes.     |
    | omitted (the default)          | Infer the dependencies from the function's closure.                  |
    | `#!python dependencies=None`   | Return a new function on every render — no caching at all.          |

#### Returns

The cached function — either the one from a previous render, or, if a dependency changed, the one you just passed in.

#### Caveats

-   **The function you pass is not discarded, it is *stored*.** ReactPy does not call it; it keeps the object. That is why caching a function that closes over state can hand you an old closure — see [A cached handler sees stale values](#a-cached-handler-sees-stale-values).
-   **`#!python dependencies=[]` pins the function forever.** The same object comes back on every render, including the one holding the values it closed over on the *first* render. This is the single most common `use_callback` bug, and ReactPy will not warn you.
-   **Listing a dependency you read is not optional.** Forgetting one produces a handler that quietly acts on outdated values. Nothing checks this for you.
-   **Stable identity does not mean stable behaviour.** A function can be the same object across renders and still be wrong, because identity was the point and the closure went stale. Cache identity when something external needs identity; do not use it as a performance gesture.
-   **Comparison follows `strictly_equal`, not identity** — see the equivalent caveat in [`use_memo`](./use-memo.md): same type first, code comparison for local functions, `==` otherwise.
-   **The decorated name is the function**, not a wrapper. `#!python @use_callback(dependencies=[x])` receives your function and returns a function, so the name still calls fine — unlike `use_memo`, where the name becomes the value.
-   Like every hook, call it **only at the top level** — never in a loop, a conditional, or after an early `#!python return`.

---

## Usage

### When a stable identity matters

Here is the case `use_callback` is actually for. The component subscribes to a bus that lives outside ReactPy. That bus stores handlers in a list and skips duplicates by identity — so a new function object on each render registers another handler, and every handler receives each message.

Press **Re-render** three times. `handlers registered` stays at `1`, because the handler really is the same object each time. Press **Publish** and it is delivered once. Replace the `use_callback` line with a plain `def` and the same interaction registers four handlers.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_callback/stable_identity/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/reference_use_callback/stable_identity/data.py" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Note the `#!python heard` updater: `#!python set_heard(lambda previous: previous + 1)`. It reads no state, which is what lets this handler keep an empty dependency list honestly — an updater function gets the current value at the moment the setter runs, so the handler does not need to close over anything.

### A cached handler sees stale values

The notes app below caches a handler with `#!python dependencies=[]` while the handler reads `#!python draft`. ReactPy keeps the first function, which closed over an empty `#!python draft`, so every click adds a blank note no matter what you type.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_callback/stale_handler/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Type something and press **Add note**: the list gains `(blank)`. The handler is working perfectly — on the render it was created on.

### Listing what the handler reads

The fix is to name the values the function reads. Now the cached function is replaced whenever `#!python notes_list` or `#!python draft` changes, so a click always sees what is currently in the box — while the identity still stays put between changes.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_callback/tracked_handler/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Type something and press **Add note**: the text lands. These two files differ by one line; the behaviour difference is the whole point.

### Omitting the dependency list

Leave out `#!python dependencies` and ReactPy infers them from the function's closure, exactly as it does for `use_memo` and `use_effect`. For a handler that reads component state this is usually what you want, and it removes the "forgot a dependency" class of bug. Omitting is not the same as `#!python dependencies=[]` — the inferred list is built from what the function actually reads, which is rarely empty.

---

## Troubleshooting

### My handler acts on old values

You cached it with an empty or incomplete dependency list. The function is the same object, and so is everything it closed over. Either list the values it reads, or stop the value from being read at all by using an updater — `#!python set_items(lambda previous: [*previous, new])` instead of `#!python set_items([*items, new])`.

### My handler never fires

Check the attribute name. `#!python {"on_click": handler}` and `#!python {"onClick": handler}` both render without complaint and are never called — the key must be the event name ReactPy expects (`#!python "onClick"`), and the value must be your function, not a call to it.

### I still get a new function every render

-   You passed `#!python dependencies=None`, which means exactly that.
-   A dependency is rebuilt each render and does not compare equal — a plain class instance without `#!python __eq__`, for instance.
-   The function is defined *outside* the component and you expect it to be cached; `use_callback` caches what you hand it, per component instance.

### Do I need this to stop a child re-rendering?

No — that mechanism does not exist in ReactPy. See the note at the top of the page: children re-render whenever their parent does, regardless of prop or handler identity.
