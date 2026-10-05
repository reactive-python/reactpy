## Overview

<p class="intro" markdown>

`use_memo` is a ReactPy hook that caches the result of a calculation, recomputing it only when one of its listed dependencies changes.

</p>

```python linenums="0"
cached_value = use_memo(calculate_value, dependencies=[dep_1, dep_2])
```

Use it when a calculation is genuinely expensive *and* the inputs it depends on change less often than the component renders. It caches a **value**; it does not stop anything from rendering.

!!! warning "What `use_memo` does not do in ReactPy"
    It does not prevent a child component from re-rendering. ReactPy has no render bailout and no `memo`: a child's body runs whenever its parent re-renders, even with identical props, and even if you cache the child element itself with `use_memo`. Texts ported from React that use `useMemo` to "skip re-rendering of components" describe a mechanism that is not here. `use_memo` saves the *computation*, nothing else.

---

## Reference

### `use_memo(function, dependencies)` { #use-memo }

Call `use_memo` at the top level of your component to cache a calculation.

```python linenums="0"
from reactpy import use_memo
```

#### Parameters

-   **`function`**: A function taking no arguments that returns the value you want. ReactPy calls it only when it must. It must be [pure](../learn/keeping-components-pure.md): same inputs, same output, no side effects.
-   **`dependencies`**: The values the calculation reads. ReactPy recomputes when any of them changes. It accepts three shapes:

    | You pass                       | Meaning                                                             |
    | ------------------------------ | ------------------------------------------------------------------- |
    | `#!python dependencies=[a, b]` | Recompute when `#!python a` or `#!python b` changes.                 |
    | omitted (the default)          | ReactPy reads the function's closure and infers the free variables.  |
    | `#!python dependencies=None`   | Recompute on every render.                                           |

#### Returns

The current value — either freshly computed, or the one cached from the last render in which a dependency changed.

#### Caveats

-   **The decorator form does not do what you would expect.** Applying `#!python @use_memo(dependencies=[x])` binds the name to the *value*, not to a function, so calling it later raises `#!python TypeError: 'int' object is not callable`. Pass your function as an argument instead.
-   **Caching lasts for the lifetime of the component.** A cached value survives as long as the component stays mounted; there is no way to invalidate it from inside. Mounting the component under a new `#!python "key"` throws it away, because that unmounts and remounts the component and every hook starts over.
-   **You must list every value the function reads.** ReactPy does not check, and does not warn. A missing dependency produces a silently stale value, not an error. See [I removed a dependency and nothing complained](#i-removed-a-dependency-and-nothing-complained).
-   **Comparison is not plain identity.** Dependencies go through `reactpy.core.hooks.strictly_equal`, which requires the two values to be the same *type* first, compares two locally-defined functions or lambdas by their code objects (so a fresh, structurally identical lambda counts as *unchanged*), and otherwise compares with `#!python ==`, falling back to `#!python is` only if that raises. Two practical consequences: a freshly built `#!python list` or `#!python dict` with equal contents does **not** force a recompute, and a value that changes type between renders — `#!python 1` then `#!python 1.0`, or `#!python 0` then `#!python False` — always counts as changed.
-   **Mutating a dependency in place defeats the cache.** Change an object and pass the same object back, and it compares equal to itself, so the cached value is kept. Build a new object instead — see [Updating Objects in State](../learn/updating-objects-in-state.md).
-   **A ref never invalidates a memo.** Writing to `#!python some_ref.current` does not change how the ref compares, so listing a `use_ref` box in `dependencies` accomplishes nothing.
-   Like every hook, call it **only at the top level** — never in a loop, a conditional, or after an early `#!python return`. ReactPy does not check; a hook that runs on some renders but not others produces a scrambled component and a cryptic `IndexError`.

---

## Usage

### Skipping an expensive calculation

Give `use_memo` the function that does the work, and list what it reads. The leaderboard sorts seven rows here, which is nothing — but it is the same shape you would use for a sort over ten thousand, and the counter on screen shows exactly how often the sort runs.

Press **Change highlight**: the component re-renders, the sort does not run, and `#!python sorted 1 time(s)` stays put. Press **Everyone scores +1**: `#!python players` changes, so the sort runs again.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_memo/expensive_calc/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

The counter (`#!python sorts`) and both buttons exist only to make the caching observable. In real code you would keep the `use_memo` call and drop the rest.

### How expensive is "expensive"?

Enough to measure. Sorting a small list, building a dict from a handful of items, or formatting a string is not worth it — the hook has a cost of its own, and a dependency list you must keep correct is a cost too.

Reach for it when you recognize one of these:

-   A sort, filter, or search over a large collection.
-   Parsing: JSON, CSV, a template, a source file.
-   Building a structure that then gets walked repeatedly.
-   Anything you have already timed and found annoying.

If you have not measured it, prefer the plain calculation. Adding `use_memo` later is a one-line change precisely because the calculation is already in its own function.

### Should you add `use_memo` everywhere?

No. Each one is a dependency list you now have to maintain correctly, and a wrong list is a *silent* bug rather than a loud one. Memoize where you have measured, not everywhere.

### Omitting the dependency list

Leave out `dependencies` and ReactPy infers them from the free variables in the function's closure. This is a ReactPy feature with no React equivalent, and it removes the most common class of mistake, because a value the function reads is by definition a free variable.

The word count below reads `#!python text` but not `#!python upper`, so toggling the case re-renders the component without re-running the count. Watch `#!python counted 1 time(s)`.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_memo/deps_inferred/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Two catches. Inference only sees *closure* variables, so a module-level name, or anything reached through an object, is invisible to it. And inference is a convenience for a function defined inside the component — pass the list explicitly when the function comes from elsewhere.

### Recomputing on every render

`#!python dependencies=None` opts out of caching entirely: the function runs on every render. That is what you want when the calculation reads something no dependency list can express, such as a module-level mutable.

The label below reads `#!python config`, which lives at module scope. Inferred dependencies would be empty, so the label would be computed once and never notice a changed `#!python config`. With `#!python dependencies=None`, `#!python label()` runs each render.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_memo/dependencies_none/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

---

## Troubleshooting

### My memo value never updates

In order of likelihood:

-   **You mutated a dependency instead of replacing it.** Same object in, equal to itself, cached value kept. Build a new object.
-   **You listed a ref as a dependency.** Mutating `#!python some_ref.current` never invalidates anything. Use state, or list the value itself.
-   **The dependency compares equal to its replacement.** Two `#!python [1, 2, 3]` lists are equal, so rebuilding one each render changes nothing.
-   **You left the value out of the list.** See the next item.

### I removed a dependency and nothing complained

Because nothing checks. The example below omits `#!python tax_rate` from the list, and it *seems* to work: press **Add 10% tax** twice and the rate climbs while the total stays frozen at whatever a 0% rate produced. Then press **Add an item** — a real dependency — and the total jumps to `#!python 12.00`, silently incorporating both tax increases you could see never happened.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_memo/missing_dependency/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

This is the failure mode to watch for: a stale value that eventually arrives, so it reads as lag rather than as a bug. List everything the function reads, or omit `dependencies` and let ReactPy infer them.

### My calculation runs on every render anyway

-   You passed `#!python dependencies=None`.
-   A dependency really is new each render — commonly an object constructed in the component body above the `use_memo` call.
-   A dependency is an object whose `#!python ==` is identity-based and which you rebuild each time.

### I wanted to stop a child from re-rendering

`use_memo` cannot do this in ReactPy, and caching the child element does not help either — a cached element is still re-rendered. ReactPy re-renders children unconditionally. If a child is genuinely expensive, the levers are to make its own calculations cheap (memoize *inside* it) or to avoid rendering it at all behind a conditional.
