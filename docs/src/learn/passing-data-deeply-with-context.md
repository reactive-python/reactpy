## Overview

<p class="intro" markdown>

Passing data through components that only hand it on is tedious and easy to get wrong. Context lets a component read a value that an ancestor provides, skipping the middle of the tree. In ReactPy it is purely a plumbing tool — it carries values down and nothing else — and there are three behaviours worth knowing before you rely on it.

</p>

!!! summary "You will learn"

    -   How to recognise prop drilling worth replacing
    -   The three steps: create, use, provide
    -   Why a component cannot read the context it provides
    -   Why *removing* a provider throws away the subtree's state

## The problem with passing props

Here is a list of places, and each row is coloured by the current theme. Only the deepest component cares about the theme, but the prop has to travel through everyone:

=== "app.py"

    ```python
    {% include "../../examples/passing_data_deeply_with_context/prop_drilling/app.py" start="# start" %}
    ```

=== ":material-play: Run"

`#!python app` holds the theme. `#!python section` receives it, `#!python list_of_places` receives it, `#!python place_list` receives it, and only `#!python place_label` reads it. Three components mention a value they never use, and adding a row to `#!python list_of_places` means threading `#!python theme` through one more signature.

That is the shape worth replacing: **a prop that a component only forwards**. If a component would use a prop itself, pass it as a prop — that is easier to trace.

## Context: an alternative to passing props

Three steps, and the order matters: create the context, read it where you need it, and provide it somewhere above.

### Step 1: Create the context

A context is an object you create once, usually at module level:

```python linenums="0"
from reactpy import create_context

ThemeContext = create_context("light")
```

The argument is the **default** — what `#!python use_context` returns when no provider sits above the reader. Pick something that renders sensibly on its own, because a component will occasionally render without a wrapper.

The object is matched by identity, so create it once and import it everywhere. Two `#!python create_context` calls are two unrelated contexts even with identical defaults.

### Step 2: Use the context

In the component that needs the value:

```python linenums="0"
from reactpy import use_context

theme = use_context(ThemeContext)
```

No parameter, no forwarding. The components in between never learn the value exists:

=== "app.py"

    ```python
    {% include "../../examples/passing_data_deeply_with_context/context_theme/app.py" start="# start" %}
    ```

=== ":material-play: Run"

`#!python place_label` calls `#!python use_context`, and `#!python place_list`, `#!python list_of_places`, and `#!python section` no longer mention `#!python theme` at all. Verified: this version and the prop-drilling version above render the same five rows with the same colours, and both respond to the toggle identically.

Without any provider at all, every reader gets the default:

=== "app.py"

    ```python
    {% include "../../examples/passing_data_deeply_with_context/context_default/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Both labels read `#!python theme=light` — the value from `#!python create_context`, not `#!python None`. This is what makes it safe to reuse a component in a page that never sets the theme up.

### Step 3: Provide the context

Wrap the subtree you want to see the value:

```python linenums="0"
ThemeContext(children, value=theme)
```

The context object *is* a component. Calling it produces a provider element whose `#!python children` render in place, adding no wrapper of its own — verified: the element with `#!python id="places"` contains the whole tree with nothing extra between it and the list.

A provider only covers **its own children**. A sibling rendered after it sees the default, and a provider nested inside another one shadows it for its own subtree:

=== "app.py"

    ```python
    {% include "../../examples/passing_data_deeply_with_context/context_nesting/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified readouts: `#!python outside` and `#!python after` see `#!python light` (the default), `#!python deep` — three levels below `#!python outer` — sees `#!python outer`, `#!python inner` sees `#!python middle-provider`, and `#!python deepest`, inside the nested provider, sees `#!python innermost`. The nearest provider wins; the search walks up and stops.

!!! warning "Pitfall"

    `#!python use_context` belongs in the component that uses the value, not in the parent that places it. Write `#!python ThemeContext(deep_label(), value="x")`, not `#!python ThemeContext(html.p(f"{use_context(ThemeContext)}"), value="x")`. The second one calls the hook while the **parent** renders, so it reads the parent's context — the provider has not been entered yet. This is easy to hit by accident: a label formatted inline above a provider reported the default `#!python light` while its own provider supplied `#!python middle-provider`.

## Using and providing context from the same component

A component cannot read the context it provides. The provider applies to its children, and a component is not its own child:

=== "app.py"

    ```python
    {% include "../../examples/passing_data_deeply_with_context/self_provider/app.py" start="# start" %}
    ```

=== ":material-play: Run"

The child reads `#!python child sees: dark` while the component that rendered the provider reads `#!python section itself sees: light` — the default, before and after the toggle. If the component needs the value too, read the state it comes from: `#!python theme` is right there in `#!python section`, so use it directly.

## Context passes through intermediate components

The value reaches any depth as long as the provider is a genuine ancestor. `#!python wrapper` and `#!python middle` in the nesting example above receive no props at all, and `#!python deep` still resolves the theme.

This is also what makes context the right tool for a component you do not control — a third-party list renderer, a slot you pass children into. Anything rendered inside the provider's subtree can read it, however deep.

!!! abstract "Note"

    A component's state, however, belongs to its *position* in the tree. Two sibling subtrees that both mount `#!python draft()` get two independent pieces of state (verified: `#!python x#1` and `#!python x#2` under two providers of the same context). Context shares what flows down from the provider; it does not merge instances below it.

## Removing a provider resets the subtree below it

A provider is a component, so *adding* or *removing* one changes the shape of the tree — and ReactPy identifies a component by where it sits. The subtree below is unmounted and rebuilt, with its state. Press **change value** and the draft you typed survives; press **toggle provider** and it is gone:

=== "app.py"

    ```python
    {% include "../../examples/passing_data_deeply_with_context/provider_remount/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Verified sequence. Type `#!python hello`: the readout shows `#!python draft='hello'`. Press **change value**: `#!python draft='hello' ... theme=light`, and the component's own render counter keeps counting, which is how you can tell it is the same instance — a changed `#!python value` does not disturb the tree. Press **toggle provider**: the counter resets to `#!python renders=1` and `#!python draft=''`. The leaf was unmounted and a fresh one mounted, so its state is not stale, it is *new*.

Flipping the conditional back does not restore it either — that is a third instance.

The rule: **keep the provider in the tree and vary only its `#!python value`.** Toggling a theme off should be `#!python Theme(child, value="light")`, not `#!python Theme(child, value=...) if dark else child`.

Do not reach for `#!python key` to fix this — it does not. Verified across four variants: a conditional provider loses the state, and adding a stable `#!python key` to the child beneath it loses the state too. What keeps the state is having the provider element present in both branches, so the tree shape never changes.

The version that works moves the condition *inside* `#!python value`, expressing "not provided" as the default rather than as an absent wrapper:

=== "app.py"

    ```python
    {% include "../../examples/passing_data_deeply_with_context/provider_always/app.py" start="# start" %}
    ```

=== ":material-play: Run"

Type `#!python hello`, press **toggle provider**: `#!python draft='hello' ... theme=light`, and the render counter keeps counting. Same buttons, same user-visible behaviour as the broken version, state intact.

This is a special case of a rule that applies to all components, not just providers — see [Preserving and Resetting State](./preserving-and-resetting-state.md). Context makes it easier to hit by accident, because "wrap this in a provider" is a natural thing to put behind an `#!python if`.

## Before you use context

-   **Does a component only forward the prop?** If it uses the value, pass a prop. If it is one level deep, pass a prop. Context pays off when the value crosses several levels that do not care about it.
-   **Is the value genuinely shared?** A value used by one subtree is simpler as a prop, and easier to trace when it is wrong.
-   **Are you hoping it saves renders?** It does not. ReactPy has no render bailout, so when the provider re-renders, everything below it re-renders too, whether or not the value changed. Context is a plumbing feature, never a performance one — see [What context does not do](../reference/use-context.md#what-context-does-not-do).
-   **Do you want to change a value from below?** Then context is the wrong shape. Put the state in a common ancestor and pass the setter (or a `#!python dispatch`) down with it — see [Scaling Up with Reducer and Context](./scaling-up-with-reducer-and-context.md).

## Recap

-   Context replaces props that components only forward. It does not replace props a component actually uses.
-   Three steps: `#!python create_context(default)` once at module level, `#!python use_context(Context)` in the component that needs it, `#!python Context(children, value=...)` above that subtree.
-   The default from `#!python create_context` is what an unprovided reader gets — not `#!python None`. Verified.
-   The nearest provider wins; a nested provider shadows the outer one, and siblings outside a provider see the default. Verified across four readers.
-   Call `#!python use_context` in the component that uses the value. Formatting it inside the parent's arguments reads the parent's context.
-   A component cannot read the context it provides — verified reading the default while its own child read the provided value. Read the underlying state instead.
-   Keep the provider element in the tree and vary only its `#!python value`. Conditionally wrapping in a provider unmounts the subtree and discards its state; a `#!python key` does not prevent it (verified).
-   Context is plumbing only: no render bailout, no reactivity, no shared state. See [Use Context](../reference/use-context.md) for the parameter-level detail and error messages.

## Related

-   [Use Context](../reference/use-context.md) — parameters, caveats, error messages, and what context does not do
-   [Scaling Up with Reducer and Context](./scaling-up-with-reducer-and-context.md) — sharing a reducer and its dispatch, the usual next step
-   [Choosing the State Structure](./choosing-the-state-structure.md) — what belongs in state at all, and where
-   [Queueing a Series of State Updates](./queueing-a-series-of-state-updates.md) — the updater form, when two handlers race
-   [Reusing Logic with Custom Hooks](./reusing-logic-with-custom-hooks.md) — the other way to share behaviour, for logic rather than values
