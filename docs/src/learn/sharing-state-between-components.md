## Overview

<p class="intro" markdown>

Sometimes, you want the state of two components to always change together. To do it, remove state from both of them, move it to their closest common parent, and then pass it down to them via props. This is known as _lifting state up,_ and it's one of the most common things you will do writing ReactPy code.

</p>

!!! summary "You will learn"

    -   How to share state between two components
    -   How to coordinate components by lifting state to their common parent
    -   What controlled and uncontrolled components are

## Lifting state up by example

In this example, a parent `#!python accordion()` component renders two separate `#!python panel()`s:

-   `#!python accordion()`
    -   `#!python panel()`
    -   `#!python panel()`

Each `#!python panel()` component has a boolean `#!python is_active` state that determines whether its content is visible.

Press the Show button for both panels:

=== "app.py"

    ```python
    {% include "../../examples/sharing_state_between_components/independent/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/sharing_state_between_components/independent/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Notice how pressing one panel's button does not affect the other panel — they are independent.

**But now let's say you want to change it so that only one panel is expanded at any given time.** With that design, expanding the second panel should collapse the first one. How would you do that?

To coordinate these two panels, you need to "lift their state up" to a parent component in three steps:

1. **Remove** state from the child components.
2. **Pass** hardcoded data from the common parent.
3. **Add** state to the common parent and pass it down together with the event handlers.

This will allow the `#!python accordion()` component to coordinate both `#!python panel()`s and only expand one at a time.

### Step 1: Remove state from the child components

You will give control of the `#!python panel()`'s `#!python is_active` to its parent component. This means that the parent component will pass `#!python is_active` to `#!python panel()` as a prop instead. Start by **removing this line** from the `#!python panel()` component:

```python linenums="0"
is_active, set_is_active = use_state(False)
```

And instead, add `#!python is_active` to the `#!python panel()`'s list of props:

```python linenums="0"
@component
def panel(title, is_active, *children):
```

Now the `#!python panel()`'s parent component can _control_ `#!python is_active` by [passing it down as a prop.](./passing-props-to-a-component.md) Conversely, the `#!python panel()` component now has _no control_ over the value of `#!python is_active` — it's now up to the parent component!

### Step 2: Pass hardcoded data from the common parent

To lift state up, you must locate the closest common parent component of _both_ of the child components that you want to coordinate:

-   `#!python accordion()` _(closest common parent)_
    -   `#!python panel()`
    -   `#!python panel()`

In this example, it's the `#!python accordion()` component. Since it's above both panels and can control their props, it will become the "source of truth" for which panel is currently active. Make the `#!python accordion()` component pass a hardcoded value of `#!python is_active` (for example, `#!python True`) to both panels:

=== "app.py"

    ```python
    {% include "../../examples/sharing_state_between_components/hardcoded/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/sharing_state_between_components/hardcoded/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

Try editing the hardcoded `#!python is_active` values in the `#!python accordion()` component and see the result on the screen.

### Step 3: Add state to the common parent

Lifting state up often changes the nature of what you're storing as state.

In this case, only one panel should be active at a time. This means that the `#!python accordion()` common parent component needs to keep track of _which_ panel is the active one. Instead of a `#!python bool` value, it could use a number as the index of the active `#!python panel()` for the state variable:

```python linenums="0"
active_index, set_active_index = use_state(0)
```

When the `#!python active_index` is `#!python 0`, the first panel is active, and when it's `#!python 1`, it's the second one.

Clicking the "Show" button in either `#!python panel()` needs to change the active index in `#!python accordion()`. A `#!python panel()` can't set the `#!python active_index` state directly because it's defined inside the `#!python accordion()`. The `#!python accordion()` component needs to _explicitly allow_ the `#!python panel()` component to change its state by [passing an event handler down as a prop](./responding-to-events.md#passing-event-handlers-as-props):

```python linenums="0"
panel(
    "About",
    active_index == 0,
    lambda event: set_active_index(0),
    ...
)
```

The `#!python html.button()` inside the `#!python panel()` will now use the `#!python on_show` prop as its click event handler:

=== "app.py"

    ```python
    {% include "../../examples/sharing_state_between_components/lifted/app.py" start="# start" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/sharing_state_between_components/lifted/styles.css" %}
    ```

=== ":material-play: Run"

    ```python
    # TODO
    ```

This completes lifting state up! Moving state into the common parent component allowed you to coordinate the two panels. Using the active index instead of two "is shown" flags ensured that only one panel is active at a given time. And passing down the event handler to the child allowed the child to change the parent's state.

### Controlled and uncontrolled components

It is common to call a component with some local state "uncontrolled". For example, the original `#!python panel()` component with an `#!python is_active` state variable is uncontrolled because its parent cannot influence whether the panel is active or not.

In contrast, you might say a component is "controlled" when the important information in it is driven by props rather than its own local state. This lets the parent component fully specify its behavior. The final `#!python panel()` component with the `#!python is_active` prop is controlled by the `#!python accordion()` component.

Uncontrolled components are easier to use within their parents because they require less configuration. But they're less flexible when you want to coordinate them together. Controlled components are maximally flexible, but they require the parent components to fully configure them with props.

In practice, "controlled" and "uncontrolled" aren't strict technical terms — each component usually has some mix of both local state and props. However, this is a useful way to talk about how components are designed and what capabilities they offer.

When writing a component, consider which information in it should be controlled (via props), and which information should be uncontrolled (via state). But you can always change your mind and refactor later.

## A single source of truth for each state

In a ReactPy application, many components will have their own state. Some state may "live" close to the leaf components (components at the bottom of the tree) like inputs. Other state may "live" closer to the top of the app. For example, a router implemented in ReactPy would keep the current route in the state of a component near the root, and pass it down by props.

**For each unique piece of state, you will choose the component that "owns" it.** This principle is also known as having a ["single source of truth".](https://en.wikipedia.org/wiki/Single_source_of_truth) It doesn't mean that all state lives in one place — but that for _each_ piece of state, there is a _specific_ component that holds that piece of information. Instead of duplicating shared state between components, _lift it up_ to their common shared parent, and _pass it down_ to the children that need it.

Your app will change as you work on it. It is common that you will move state down or back up while you're still figuring out where each piece of the state "lives". This is all part of the process!

To see what this feels like in practice with a few more components, read [Thinking in React.](./thinking-in-react.md)

## Summary

-   When you want to coordinate two components, move their state to their common parent.
-   Then pass the information down through props from their common parent.
-   Finally, pass the event handlers down so that the children can change the parent's state.
-   It's useful to consider components as "controlled" (driven by props) or "uncontrolled" (driven by state).
