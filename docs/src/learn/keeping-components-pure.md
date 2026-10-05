## Overview

<p class="intro" markdown>

Some Python functions are _pure._ Pure functions only perform a calculation and nothing more. By strictly only writing your components as pure functions, you can avoid an entire class of baffling bugs and unpredictable behavior as your codebase grows. To get these benefits, though, there are a few rules you must follow.

</p>

!!! summary "You will learn"

    -   What purity is and how it helps you avoid bugs
    -   How to keep components pure by keeping changes out of the render phase
    -   Why ReactPy cannot check purity for you

## Purity: Components as formulas

In computer science (and especially the world of functional programming), [a pure function](https://wikipedia.org/wiki/Pure_function) is a function with the following characteristics:

-   **It minds its own business.** It does not change any objects or variables that existed before it was called.
-   **Same inputs, same output.** Given the same inputs, a pure function should always return the same result.

You might already be familiar with one example of pure functions: formulas in math.

Consider this math formula: `#!python y = 2 * x`.

If `#!python x = 2` then `#!python y = 4`. Always.

If `#!python x = 3` then `#!python y = 6`. Always.

If `#!python x = 3`, `#!python y` won't sometimes be `#!python 9` or `#!python -1` or `#!python 2.5` depending on the time of day or the state of the stock market.

If `#!python y = 2 * x` and `#!python x = 3`, `#!python y` will _always_ be `#!python 6`.

If we made this into a Python function, it would look like this:

```python linenums="0"
def double(number):
    return 2 * number
```

In the above example, `#!python double` is a **pure function.** If you pass it `#!python 3`, it will return `#!python 6`. Always.

ReactPy is designed around this concept. **ReactPy assumes that every component you write is a pure function.** This means that ReactPy components you write must always return the same VDOM given the same inputs:

=== "app.py"

    ```python
    {% include "../../examples/keeping_components_pure/recipe/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

When you pass `#!python drinkers=2` to `#!python recipe()`, it will return VDOM containing `#!python 2 cups of water`. Always.

If you pass `#!python drinkers=4`, it will return VDOM containing `#!python 4 cups of water`. Always.

Just like a math formula.

You could think of your components as recipes: if you follow them and don't introduce new ingredients during the cooking process, you will get the same dish every time. That "dish" is the VDOM that the component serves to ReactPy to [render.](./render-and-commit.md)

## Side Effects: (un)intended consequences

ReactPy's rendering process must always be pure. Components should only _return_ their VDOM, and not _change_ any objects or variables that existed before rendering—that would make them impure!

Here is a component that breaks this rule:

=== "app.py"

    ```python
    {% include "../../examples/keeping_components_pure/impure/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

This component is reading and writing a `#!python guest` variable declared outside of it. This means that **calling this component multiple times will produce different VDOM!** And what's more, if _other_ components read `#!python guest`, they will produce different VDOM, too, depending on when they were rendered! That's not predictable.

Render this once and you get the numbering you expect:

```text linenums="0"
Tea cup for guest #1
Tea cup for guest #2
Tea cup for guest #3
```

Render it again — after a hot reload, a reconnect, or simply a second request in the same process — and the counters have silently moved on:

```text linenums="0"
Tea cup for guest #4
Tea cup for guest #5
Tea cup for guest #6
```

Going back to our formula `#!python y = 2 * x`, now even if `#!python x = 2`, we cannot trust that `#!python y = 4`. Our tests could fail, our users would be baffled, planes would fall out of the sky—you can see how this would lead to confusing bugs!

You can fix this component by [passing `#!python guest` as a prop instead](./passing-props-to-a-component.md):

=== "app.py"

    ```python
    {% include "../../examples/keeping_components_pure/fixed/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Now your component is pure, as the VDOM it returns only depends on the `#!python guest` prop.

In general, you should not expect your components to be rendered in any particular order. It doesn't matter if you call `#!python y = 2 * x` before or after `#!python y = 5 * x`: both formulas will resolve independently of each other. In the same way, each component should only "think for itself", and not attempt to coordinate with or depend upon others during rendering. Rendering is like a school exam: each component should calculate VDOM on their own!

!!! warning "ReactPy has no Strict Mode to catch this for you"

    React ships a "Strict Mode" that calls every component function **twice** in development, which is how the example above gets caught: an impure counter jumps to `#2`, `#4`, `#6`. **ReactPy has no equivalent** — there is no `StrictMode` component and no double-invoke. A single render of an impure component looks completely correct, and the bug only appears later as drifting output or as a failure under a test that renders twice.

    Two practical consequences:

    - Add a test that renders the component twice and asserts the two results are equal. That is the closest ReactPy gets to Strict Mode, and it is entirely in your hands.
    - Because there is no double-invoke to hide behind, impurity in ReactPy tends to surface as *state that changes between reconnects* rather than as an obvious warning. Treat any component that touches module-level state as suspect.

### Local mutation: Your component's little secret

In the above example, the problem was that the component changed a _preexisting_ variable while rendering. This is often called a **"mutation"** to make it sound a bit scarier. Pure functions don't mutate variables outside of the function's scope or objects that were created before the call—that makes them impure!

However, **it's completely fine to change variables and objects that you've _just_ created while rendering.** In this example, you create a `#!python []` list, assign it to a `#!python cups` variable, and then append a dozen cups into it:

=== "app.py"

    ```python
    {% include "../../examples/keeping_components_pure/local_mutation/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

If the `#!python cups` variable or the `#!python []` list were created outside the `#!python tea_gathering()` function, this would be a huge problem! You would be changing a _preexisting_ object by appending items to that list.

However, it's fine because you've created them _during the same render_, inside `#!python tea_gathering()`. No code outside of `#!python tea_gathering()` will ever know that this happened. This is called **"local mutation"**—it's like your component's little secret.

## Where you _can_ cause side effects

While functional programming relies heavily on purity, at some point, somewhere, _something_ has to change. That's kind of the point of programming! These changes—updating the screen, starting an animation, changing the data—are called **side effects.** They're things that happen _"on the side"_, not during rendering.

In ReactPy, **side effects usually belong inside [event handlers.](./responding-to-events.md)** Event handlers are functions that ReactPy runs when you perform some action—for example, when you click a button. Even though event handlers are defined _inside_ your component, they don't run _during_ rendering! **So event handlers don't need to be pure.**

=== "app.py"

    ```python
    {% include "../../examples/keeping_components_pure/side_effects/app.py" start="# start" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

If you've exhausted all other options and can't find the right event handler for your side effect, you can still attach it to your returned VDOM with a `#!python use_effect` or `#!python use_async_effect` call in your component. This tells ReactPy to execute it later, after rendering, when side effects are allowed. **However, this approach should be your last resort.**

When possible, try to express your logic with rendering alone. You'll be surprised how far this can take you!

!!! info "Why does ReactPy care about purity?"

    Writing pure functions takes some habit and discipline. But it also unlocks real opportunities:

    -   **Your components can run on the server.** Since they return the same result for the same inputs, one component can serve many user requests. ReactPy renders components to HTML with `#!python reactpy_to_string`, which is only safe because rendering is pure — a component that mutated module state would leak one request's output into another's.
    -   **Rendering can be restarted.** ReactPy may need to discard an in-progress render, and purity makes it safe to stop calculating at any time.
    -   **Reasoning and testing become mechanical.** A pure component is an ordinary Python function: call it inside a `reactpy.core.layout.Layout`, render it twice, and compare the results — no browser required.

    Note that one React benefit is _not_ available to you yet: React skips re-rendering components whose inputs have not changed, which is safe precisely because pure functions are safe to cache. ReactPy has `#!python use_memo` for values, but **no `#!python memo` for components**, so a child re-runs whenever its parent renders. Purity is still required; it simply isn't being used for caching today.

## Recap

-   A component must be pure, meaning:

    -   **It minds its own business.** It should not change any objects or variables that existed before rendering.
    -   **Same inputs, same output.** Given the same inputs, a component should always return the same VDOM.

-   Rendering can happen at any time, so components should not depend on each others' rendering sequence.
-   You should not mutate any of the inputs that your components use for rendering. That includes props, state, and context. To update the screen, ["set" state](./state-a-components-memory.md) instead of mutating preexisting objects.
-   Strive to express your component's logic in the VDOM you return. When you need to "change things", you'll usually want to do it in an event handler. As a last resort, you can `#!python use_effect`.
-   ReactPy will not double-render your components to find impurity for you; write the render-twice test yourself.
-   Writing pure functions takes a bit of practice, but it unlocks the power of the ReactPy paradigm.
