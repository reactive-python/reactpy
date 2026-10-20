## Overview

<p class="intro" markdown>

Components often need to change what's on the screen as a result of an interaction. Typing into a form should update the input field, clicking "next" on an image carousel should change which image is displayed, clicking "buy" should put a product in the shopping cart. Components need to "remember" things: the current input value, the current image, the shopping cart. In ReactPy, this kind of component-specific memory is called _state_.

</p>

!!! summary "You will learn"

    -   How to add a state variable with `#!python use_state`
    -   What pair of values `#!python use_state` returns
    -   How to add more than one state variable
    -   Why state is called local

## When a regular variable isn't enough

Here's a component that renders a sculpture image. Clicking "Next" should show the next sculpture by changing `#!python index` to `#!python 1`, then `#!python 2`, and so on. However, this **won't work** (you can try it!):

=== "app.py"

    ```python
    {% include "../../examples/state_a_components_memory/regular_variable/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/state_a_components_memory/regular_variable/data.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/state_a_components_memory/regular_variable/styles.css" %}
    ```

=== ":material-play: Run"

The `#!python handle_next` event handler is updating a local variable, `#!python index`. But two things prevent that change from being visible:

1. **Local variables don't persist between renders.** When ReactPy renders this component a second time, it renders it from scratch — it doesn't consider any changes to the local variables.
2. **Changes to local variables won't trigger renders.** ReactPy doesn't realize it needs to render the component again with the new data.

Both were checked against this exact component: clicking "Next" three times leaves the served VDOM byte-identical, and a later render caused by real state shows `#!python index` back at `#!python 0` even though the handler had bumped it to `#!python 3`.

To update a component with new data, two things need to happen:

1. **Retain** the data between renders.
2. **Trigger** ReactPy to render the component with new data (re-rendering).

`#!python use_state` provides those two things:

1. A **state variable** to retain the data between renders.
2. A **state setter function** to update the variable and trigger ReactPy to render the component again.

## Adding a state variable

To add a state variable, import `#!python use_state` from `#!python reactpy` at the top of the file:

```python linenums="0"
from reactpy import component, html, use_state
```

Then replace this line:

```python linenums="0"
index = 0
```

with

```python linenums="0"
index, set_index = use_state(0)
```

`#!python index` is a state variable and `#!python set_index` is the setter function.

!!! note "Python gives you the destructuring for free"

    React's `#!js const [index, setIndex] = useState(0)` needs array destructuring syntax. In Python this is ordinary tuple unpacking, so there is nothing new to learn here — and unlike JavaScript, leaving out a name is a syntax error rather than a silent `#!js undefined`.

This is how they work together in `#!python handle_next`:

```python linenums="0"
async def handle_next(event):
    set_index(index + 1)
```

!!! warning "The handler needs `#!python nonlocal` to read its own variable"

    If you keep the plain-variable version, the assignment inside the nested function is not legal Python without a declaration:

    ```python linenums="0"
    async def handle_next(event):
        nonlocal index
        index = index + 1
    ```

    Without it, Python treats `#!python index` as a *new* local of `#!python handle_next`, and reading it on the right-hand side raises `#!python UnboundLocalError`. This is a Python scoping rule, not a ReactPy one — JavaScript closures just work. With `#!python use_state` you never need it, because you read `#!python index` and call `#!python set_index` instead of assigning.

Now clicking the "Next" button switches the current sculpture:

=== "app.py"

    ```python
    {% include "../../examples/state_a_components_memory/state_variable/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/state_a_components_memory/state_variable/data.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/state_a_components_memory/state_variable/styles.css" %}
    ```

=== ":material-play: Run"

### Meet your first Hook

In ReactPy, `#!python use_state`, as well as any other function starting with `#!python use`, is called a Hook.

_Hooks_ are special functions that are only available while ReactPy is [rendering](./render-and-commit.md#step-1-trigger-a-render) (which we'll get into in more detail on the next page). They let you "hook into" different ReactPy features.

State is just one of those features, but you will meet the other Hooks later.

!!! danger "Call Hooks only at the top level"

    **Hooks — functions starting with `#!python use` — can only be called at the top level of your components or [your own Hooks.](./reusing-logic-with-custom-hooks.md)** You can't call Hooks inside conditions, loops, or other nested functions. Hooks are functions, but it's helpful to think of them as unconditional declarations about your component's needs. You "use" ReactPy features at the top of your component similar to how you "import" modules at the top of your file.

    Nothing enforces the rule, which is what makes it dangerous. Hook state is stored in a list read by *position*, so a Hook under a branch changes how many slots the component asks for:

    ```python linenums="0"
    @component
    def bad(flag):
        a, _ = use_state("A")
        if flag:
            b, _ = use_state("B")
            return html.p(b)
        return html.p(a)
    ```

    When the branch stops taking that path, the component asks for fewer Hooks than it did on its first render — no error, the values simply shift into each other's slots. Asking for more raises `#!python IndexError` and blanks the region. Call every Hook at the top level and branch on what they return.

### Anatomy of `#!python use_state`

When you call `#!python use_state`, you are telling ReactPy that you want this component to remember something:

```python linenums="0"
index, set_index = use_state(0)
```

In this case, you want ReactPy to remember `#!python index`.

!!! note ""

    The convention is to name this pair like `#!python something, set_something`. You could name it anything you like, but conventions make things easier to understand across projects.

The only argument to `#!python use_state` is the **initial value** of your state variable. In this example, the `#!python index`'s initial value is set to `#!python 0` with `#!python use_state(0)`.

Every time your component renders, `#!python use_state` gives you a pair containing two values:

1. The **state variable** (`#!python index`) with the value you stored.
2. The **state setter function** (`#!python set_index`) which can update the state variable and trigger ReactPy to render the component again.

Here's how that happens in action:

```python linenums="0"
index, set_index = use_state(0)
```

1. **Your component renders the first time.** Because you passed `#!python 0` to `#!python use_state` as the initial value for `#!python index`, it returns `#!python (0, set_index)`. ReactPy remembers `#!python 0` is the latest state value.
2. **You update the state.** When a user clicks the button, it calls `#!python set_index(index + 1)`. `#!python index` is `#!python 0`, so it's `#!python set_index(1)`. This tells ReactPy to remember `#!python index` is `#!python 1` now and triggers another render.
3. **Your component's second render.** ReactPy still sees `#!python use_state(0)`, but because ReactPy _remembers_ that you set `#!python index` to `#!python 1`, it returns `#!python (1, set_index)` instead.
4. And so on!

!!! tip "Pass a function for an expensive initial value"

    `#!python use_state` accepts a callable and calls it only when the state is first created: `#!python use_state(lambda: json.loads(big_blob))`. Passing the *result* of an expensive call instead — `#!python use_state(json.loads(big_blob))` — reparses on every render, because Python evaluates the argument before `#!python use_state` ever runs.

## Giving a component multiple state variables

You can have as many state variables of as many types as you like in one component. This component has two state variables, a number `#!python index` and a boolean `#!python show_more` that's toggled when you click "Show details":

=== "app.py"

    ```python
    {% include "../../examples/state_a_components_memory/multiple_state/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/state_a_components_memory/multiple_state/data.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/state_a_components_memory/multiple_state/styles.css" %}
    ```

=== ":material-play: Run"

It is a good idea to have multiple state variables if their state is unrelated, like `#!python index` and `#!python show_more` in this example. But if you find that you often change two state variables together, it might be easier to combine them into one. For example, if you have a form with many fields, it's more convenient to have a single state variable that holds a dict than a state variable per field. Read [Choosing the State Structure](./choosing-the-state-structure.md) for more tips.

## State is isolated and private

State is local to a particular invocation of a component — like a local variable. Render the same component twice and each copy gets its own state.

=== "app.py"

    ```python
    {% include "../../examples/state_a_components_memory/isolated_galleries/app.py" start="# start" %}
    ```

=== "data.py"

    ```python
    {% include "../../examples/state_a_components_memory/isolated_galleries/data.py" %}
    ```

=== "styles.css"

    ```css
    {% include "../../examples/state_a_components_memory/isolated_galleries/styles.css" %}
    ```

=== ":material-play: Run"

Click "Next" in one gallery and the other doesn't budge. Each call to `#!python gallery()` is a separate component instance with its own state.

This is the same mechanism behind [Passing Props to a Component](./passing-props-to-a-component.md): the `#!python person` prop is local to one invocation of `#!python Profile()`, so two `#!python Profile()` calls don't share it. State works the same way.

Because state belongs to the instance and not the function, two galleries can drift apart — which is sometimes what you want, and sometimes not. [Sharing State Between Components](./sharing-state-between-components.md) covers the case where they must move together.

!!! info "How does ReactPy know which state to return?"

    You might have noticed that the `#!python use_state` call does not receive any information about _which_ state variable it refers to. There is no "identifier" passed to `#!python use_state`, so how does it know which state to return? Does it rely on some magic like parsing your functions? The answer is no.

    Instead, to enable their concise syntax, Hooks **rely on a stable call order on every render of the same component.** ReactPy appends each Hook's state to a list on the component's first render, then walks that list by position on every render after (`LifeCycleHook.use_state` in `core/_life_cycle_hook.py`). This works well in practice because if you follow the rule above ("only call Hooks at the top level"), Hooks are always called in the same order — and nothing has to check.

    What happens when the order does change is worth knowing, because one of the two outcomes fails *silently*:

    -   **A Hook appears where there was none before** → `#!python IndexError: list index out of range`, the render aborts, and the error is logged.
    -   **A Hook stops being called** → the Hooks after it shift up one slot and **quietly receive the wrong values**. Nothing is logged, and the component keeps rendering.

    Measured with two `#!python use_state` calls that vanish behind a branch, the surviving Hook got the *first* slot's value while its own was left orphaned. That is far harder to debug than a crash, which is exactly why the top-level rule is enforced rather than merely recommended.

## Recap

-   Components need to "remember" things, and that memory is called _state_.
-   A state variable is declared with `#!python use_state`, which returns the current value and a setter function.
-   Updating a local variable doesn't re-render, and re-renders throw local variables away. State is what survives.
-   Hooks must be called at the top level, in the same order every render — state is read back by position, and nothing checks it for you.
-   State is local to each invocation of a component, so two instances never share it.
