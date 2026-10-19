## Overview

<p class="intro" markdown>

`use_context` is a ReactPy hook that reads a value provided by a component higher in the tree, without every component in between having to pass it along.

</p>

```python linenums="0"
value = use_context(SomeContext)
```

Context is for values a whole subtree needs and the middle of the tree does not: a theme, the current user, the active locale, a store. If a component would only forward a prop to its children, context removes both the prop and the component's reason to exist.

---

## Reference

### `use_context(context)` { #use-context }

Call it at the top level of a component, passing the context object you created with `create_context`.

```python linenums="0"
from reactpy import use_context
```

#### Parameters

-   **`context`**: The object returned by `create_context`. It is matched by identity, so the same object must be used on both the provider and the reader — import it from one place.

#### Returns

The `#!python value` of the nearest `#!python context` provider above the component. With no provider anywhere above, it returns the default given to `create_context`.

#### Caveats

-   **Reading context is not a subscription that spares renders.** When a provider re-renders with a new value, its children re-render — which they would have anyway, since ReactPy re-renders children unconditionally. Context hands you the new value; it does not narrow the work. See [What context does not do](#what-context-does-not-do).
-   **It returns the default, not `None`, when nothing provides it.** `create_context("light")` yields `#!python "light"` to an unprovided reader, so a component renders on its own without a wrapper. Pick a default that makes sense standalone, or `#!python None` plus an explicit fallback branch.
-   **Call it during the render, not from an effect body.** An effect runs later, in its own task, where no hook is active; calling `use_context` there raises `#!python RuntimeError: No life cycle hook is active. Are you rendering in a layout?` Read it in the component and let the closure carry the value in — see [Reading context inside an effect](#reading-context-inside-an-effect).
-   **The context object must be hashable and must be the same object.** Passing something else raises: `#!python TypeError: <x> is not a Context` for a class or string, `#!python TypeError: unhashable type: 'dict'` if you hand it a dict or list. Two `create_context` calls over the same default are two unrelated contexts.
-   **A `#!python None` default narrows the type.** `create_context(None)` infers a value type of `#!python None`, so a type checker rejects `#!python value=[...]`. Annotate the name to widen it: `#!python Cart: Context[list[str] | None] = create_context(None)`.
-   Like every hook, call it **only at the top level**. Unusually, context *is* safe to call conditionally — it reserves no hook slot, so unlike `#!python use_state` it cannot shift other hooks' state.

---

## Creating and providing a context

A context is created once, at module level, with `create_context`:

```python linenums="0"
from reactpy import create_context

Theme = create_context("light")
```

What comes back is an ordinary function, and calling it *is* the provider: pass the children positionally and the value as a keyword.

```python linenums="0"
Theme(child_a, child_b, value="dark")
```

There is no `#!python Theme.Provider` — calling the context is the only form. The provider renders a nameless fragment around its children, so it adds nothing to the output.

The `#!python value=` keyword is optional; omit it and the default from `create_context` is used. A `#!python key=` keyword is also accepted, with the same meaning as on any other element.

---

## Usage

### Passing data deeply

`#!python swatch` needs the theme. `#!python toolbar` does not — it renders `#!python swatch` and never mentions it. Without context, `#!python toolbar` would take a `#!python theme` argument purely to forward it, and every component added in between would inherit that obligation.

Press **Switch to dark**: the provider gets a new value, and the component far below reads it.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_context/theme_provider/app.py" start="# start" %}
    ```

=== ":material-play: Run"

### Choosing a default

The default is what a component sees when no provider is above it, which is exactly the situation in a unit test or a standalone render. Make it something the component can handle.

`#!python cart_badge` below copes with either — rendered bare it says the cart is unavailable, wrapped in the provider it counts the items.

=== "app.py"

    ```python
    {% include "../../examples/reference_use_context/default_value/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Note the type annotation on `#!python Cart`. Because the default is `#!python None`, without the annotation a type checker infers the value type as `#!python None` and rejects `#!python Cart(shop(), value=["widget", ...])`.

### Nesting providers

The provider nearest above the reader wins, and sibling subtrees are independent. "Above" means *in the tree that renders it*, so the reader has to live inside a child component — reading in the enclosing body runs before the provider is rendered:

```python linenums="0"
Theme = create_context("light")


@component
def swatch():
    # A child component: it renders after the provider above it has registered.
    return html.p(use_context(Theme))


@component
def page():
    return Theme(
        swatch(),                                     # "outer"
        Theme(swatch(), value="inner"),               # "inner"
        value="outer",
    )
```

Verified: the first reads `#!python "outer"`, the second `#!python "inner"`; two sibling providers with different values each see their own.

!!! warning "Do not read the context in the same body that renders the provider"

    ```python linenums="0"
    @component
    def page():
        return Theme(
            html.p(use_context(Theme)),   # "light", not "outer"
            value="outer",
        )
    ```

    Arguments are evaluated while `#!python page()` runs, and the provider registers its value only when the layout later renders it. Both reads here return the `#!python create_context("light")` default. Move the read into a child component. The same rule explains why reading inside an effect fails ([below](#reading-context-inside-an-effect)).

Removing a provider returns its descendants to the default. What actually produces that is the remount: a provider is a component node in the tree, so dropping it moves its children to a different position and ReactPy rebuilds them — verified, a counter below a removed provider went back to `#!python 0` along with its value. Do not lean on that. `core/_life_cycle_hook.py`, `set_current` only ever *merges* the parent's providers into a hook (`_context_providers.update(...)`) and nothing prunes the dict, so a component that survives a render keeps whatever it inherited. If you need a guaranteed reset, change the child's `#!python "key"`.

### Reading context inside an effect

Effects run in their own task, outside any component render, so no hook is active there and `use_context` will not work. Read it in the component and use the local:

=== "app.py"

    ```python
    {% include "../../examples/reference_use_context/reading_in_an_effect/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Putting `use_context(Config)` inside `#!python on_mount` instead raises `RuntimeError: No life cycle hook is active. Are you rendering in a layout?` — and since an effect error is logged only on the server, it is easy to miss.

---

## What context does not do

Context solves **plumbing**: it moves a value past components that do not care about it. It is not a performance feature.

-   **It does not stop children from re-rendering.** ReactPy has no render bailout, so when the provider re-renders, everything below it re-renders too. A component reading a context whose value did not change still re-renders — verified: toggling a theme re-ran the bodies of both a context reader and an unrelated sibling.
-   **It does not make a value reactive by itself.** The value changes because the component that renders the provider re-rendered with a new one. If nothing re-renders the provider, readers keep seeing the old value.
-   **It does not replace state.** Context carries values *down*. To let a component change a shared value, put the state in a common ancestor and pass the setter down alongside it — or move to a reducer, see [`use_reducer`](./use-reducer.md).

For a value that only one component's subtree uses, a prop is simpler and easier to trace. Reach for context when the value genuinely crosses several levels that have no use for it.

---

## Troubleshooting

### Readers always get the default

Usually one of:

-   The provider is not above the reader in the *tree*. `#!python Theme(child, value=...)` must be an ancestor — calling it and discarding the result provides nothing.
-   The provider and the reader hold **different context objects**. Two `create_context` calls are different contexts even with the same default, so create it once and import it.
-   The provider's `#!python value=` never changes, so readers keep seeing the value from the render that set it.

### `RuntimeError: No life cycle hook is active. Are you rendering in a layout?`

You called `use_context` outside a render — from an effect body, from a plain function called before the component runs, or directly in a test. Move the call into the component body.

### `TypeError: ... is not a Context`

You passed something other than the result of `create_context` — often the *provider* instead of the context (`use_context(Theme(child, value="x"))`), or the class of a value rather than a context.

### My type checker rejects the provider's `value`

The default narrowed the type. Annotate the module-level name with `#!python Context[<your type> | None]`, as in the default-value example above.
